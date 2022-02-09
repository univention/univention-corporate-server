#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: password reset service
#
# Copyright 2015-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import traceback
import datetime
import random
import string
import atexit
import os.path
import smtplib
from functools import wraps
from subprocess import Popen, PIPE, STDOUT
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate
import email.charset

from ldap.filter import filter_format
import pylibmc

from univention.lib.i18n import Translation
from univention.lib.umc import Client, HTTPError, ConnectionError, Unauthorized
import univention.admin.objects
import univention.admin.syntax
import univention.admin.uexceptions as udm_errors
from univention.admin.uldap import getMachineConnection
from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.modules import UMC_Error
from univention.management.console.ldap import get_user_connection, get_machine_connection, get_admin_connection, machine_connection

from .tokendb import TokenDB, MultipleTokensInDB
from .sending import get_plugins as get_sending_plugins

_ = Translation('univention-self-service-passwordreset-umc').translate

MEMCACHED_SOCKET = "/var/lib/univention-self-service-passwordreset-umc/memcached.socket"
MEMCACHED_MAX_KEY = 250

SELFSERVICE_MASTER = ucr.get("self-service/backend-server", ucr.get("ldap/master"))
IS_SELFSERVICE_MASTER = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname')) == SELFSERVICE_MASTER
DISALLOW_AUTHENTICATION = not ucr.is_true('umc/self-service/allow-authenticated-use')

DEREGISTRATION_TIMESTAMP_FORMATTING = '%Y%m%d%H%M%SZ'

if IS_SELFSERVICE_MASTER:
	try:
		from univention.management.console.modules.udm.syntax import widget
		from univention.management.console.modules.udm.udm_ldap import UDM_Error, UDM_Module
		from univention.udm import UDM, NoObject
		from univention.admin.rest.client import UDMRest
	except ImportError as exc:
		MODULE.error('Could not load udm module: %s' % (exc,))
		widget = None


def forward_to_master(func):
	@wraps(func)
	def _decorator(self, request, *args, **kwargs):
		if not IS_SELFSERVICE_MASTER:
			try:
				language = str(self.locale).split('.')[0].replace('_', '-')
				client = Client(SELFSERVICE_MASTER, language=language)
				client.authenticate_with_machine_account()
				response = client.umc_command(request.arguments[0], request.options)
			except (Unauthorized, ConnectionError) as exc:
				raise UMC_Error(_('The connection to the server could not be established. Please try again later. Error message was: %s') % (exc,), status=503)
			except HTTPError as exc:
				response = exc.response
			self.finished(request.id, response.result, message=response.message, status=response.status)
			return
		return func(self, request, *args, **kwargs)
	return _decorator


def forward_to_master_if_authentication_disabled(func):
	if DISALLOW_AUTHENTICATION:
		return forward_to_master(func)
	return func


def prevent_denial_of_service(func):
	def _pretty_time(sec):
		if sec <= 60:
			return _("one minute")
		m, s = divmod(sec, 60)
		if m < 60:
			return _("{} minutes").format(m + 1)
		elif m == 60:
			return _("one hour")  # and one minute, but nvm
		h, m = divmod(m, 60)
		return _("{} hours").format(h + 1)

	def _check_limits(memcache, limits):
		limit_reached = False
		_max_wait = datetime.datetime.utcnow()
		for key, decay, limit in limits:
			# Not really a "decay", as for that we'd have to store the date for
			# each request. Then a moving window could be implemented. But
			# my guess is that we won't need that, so this is simpler.
			# Continue even if a limit was reached, so that all counters are
			# incremented.
			if limit == 0:
				# limit deactivated by UCR
				continue
			try:
				count = memcache.incr(key)
			except pylibmc.NotFound:
				count = 1
				memcache.set_multi(
					{
						key: count,
						"{}:exp".format(key): datetime.datetime.utcnow() + datetime.timedelta(seconds=decay)
					},
					decay
				)
			if count > limit:
				limit_reached = True
				_max_wait = max(_max_wait, memcache.get("{}:exp".format(key)))
		return limit_reached, _max_wait

	@wraps(func)
	def _decorated(self, *args, **kwargs):
		# check total request limits
		total_limit_reached, total_max_wait = _check_limits(self.memcache, self.total_limits)

		# check user request limits
		try:
			if "username" in kwargs:
				username = kwargs["username"]
			else:
				username = args[0].options["username"]
		except (IndexError, AttributeError, KeyError, TypeError):
			# args[0] is not the expected 'request'
			MODULE.error("prevent_denial_of_service() could not find username argument. self: %r args: %r kwargs: %r exception: %s" % (self, args, kwargs, traceback.format_exc()))
			raise
			# TODO: return func(self, *args, **kwargs) here?!

		if len(username) > MEMCACHED_MAX_KEY - 9:  # "_hour:exp"
			raise ServiceForbidden()

		username = self.email2username(username)
		user_limits = [
			("{}_minute".format(username), 60, self.limit_user_minute),
			("{}_hour".format(username), 3600, self.limit_user_hour),
			("{}_day".format(username), 86400, self.limit_user_day)
		]

		user_limit_reached, user_max_wait = _check_limits(self.memcache, user_limits)

		if total_limit_reached or user_limit_reached:
			time_s = _pretty_time((max(total_max_wait, user_max_wait) - datetime.datetime.utcnow()).total_seconds())
			raise ConnectionLimitReached(time_s)

		return func(self, *args, **kwargs)
	return _decorated


class ConnectionLimitReached(UMC_Error):
	status = 503

	def __init__(self, seconds):
		super(ConnectionLimitReached, self).__init__(_("The allowed maximum number of connections to the server has been reached. Please retry in {}.").format(seconds))


class ServiceForbidden(UMC_Error):
	# protection against bruteforcing user names
	status = 403

	def __init__(self):
		super(ServiceForbidden, self).__init__(_("Either username or password is incorrect or you are not allowed to use this service."))


class TokenNotFound(UMC_Error):
	status = 400

	def __init__(self):
		super(TokenNotFound, self).__init__(
			_("The token you supplied is either expired or invalid. Please request a new one."))


class NoMethodsAvailable(UMC_Error):
	status = 403

	def __init__(self):
		super(NoMethodsAvailable, self).__init__(_('No contact information is stored for this user. Resetting the password is not possible.'))


class MissingContactInformation(UMC_Error):

	def __init__(self):
		super(MissingContactInformation, self).__init__(_("No address has been stored, where a password recovery token could be sent to."))


class Instance(Base):

	def init(self):
		if not ucr.is_true("umc/self-service/enabled"):
			raise UMC_Error(_('The password reset service is disabled via configuration registry.'), status=503)

		self._usersmod = None
		self.groupmod = None

		def ucr_try_int(variable, default):
			try:
				return int(ucr.get(variable, default))
			except ValueError:
				MODULE.error('UCR variables %s is not a number, using default: %s' % (variable, default))
				return default

		self.token_validity_period = ucr_try_int("umc/self-service/passwordreset/token_validity_period", 3600)
		limit_total_minute = ucr_try_int("umc/self-service/passwordreset/limit/total/minute", 0)
		limit_total_hour = ucr_try_int("umc/self-service/passwordreset/limit/total/hour", 0)
		limit_total_day = ucr_try_int("umc/self-service/passwordreset/limit/total/day", 0)
		self.limit_user_minute = ucr_try_int("umc/self-service/passwordreset/limit/per_user/minute", 0)
		self.limit_user_hour = ucr_try_int("umc/self-service/passwordreset/limit/per_user/hour", 0)
		self.limit_user_day = ucr_try_int("umc/self-service/passwordreset/limit/per_user/day", 0)

		self.total_limits = [
			("t:c_minute", 60, limit_total_minute),
			("t:c_hour", 3600, limit_total_hour),
			("t:c_day", 86400, limit_total_day)
		]
		if IS_SELFSERVICE_MASTER:
			self.db = TokenDB(MODULE)
			self.conn = self.db.conn
			atexit.register(self.db.close_db)
			if not self.db.table_exists():
				self.db.create_table()
			self.memcache = pylibmc.Client([MEMCACHED_SOCKET], binary=True)

		self.send_plugins = get_sending_plugins(MODULE.process)
		self.password_reset_plugins = {k: v for k, v in self.send_plugins.items() if v.message_application() == 'password_reset'}

	@property
	def usersmod(self):
		if not self._usersmod:
			univention.admin.modules.update()
			self._usersmod = univention.admin.modules.get('users/user')
			if not self._usersmod.initialized:
				lo, po = get_machine_connection()
				univention.admin.modules.init(lo, po, self._usersmod)
		return self._usersmod

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_service_specific_passwords(self, username, password):
		"""
		Get users (possible) service specific passwords.

		:return: list of dicts with users ssp
		"""
		if ucr.is_false('umc/self-service/service-specific-passwords/backend/enabled') or \
			not ucr.is_true('radius/use-service-specific-password'):  # TODO - once we have more than one type, this should change
			msg = _('Service specific passwords were disabled via the Univention Configuration Registry.')
			MODULE.error('get_service_specific_passwords(): {}'.format(msg))
			raise UMC_Error(msg)
		dn, username = self.auth(username, password)
		ret = []
		if ucr.is_true('radius/use-service-specific-password'):
			ldap_connection, ldap_position = getMachineConnection()
			radius_passwords = ldap_connection.get(dn, attr=['univentionRadiusPassword']).get('univentionRadiusPassword', [])
			ret.append({'type': 'radius', 'set': len(radius_passwords)})
		return ret

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1),
		password_type=StringSanitizer(required=True, minimum=1))
	@simple_response
	def set_service_specific_passwords(self, username, password, password_type):
		'''
		Set a new service specific password.

		:return: The password in cleartext
		'''
		if ucr.is_false('umc/self-service/service-specific-passwords/backend/enabled'):
			msg = _('Service specific passwords were disabled via the Univention Configuration Registry.')
			MODULE.error('get_service_specific_passwords(): {}'.format(msg))
			raise UMC_Error(msg)
		dn, username = self.auth(username, password)
		MODULE.error('set_service_specific_passwords(): Setting {} password for {}'.format(password_type, username))
		if password_type == 'radius' and ucr.is_true('radius/use-service-specific-password'):
			udm = UDMRest.http('https://%s.%s/univention/udm/' % (ucr.get('hostname'), ucr.get('domainname')), 'cn=admin', open('/etc/ldap.secret').read())
			user_obj = udm.get('users/user').get(dn)
			service_specific_password = user_obj.generate_service_specific_password('radius')
		else:
			msg = _('Service specific passwords were disabled for "%s".') % password_type
			MODULE.error('get_service_specific_passwords(): {}'.format(msg))
			raise UMC_Error(msg)
		return {'password': service_specific_password}

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_contact(self, username, password):
		"""
		Get users contact data.

		:return: list of dicts with users contact data
		"""
		if ucr.is_false('umc/self-service/protect-account/backend/enabled'):
			msg = _('The account protection was disabled via the Univention Configuration Registry.')
			MODULE.error('get_contact(): {}'.format(msg))
			raise UMC_Error(msg)

		dn, username = self.auth(username, password)
		if self.is_blacklisted(username, 'passwordreset'):  # FIXME: should be 'protect-account'
			raise ServiceForbidden()

		user = self.get_udm_user(username=username)
		if not self.password_reset_plugins:
			raise ServiceForbidden()

		return [{
			"id": p.send_method(),
			"label": p.send_method_label(),
			"value": user[p.udm_property]
		} for p in self.password_reset_plugins.values() if p.udm_property in user]

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1),
		password=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1))
	@simple_response
	def get_user_attributes(self, username=None, password=None):  # MUST be supported until UCS 4.4-7 is out of maintenance
		dn, username = self.authenticate_user(username, password)
		if self.is_blacklisted(username, 'profiledata'):
			raise ServiceForbidden()

		user = self.get_udm_user_by_dn(dn)
		user.set_defaults = True
		user.set_default_values()
		properties = user.info.copy()
		widget_descriptions = [
			dict(wd, value=properties.get(wd['id'])) for wd in self._get_user_attributes_descriptions()
			if user.has_property(wd['id'])
		]
		# TODO make layout configurable via ucr ?
		layout = [wd['id'] for wd in widget_descriptions]

		return {
			'widget_descriptions': widget_descriptions,
			'layout': layout,
		}

	@forward_to_master_if_authentication_disabled
	@sanitize(
		username=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1),
		password=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1))
	@simple_response
	def get_user_attributes_values(self, attributes, username=None, password=None):
		dn, username = self.authenticate_user(username, password)
		if self.is_blacklisted(username, 'profiledata'):
			raise ServiceForbidden()

		user_attributes = [attr.strip() for attr in ucr.get('self-service/udm_attributes', '').split(',')]
		user = self.get_udm_user_by_dn(dn)
		user.set_defaults = True
		user.set_default_values()
		properties = user.info.copy()
		return {
			prop: properties.get(prop) for prop in attributes if user.has_property(prop) and prop in user_attributes
		}

	@forward_to_master
	@simple_response
	def get_user_attributes_descriptions(self):
		return self._get_user_attributes_descriptions()

	def _get_user_attributes_descriptions(self):
		user_attributes = [attr.strip() for attr in ucr.get('self-service/udm_attributes', '').split(',')]

		widget_descriptions = []
		label_overwrites = {
			'jpegPhoto': _('Your picture')
		}
		for propname in user_attributes:
			if propname == 'password':
				continue
			prop = self.usersmod.property_descriptions.get(propname)
			if not prop:
				continue
			widget_description = {
				'id': propname,
				'label': label_overwrites.get(propname, prop.short_description),
				'description': prop.long_description,
				'syntax': prop.syntax.name,
				'size': prop.size or prop.syntax.size,
				'required': bool(prop.required),
				'editable': bool(prop.may_change),
				'readonly': not bool(prop.editable),
				'multivalue': bool(prop.multivalue),
			}
			widget_description.update(widget(prop.syntax, widget_description))
			if 'udm' in widget_description['type']:
				continue
			if 'dynamicValues' in widget_description:
				continue
			widget_descriptions.append(widget_description)
		return widget_descriptions

	@forward_to_master
	@simple_response
	def get_registration_attributes(self):
		ucr.load()
		property_ids = ['PasswordRecoveryEmail', 'password']
		for id_ in [attr.strip() for attr in ucr.get('umc/self-service/account-registration/udm_attributes', '').split(',') if attr.strip()]:
			if id_ not in property_ids:
				property_ids.append(id_)
		lo, po = get_machine_connection()
		users_mod = UDM_Module('users/user', True, lo, po)
		properties = {prop['id']: prop for prop in users_mod.properties(None)}
		not_existing = set(property_ids) - set(properties.keys())
		properties = {k: v for (k, v) in properties.items() if 'dynamicValues' not in v and 'udm' not in v['type']}  # filter out not supported props
		not_supported = set(property_ids) - set(properties.keys()) - not_existing
		if 'PasswordRecoveryEmail' in properties:
			properties['PasswordRecoveryEmail']['label'] = _('Email')
			properties['PasswordRecoveryEmail']['description'] = ''
		self._update_required_attr_of_props_for_registration(properties)
		properties = [properties[id_] for id_ in property_ids if id_ in properties]
		if not_existing:
			MODULE.warn("get_registration_attributes(): the following attributes defined by umc/self-service/account-registration/udm_attributes do not exist on users/user: {}".format(", ".join(not_existing)))
		if not_supported:
			MODULE.warn("get_registration_attributes(): the following attributes defined by umc/self-service/account-registration/udm_attributes are not supported: {}".format(", ".join(not_supported)))
		return {
			'widget_descriptions': properties,
			'layout': [prop['id'] for prop in properties],
		}

	def _update_required_attr_of_props_for_registration(self, properties):
		for k in properties.keys():
			if isinstance(properties[k], dict):
				properties[k]['required'] = False
			else:
				properties[k].required = False
		required_ids = set(['PasswordRecoveryEmail', 'password'] + [attr.strip() for attr in ucr.get('umc/self-service/account-registration/udm_attributes/required', '').split(',') if attr.strip()])
		for id_ in required_ids:
			if id_ in properties:
				if isinstance(properties[id_], dict):
					properties[id_]['required'] = True
				else:
					properties[id_].required = True

	@forward_to_master_if_authentication_disabled
	@sanitize(
		username=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1),
		password=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1))
	@simple_response
	def validate_user_attributes(self, username, password, attributes):
		dn, username = self.authenticate_user(username, password)
		if self.is_blacklisted(username, 'profiledata'):
			raise ServiceForbidden()
		return self._validate_user_attributes(attributes)

	def _validate_user_attributes(self, attributes, map_properties_func=None):
		res = {}
		properties = self.usersmod.property_descriptions
		if map_properties_func:
			properties = properties.copy()
			map_properties_func(properties)
		for propname, value in attributes.items():
			prop = properties.get(propname)
			if not prop:
				continue

			isValid = True
			message = ''
			if prop.multivalue and isinstance(value, (tuple, list)):
				isValid = []
				message = []
				for ival in value:
					_isValid = True
					_message = ''
					try:
						prop.syntax.parse(ival)
					except (udm_errors.valueError, udm_errors.valueInvalidSyntax) as e:
						_isValid = False
						_message = str(e)
					finally:
						isValid.append(_isValid)
						message.append(_message)
			else:
				try:
					prop.syntax.parse(value)
				except (udm_errors.valueError, udm_errors.valueInvalidSyntax) as e:
					isValid = False
					message = str(e)

			if prop.required and not value:
				isValid = False
				message = _('This value is required')
			res[propname] = {
				'isValid': isValid,
				'message': message,
			}
		return res

	@forward_to_master_if_authentication_disabled
	@sanitize(
		username=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1),
		password=StringSanitizer(required=DISALLOW_AUTHENTICATION, minimum=1))
	@simple_response
	def set_user_attributes(self, attributes, username=None, password=None):
		dn, username = self.authenticate_user(username, password)
		username = username or self.username
		if password:
			dn, username = self.auth(username, password)
			lo, po = get_user_connection(binddn=dn, bindpw=password)
		else:
			lo = self.get_user_ldap_connection(write=True)
			po = univention.admin.uldap.position(lo.base)

		if self.is_blacklisted(username, 'profiledata'):
			raise ServiceForbidden()

		user_attributes = [attr.strip() for attr in ucr.get('self-service/udm_attributes', '').split(',')]
		user = self.usersmod.object(None, lo, po, dn)
		user.open()
		for propname, value in attributes.items():
			if propname in user_attributes and user.has_property(propname):
				user[propname] = value
		try:
			user.modify()
		except udm_errors.base as exc:
			MODULE.error('set_user_attributes(): modifying the user failed: %s' % (traceback.format_exc(),))
			raise UMC_Error(_('The attributes could not be saved: %s') % (UDM_Error(exc)))
		return _("Successfully changed your profile data.")

	@forward_to_master
	@simple_response
	def create_self_registered_account(self, attributes):
		MODULE.info('create_self_registered_account(): attributes: {}'.format(attributes))
		ucr.load()
		if ucr.is_false('umc/self-service/account-registration/backend/enabled', True):
			msg = _('The account registration was disabled via the Univention Configuration Registry.')
			MODULE.error('create_self_registered_account(): {}'.format(msg))
			raise UMC_Error(msg)
		# filter out attributes that are not valid to set
		allowed_to_set = set(['PasswordRecoveryEmail', 'password'] + [attr.strip() for attr in ucr.get('umc/self-service/account-registration/udm_attributes', '').split(',') if attr.strip()])
		attributes = {k: v for (k, v) in attributes.items() if k in allowed_to_set}
		# validate attributes
		res = self._validate_user_attributes(attributes, self._update_required_attr_of_props_for_registration)
		# check username taken
		if 'username' in attributes:
			try:
				UDM.machine().version(2).get('users/user').get_by_id(attributes['username'])
			except NoObject:
				pass
			else:
				res['username'] = {
					'isValid': False,
					'message': _('The username is already taken'),
				}
		invalid = {k: v for (k, v) in res.items() if not (all(v['isValid']) if isinstance(v['isValid'], list) else v['isValid'])}
		if len(invalid):
			return {
				'success': False,
				'failType': 'INVALID_ATTRIBUTES',
				'data': invalid,
			}

		# check for missing required attributes from umc/self-service/account-registration/udm_attributes/required
		required_attrs = [attr.strip() for attr in ucr.get('umc/self-service/account-registration/udm_attributes/required', '').split(',') if attr.strip()]
		not_found = [attr for attr in required_attrs if attr not in attributes]
		if not_found:
			msg = _('The account could not be created:\nInformation provided is not sufficient. The following properties are missing:\n%s') % ('\n'.join(not_found),)
			MODULE.error('create_self_registered_account(): {}'.format(msg))
			raise UMC_Error(msg)

		univention.admin.modules.update()
		lo, po = get_admin_connection()

		# get usertemplate
		template_dn = ucr.get('umc/self-service/account-registration/usertemplate', '')
		usertemplate = None
		if template_dn:
			usertemplate_mod = univention.admin.modules.get('settings/usertemplate')
			univention.admin.modules.init(lo, po, usertemplate_mod, None, True)
			try:
				usertemplate = usertemplate_mod.object(None, lo, None, template_dn)
			except udm_errors.noObject:
				msg = _('The user template "{}" set by the "umc/self-service/account-registration/usertemplate" UCR variable does not exist. A user account can not be created. Please contact your system administrator.'.format(template_dn))
				MODULE.error('create_self_registered_account(): {}'.format(msg))
				raise UMC_Error(msg)

		# init user module with template
		usersmod = univention.admin.modules.get('users/user')
		univention.admin.modules.init(lo, po, usersmod, usertemplate, True)

		# get user container
		udm = UDM.machine().version(2)
		user_position = univention.admin.uldap.position(po.getBase())
		container_dn = ucr.get('umc/self-service/account-registration/usercontainer', None)
		if container_dn:
			try:
				container = udm.obj_by_dn(container_dn)
			except NoObject:
				msg = _('The container "{}" set by the "umc/self-service/account-registration/usercontainer" UCR variable does not exist. A user account can not be created. Please contact your system administrator.'.format(container_dn))
				MODULE.error('create_self_registered_account(): {}'.format(msg))
				raise UMC_Error(msg)
			else:
				user_position.setDn(container.dn)
		else:
			for dn in usersmod.object.get_default_containers(lo):
				try:
					container = udm.obj_by_dn(dn)
				except NoObject:
					pass
				else:
					user_position.setDn(container.dn)
					break

		# create user
		attributes['PasswordRecoveryEmailVerified'] = 'FALSE'
		attributes['RegisteredThroughSelfService'] = 'TRUE'
		new_user = usersmod.object(None, lo, user_position)
		new_user.open()
		for key, value in attributes.items():
			if key in new_user and value:
				new_user[key] = value
		try:
			new_user.create()
		except univention.admin.uexceptions.base as exc:
			MODULE.error('create_self_registered_account(): could not create user: %s' % (traceback.format_exc(),))
			return {
				'success': False,
				'failType': 'CREATION_FAILED',
				'data': _('The account could not be created:\n%s') % UDM_Error(exc),
			}
		finally:
			# TODO cleanup
			# reinit user module without template.
			# This has to be done since the modules are singletons?
			univention.admin.modules.update()
			self._usersmod = None
			#  univention.admin.modules.init(lo, po, usersmod, None, True)
		try:
			# in all SS cases we need more than the previously default fields
			user_info = self._extract_user_properties(new_user)
			self.send_message(
				new_user['username'],
				'verify_email',
				new_user['PasswordRecoveryEmail'],
				user_info,
				raise_on_success=False
			)
		except Exception:
			MODULE.error('could not send message: %s' % (traceback.format_exc(),))
			verify_token_successfully_send = False
		else:
			verify_token_successfully_send = True
		return {
			'success': True,
			'verifyTokenSuccessfullySend': verify_token_successfully_send,
			'data': {
				'username': new_user['username'],
				'email': new_user['PasswordRecoveryEmail'],
			}
		}

	def _extract_user_properties(self, user_obj):
		message_fields = [
			'username',
			'title',
			'initials',
			'displayName',
			'organisation',
			'employeeNumber',
			'firstname',
			'lastname',
			'mailPrimaryAddress'
		]
		info_out = {field: user_obj.info.get(field, '') for field in message_fields}
		return info_out

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True))
	@simple_response
	def send_verification_token(self, username):
		MODULE.info("send_verification_token(): username: {}".format(username))
		ucr.load()
		if ucr.is_false('umc/self-service/account-verification/backend/enabled', True):
			msg = _('The account verification was disabled via the Univention Configuration Registry.')
			MODULE.error('send_verification_token(): {}'.format(msg))
			raise UMC_Error(msg)
		invalid_information = {
			'success': False,
			'failType': 'INVALID_INFORMATION'
		}
		users_mod = UDM.machine().version(2).get('users/user')
		try:
			user = users_mod.get_by_id(username)
		except NoObject:
			return invalid_information
		try:
			email = user.props.PasswordRecoveryEmail
		except AttributeError:
			return invalid_information
		else:
			if not email:
				return invalid_information
		user_info = self._extract_user_properties(user._orig_udm_object)
		self.send_message(username, 'verify_email', email, user_info, raise_on_success=False)
		return {
			'success': True,
			'data': {
				'username': username,
			}
		}

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		email=StringSanitizer(required=False),
		mobile=StringSanitizer(required=False))
	@simple_response
	def set_contact(self, username, password, email=None, mobile=None):
		if ucr.is_false('umc/self-service/protect-account/backend/enabled'):
			msg = _('The account protection was disabled via the Univention Configuration Registry.')
			MODULE.error('set_contact(): {}'.format(msg))
			raise UMC_Error(msg)
		MODULE.info("set_contact(): username: {} password: ***** email: {} mobile: {}".format(username, email, mobile))
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username, 'passwordreset'):
			raise ServiceForbidden()
		try:
			return self.set_contact_data(dn, email, mobile)
		except Exception:
			raise UMC_Error(_('Changing contact data failed.'), status=500)

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		method=StringSanitizer(required=True))
	@simple_response
	def send_token(self, username, method):
		if ucr.is_false('umc/self-service/passwordreset/backend/enabled'):
			msg = _('The password reset was disabled via the Univention Configuration Registry.')
			MODULE.error('send_token(): {}'.format(msg))
			raise UMC_Error(msg)
		MODULE.info("send_token(): username: '{}' method: '{}'.".format(username, method))
		try:
			plugin = self.password_reset_plugins[method]
		except KeyError:
			MODULE.error("send_token() method '{}' not in {}.".format(method, self.password_reset_plugins.keys()))
			raise UMC_Error(_("Unknown recovery method '{}'.").format(method))

		if self.is_blacklisted(username, 'passwordreset'):
			raise MissingContactInformation()

		# check if the user has the required attribute set
		user = self.get_udm_user(username=username)
		username = user["username"]

		if len(user[plugin.udm_property]) > 0:
			# found contact info
			user_info = self._extract_user_properties(user)
			self.send_message(username, method, user[plugin.udm_property], user_info, raise_on_success=True)

		# no contact info
		raise MissingContactInformation()

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		token=StringSanitizer(required=True),
		username=StringSanitizer(required=True),
		method=StringSanitizer(required=True),
	)
	@simple_response
	def verify_contact(self, token, username, method):
		MODULE.info('verify_contact(): token: {} username: {} method: {}'.format(token, username, method))
		ucr.load()
		if ucr.is_false('umc/self-service/account-verification/backend/enabled', True):
			msg = _('The account verification was disabled via the Univention Configuration Registry.')
			MODULE.error('verify_contact(): {}'.format(msg))
			raise UMC_Error(msg)
		users_mod = UDM.admin().version(1).get('users/user')
		try:
			user = users_mod.get_by_id(username)
		except NoObject:
			return {
				'success': False,
				'failType': 'INVALID_INFORMATION',
			}
		next_steps = ucr.get('umc/self-service/account-verification/next-steps/%s' % self.locale.language, '')
		if not next_steps:
			next_steps = ucr.get('umc/self-service/account-verification/next-steps', '')
		plugin = self._get_send_plugin(method)
		if getattr(user.props, plugin.udm_property) == 'TRUE':  # cleanup. map property to actual boolean?
			return {
				'success': True,
				'successType': 'ALREADY_VERIFIED',
				'data': {
					'username': username,
					'nextSteps': next_steps,
				}
			}
		self._check_token(username, token, token_application=plugin.message_application())
		setattr(user.props, plugin.udm_property, 'TRUE')
		user.save()
		self.db.delete_tokens(token=token, username=username)
		return {
			'success': True,
			'successType': 'VERIFIED',
			'data': {
				'username': username,
				'nextSteps': next_steps,
			}
		}

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
	)
	@simple_response
	def deregister_account(self, username, password):
		MODULE.info("deregister_account(): username: {} password: *****".format(username))
		ucr.load()
		if ucr.is_false('umc/self-service/account-deregistration/enabled', True):
			msg = _('The account deregistration was disabled via the Univention Configuration Registry.')
			MODULE.error('deregister_account(): {}'.format(msg))
			raise UMC_Error(msg)
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username, 'account-deregistration'):
			raise ServiceForbidden()
		try:
			return self._deregister_account(username)
		except Exception:
			raise UMC_Error(_('Account could not be deleted'), status=500)

	def _deregister_account(self, username):
		try:
			user = UDM.admin().version(2).get('users/user').get_by_id(username)
			user.props.DeregisteredThroughSelfService = 'TRUE'
			user.props.DeregistrationTimestamp = datetime.datetime.strftime(datetime.datetime.utcnow(), DEREGISTRATION_TIMESTAMP_FORMATTING)
			user.props.disabled = True
			user.save()
			try:
				self._notify_about_account_deregistration(user.props.username, user.props.PasswordRecoveryEmail)
			except Exception:
				MODULE.error("_deregister_account(): sending of email failed: {}".format(traceback.format_exc()))
			return
		except Exception:
			MODULE.error("_deregister_account(): {}".format(traceback.format_exc()))
			raise

	def _notify_about_account_deregistration(self, username, mail):
		if not mail:
			return
		ucr.load()
		path_ucr = ucr.get("umc/self-service/account-deregistration/email/text_file")
		if path_ucr and os.path.exists(path_ucr):
			path = path_ucr
		else:
			path = "/usr/share/univention-self-service/email_bodies/deregistration_notification_email_body.txt"
		with open(path, "r") as fp:
			txt = fp.read()
		txt = txt.format(username=username)
		msg = MIMENonMultipart('text', 'plain', charset='utf-8')
		msg["Subject"] = "Account deletion"
		msg["Date"] = formatdate(localtime=True)
		msg["From"] = ucr.get("umc/self-service/account-deregistration/email/sender_address", "Password Reset Service <noreply@{}>".format(".".join([ucr["hostname"], ucr["domainname"]])))
		msg["To"] = mail
		cs = email.charset.Charset("utf-8")
		cs.body_encoding = email.charset.QP
		msg.set_payload(txt, charset=cs)
		smtp = smtplib.SMTP(ucr.get("umc/self-service/account-deregistration/email/server", "localhost"))
		smtp.sendmail(msg["From"], msg["To"], msg.as_string())
		smtp.quit()

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		token=StringSanitizer(required=True),
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True))  # new_password(!)
	@simple_response
	def set_password(self, token, username, password):
		MODULE.info("set_password(): username: '{}'.".format(username))
		username = self.email2username(username)
		token_from_db = self._check_token(username, token)

		# token is correct and valid
		MODULE.info("Receive valid token for '{}'.".format(username))
		if self.is_blacklisted(username, 'passwordreset'):
			# this should not happen
			MODULE.error("Found token in DB for blacklisted user '{}'.".format(username))
			self.db.delete_tokens(token=token, username=username)
			raise ServiceForbidden()  # TokenNotFound() ?

		plugin = self._get_send_plugin(token_from_db['method'])
		email_verified = plugin.password_reset_verified_recovery_email()
		ret = self.udm_set_password(username, password, email_verified=email_verified)
		self.db.delete_tokens(token=token, username=username)
		if ret:
			raise UMC_Error(_("Successfully changed your password."), status=200)
		raise UMC_Error(_('Failed to change password.'), status=500)

	def _check_token(self, username, token, token_application='password_reset'):
		try:
			token_from_db = self.db.get_one(token=token, username=username)
		except MultipleTokensInDB as e:
			# this should not happen, delete all tokens, raise Exception
			# regardless of correctness of token
			MODULE.error("set_password(): {}".format(e))
			self.db.delete_tokens(token=token, username=username)
			raise TokenNotFound()

		if not token_from_db:
			# no token in DB
			MODULE.info("Token not found in DB for user '{}'.".format(username))
			raise TokenNotFound()

		if (datetime.datetime.utcnow() - token_from_db["timestamp"]).total_seconds() >= self.token_validity_period:
			# token is correct but expired
			MODULE.info("Receive correct but expired token for '{}'.".format(username))
			self.db.delete_tokens(token=token, username=username)
			raise TokenNotFound()

		if not self._get_send_plugin(token_from_db['method']).message_application() == token_application:
			# token is correct but should not be used for this application
			MODULE.info("Receive correct token for '{}' but it should be used for another application.".format(username))
			self.db.delete_tokens(token=token, username=username)
			raise TokenNotFound()
		return token_from_db

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_reset_methods(self, username):
		if ucr.is_false('umc/self-service/passwordreset/backend/enabled'):
			msg = _('The password reset was disabled via the Univention Configuration Registry.')
			MODULE.error('get_reset_methods(): {}'.format(msg))
			raise UMC_Error(msg)
		if self.is_blacklisted(username, 'passwordreset'):
			raise NoMethodsAvailable()

		user = self.get_udm_user(username=username)
		if not self.password_reset_plugins:
			raise NoMethodsAvailable()

		# return list of method names, for all LDAP attribs user has data
		reset_methods = [{
			"id": p.send_method(),
			"label": p.send_method_label()
		} for p in self.password_reset_plugins.values() if user[p.udm_property]]
		if not reset_methods:
			raise NoMethodsAvailable()
		return reset_methods

	@staticmethod
	def create_token(length):
		# remove easily confusable characters
		chars = ''.join(set(string.ascii_letters) | set(string.digits) - {"0", "O", "1", "I", "l"})
		rand = random.SystemRandom()
		return ''.join(rand.choice(chars) for _ in range(length))

	def send_message(self, username, method, address, user_properties, raise_on_success=True):
		plugin = self._get_send_plugin(method)
		try:
			token_from_db = self.db.get_one(username=username)
		except MultipleTokensInDB as e:
			# this should not happen, delete all tokens
			MODULE.error("send_token(): {}".format(e))
			self.db.delete_tokens(username=username)
			token_from_db = None

		token = self.create_token(plugin.token_length)
		if token_from_db:
			# replace with fresh token
			MODULE.info("send_token(): Updating token for user '{}'...".format(username))
			self.db.update_token(username, method, token)
		else:
			# store a new token
			MODULE.info("send_token(): Adding new token for user '{}'...".format(username))
			self.db.insert_token(username, method, token)
		try:
			self._call_send_msg_plugin(username, method, address, token, user_properties)
		except Exception:
			MODULE.error("send_token(): Error sending token with via '{method}' to '{username}'.".format(
				method=method, username=username))
			self.db.delete_tokens(username=username)
			raise
		if raise_on_success:
			raise UMC_Error(_("Successfully send token.").format(method), status=200)
		else:
			return True

	def _get_send_plugin(self, method):
		try:
			plugin = self.send_plugins[method]
			if not plugin.is_enabled:
				raise KeyError
		except KeyError:
			raise UMC_Error("Unknown send message method", status=500)
		return plugin

	def _call_send_msg_plugin(self, username, method, address, token, user_properties):
		MODULE.info("send_message(): username: {} method: {} address: {}".format(username, method, address))
		plugin = self._get_send_plugin(method)

		plugin.set_data({
			"username": username,
			"address": address,
			"token": token,
			"user_properties": user_properties,
		})
		MODULE.info("send_message(): Running plugin of class {}...".format(plugin.__class__.__name__))
		try:
			plugin.send()
		except Exception as exc:
			MODULE.error('Unknown error: %s' % (traceback.format_exc(),))
			raise UMC_Error(_("Error sending token: {}").format(exc), status=500)
		return True

	@staticmethod
	@machine_connection
	def auth(username, password, ldap_connection=None, ldap_position=None):
		filter_s = filter_format("(|(uid=%s)(mailPrimaryAddress=%s))", (username, username))
		users = ldap_connection.search(filter=filter_s)
		try:
			binddn, userdict = users[0]
			get_user_connection(binddn=binddn, bindpw=password)
		except (udm_errors.authFail, IndexError):
			raise ServiceForbidden()
		return binddn, userdict["uid"][0].decode('utf-8')

	def authenticate_user(self, username=None, password=None):
		"""Check if the user is already authenticated (via UMC/SAML login) or use the credentials provided via the form."""
		if username and password:  # credentials provided, use them
			dn, username = self.auth(username, password)
			return (dn, username)
		elif self.user_dn and self.username and not DISALLOW_AUTHENTICATION:  # logged in via SAML/UMC
			return (self.user_dn, self.username)
		else:  # malformed request, cannot really happen
			raise UMC_Error('Please provide username and password.')

	def set_contact_data(self, dn, email, mobile):
		try:
			user = self.get_udm_user_by_dn(userdn=dn, admin=True)
			old_email = user['PasswordRecoveryEmail']
			if email is not None and email.lower() != old_email.lower():
				try:
					user["PasswordRecoveryEmail"] = email
				except udm_errors.valueInvalidSyntax as err:
					raise UMC_Error(err)
				else:
					user['PasswordRecoveryEmailVerified'] = 'FALSE'
			if mobile is not None and mobile.lower() != user["PasswordRecoveryMobile"].lower():
				user["PasswordRecoveryMobile"] = mobile
			user.modify()
			verification_email_send = False
			if user['RegisteredThroughSelfService'] == 'TRUE':
				if old_email is not None and old_email.lower() != email.lower():
					self._notify_about_email_change(user['username'], old_email, email)
				if email is not None and email.lower() != old_email.lower():
					user_info = self._extract_user_properties(user)
					self.send_message(user['username'], 'verify_email', email, user_info, raise_on_success=False)
					verification_email_send = True
			return {
				'verificationEmailSend': verification_email_send,
				'email': email,
			}
		except Exception:
			MODULE.error("set_contact_data(): {}".format(traceback.format_exc()))
			raise

	def _notify_about_email_change(self, username, old_email, new_email):
		if not old_email:
			return
		new_email = new_email or ''
		ucr.load()
		path_ucr = ucr.get("umc/self-service/email-change-notification/email/text_file")
		if path_ucr and os.path.exists(path_ucr):
			path = path_ucr
		else:
			path = "/usr/share/univention-self-service/email_bodies/email_change_notification_email_body.txt"
		with open(path, "r") as fp:
			txt = fp.read()
		txt = txt.format(username=username, old_email=old_email, new_email=new_email)
		msg = MIMENonMultipart('text', 'plain', charset='utf-8')
		msg["Subject"] = "Account recovery email changed"
		msg["Date"] = formatdate(localtime=True)
		msg["From"] = ucr.get("umc/self-service/passwordreset/email/sender_address", "Password Reset Service <noreply@{}>".format(".".join([ucr["hostname"], ucr["domainname"]])))
		msg["To"] = old_email
		cs = email.charset.Charset("utf-8")
		cs.body_encoding = email.charset.QP
		msg.set_payload(txt, charset=cs)
		smtp = smtplib.SMTP(ucr.get("umc/self-service/passwordreset/email/server", "localhost"))
		smtp.sendmail(msg["From"], msg["To"], msg.as_string())
		smtp.quit()

	def admember_set_password(self, username, password):
		ldb_url = ucr.get('connector/ad/ldap/host')
		ldb_url = 'ldaps://%s' % (ldb_url,) if ucr.is_true('connector/ad/ldap/ldaps') else 'ldap://%s' % (ldb_url,)
		try:
			reset_username = dict(ucr)['ad/reset/username']
			with open(dict(ucr)['ad/reset/password']) as fd:
				reset_password = fd.readline().strip()
		except (EnvironmentError, KeyError):
			raise UMC_Error(_('The configuration of the password reset service is not complete. The UCR variables "ad/reset/username" and "ad/reset/password" need to be set properly. Please inform an administrator.'), status=500)
		process = Popen(['samba-tool', 'user', 'setpassword', '--username', reset_username, '--password', reset_password, '--filter', filter_format('samaccountname=%s', (username,)), '--newpassword', password, '-H', ldb_url], stdout=PIPE, stderr=STDOUT)
		stdouterr = process.communicate()[0].decode('utf-8', 'replace')

		if stdouterr:
			MODULE.process('samba-tool user setpassword: %s' % (stdouterr,))

		if process.returncode:
			MODULE.error("admember_set_password(): failed to set password. Return code: %s" % (process.returncode,))
			return False
		return True

	def udm_set_password(self, username, password, email_verified):
		user = self.get_udm_user(username=username, admin=True)
		if ucr.is_true('ad/member') and 'synced' in user.get('objectFlag', []):
			success = self.admember_set_password(username, password)
		else:
			user["password"] = password
			user["pwdChangeNextLogin"] = 0
			success = True
		if email_verified:
			user["PasswordRecoveryEmailVerified"] = 'TRUE'
		try:
			user.modify()
		except (udm_errors.pwToShort, udm_errors.pwQuality) as exc:
			raise UMC_Error(str(exc))
		except udm_errors.pwalreadyused as exc:
			raise UMC_Error(exc.message)
		except Exception:
			MODULE.error("udm_set_password(): failed to set password: {}".format(traceback.format_exc()))
			raise
		else:
			return success

	# TODO: decoratorize
	@machine_connection
	def is_blacklisted(self, username, feature, ldap_connection=None, ldap_position=None):
		def listize(li):
			return [x.strip().lower() for x in li.split(",") if x.strip()]

		bl_users = listize(ucr.get("umc/self-service/{}/blacklist/users".format(feature), ""))
		bl_groups = listize(ucr.get("umc/self-service/{}/blacklist/groups".format(feature), ""))
		wh_users = listize(ucr.get("umc/self-service/{}/whitelist/users".format(feature), ""))
		wh_groups = listize(ucr.get("umc/self-service/{}/whitelist/groups".format(feature), ""))

		username = self.email2username(username)

		# user blacklist
		if username.lower() in bl_users:
			MODULE.info("is_blacklisted(username: {}, feature: {}): match in blacklisted users".format(username, feature))
			return True

		# get groups
		try:
			filter_s = filter_format("(|(uid=%s)(mailPrimaryAddress=%s))", (username, username))
			userdn = ldap_connection.searchDn(filter=filter_s)[0]
			groups_dns = self.get_groups(userdn)
			for group_dn in list(groups_dns):
				groups_dns.extend(self.get_nested_groups(group_dn))
			groups_dns = list(set(groups_dns))
			gr_names = [x.lower() for x in self.dns_to_groupname(groups_dns)]
		except IndexError:
			# no user or no group found
			return True

		# group blacklist
		if any(gr in bl_groups for gr in gr_names):
			MODULE.info("is_blacklisted(username: {}, feature: {}): match in blacklisted groups".format(username, feature))
			return True

		# if not on blacklist, check whitelists
		# user whitelist
		if username.lower() in wh_users:
			MODULE.info("is_blacklisted(username: {}, feature: {}): match in whitelisted users".format(username, feature))
			return False

		# group whitelist
		if any(gr in wh_groups for gr in gr_names):
			MODULE.info("is_blacklisted(username: {}, feature: {}): match in whitelisted groups".format(username, feature))
			return False

		# not on either black or white list -> not allowed if whitelist exists, else OK
		MODULE.info("is_blacklisted(username: {}, feature: {}): neither black nor white listed".format(username, feature))
		return bool(wh_users or wh_groups)

	def get_groups(self, userdn):
		user = self.get_udm_user_by_dn(userdn=userdn)
		groups = user["groups"]
		prim_group = user["primaryGroup"]
		if prim_group not in groups:
			groups.append(prim_group)
		return groups

	def get_nested_groups(self, groupdn):
		group = self.get_udm_group(groupdn)
		res = group["memberOf"] or []
		for ng in list(res):
			res.extend(self.get_nested_groups(ng))
		return res

	def dns_to_groupname(self, dns):
		names = list()
		for groupdn in dns:
			group = self.get_udm_group(groupdn)
			names.append(group["name"])
		return names

	def get_udm_user_by_dn(self, userdn, admin=False):
		if admin:
			lo, po = get_admin_connection()
		else:
			lo, po = get_machine_connection()
		user = self.usersmod.object(None, lo, po, userdn)
		user.open()
		return user

	def get_udm_user(self, username, admin=False):
		filter_s = filter_format('(|(uid=%s)(mailPrimaryAddress=%s))', (username, username))

		lo, po = get_machine_connection()
		dn = lo.searchDn(filter=filter_s)[0]
		return self.get_udm_user_by_dn(dn, admin=admin)

	@machine_connection
	def get_udm_group(self, groupdn, ldap_connection=None, ldap_position=None):
		# reuse module for recursive lookups by get_nested_groups()
		if not self.groupmod:
			univention.admin.modules.update()
			self.groupmod = univention.admin.modules.get("groups/group")
			univention.admin.modules.init(ldap_connection, ldap_position, self.groupmod)

		group = self.groupmod.object(None, ldap_connection, ldap_position, groupdn)
		group.open()
		return group

	@machine_connection  # TODO: overwrite StringSanitizer and do it there
	def email2username(self, email, ldap_connection=None, ldap_position=None):
		if "@" not in email:
			return email

		# cache email->username in memcache
		username = self.memcache.get("e2u:{}".format(email))
		if not username:
			mailf = filter_format("(mailPrimaryAddress=%s)", (email,))
			users = ldap_connection.search(filter=mailf)
			try:
				_, userdict = users[0]
			except IndexError:
				return email
			username = userdict["uid"][0].decode('utf-8')
			self.memcache.set("e2u:{}".format(email), username, 300)

		return username
