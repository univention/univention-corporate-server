#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: password reset service
#
# Copyright 2015-2019 Univention GmbH
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
from functools import wraps
from subprocess import Popen, PIPE, STDOUT

from ldap.filter import filter_format
import pylibmc

from univention.lib.i18n import Translation
from univention.lib.umc import Client, HTTPError, ConnectionError, Unauthorized
import univention.admin.objects
import univention.admin.uexceptions as udm_errors
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.modules import UMC_Error
from univention.management.console.ldap import get_user_connection, get_machine_connection, get_admin_connection, machine_connection

from univention.management.console.modules.passwordreset.tokendb import TokenDB, MultipleTokensInDB
from univention.management.console.modules.passwordreset.sending import get_plugins as get_sending_plugins

_ = Translation('univention-self-service-passwordreset-umc').translate

TOKEN_VALIDITY_TIME = 3600
MEMCACHED_SOCKET = "/var/lib/univention-self-service-passwordreset-umc/memcached.socket"
MEMCACHED_MAX_KEY = 250

SELFSERVICE_MASTER = ucr.get("self-service/backend-server", ucr.get("ldap/master"))
IS_SELFSERVICE_MASTER = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname')) == SELFSERVICE_MASTER

if IS_SELFSERVICE_MASTER:
	try:
		from univention.management.console.modules.udm.syntax import widget
		from univention.management.console.modules.udm.udm_ldap import UDM_Error
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
		_max_wait = datetime.datetime.now()
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
						"{}:exp".format(key): datetime.datetime.now() + datetime.timedelta(seconds=decay)
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
			time_s = _pretty_time((max(total_max_wait, user_max_wait) - datetime.datetime.now()).seconds)
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
		if not ucr.is_true("umc/self-service/passwordreset/enabled"):
			raise UMC_Error(_('The password reset service is disabled via configuration registry.'), status=503)

		if not IS_SELFSERVICE_MASTER:
			return

		self._usersmod = None
		self.groupmod = None

		self.db = TokenDB(MODULE)
		self.conn = self.db.conn
		atexit.register(self.db.close_db)
		if not self.db.table_exists():
			self.db.create_table()

		def ucr_try_int(variable, default):
			try:
				return int(ucr.get(variable, default))
			except ValueError:
				MODULE.error('UCR variables %s is not a number, using default: %s' % (variable, default))
				return default

		self.token_validity_period = ucr_try_int("umc/self-service/passwordreset/token_validity_period", 3600)
		self.send_plugins = get_sending_plugins(MODULE.process)
		self.memcache = pylibmc.Client([MEMCACHED_SOCKET], binary=True)

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
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_contact(self, username, password):
		"""
		Get users contact data.

		:return: list of dicts with users contact data
		"""
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username):
			raise ServiceForbidden()

		user = self.get_udm_user(username=username)
		if not self.send_plugins:
			raise ServiceForbidden()

		return [{
			"id": p.send_method(),
			"label": p.send_method_label(),
			"value": user[p.udm_property]
		} for p in self.send_plugins.values() if p.udm_property in user]

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_user_attributes(self, username, password):
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username):
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
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def validate_user_attributes(self, username, password, attributes):
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username):
			raise ServiceForbidden()

		res = {}
		for propname, value in attributes.items():
			prop = self.usersmod.property_descriptions.get(propname)
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

			_isValid = all(isValid) if type(isValid) == list else isValid
			if _isValid and prop.required and not value:
				isValid = False
				message = _('This value is required')
			res[propname] = {
				'isValid': isValid,
				'message': message,
			}
		return res

	@forward_to_master
	@sanitize(
		username=StringSanitizer(required=True, minimum=1),
		password=StringSanitizer(required=True, minimum=1))
	@simple_response
	def set_user_attributes(self, username, password, attributes):
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username):
			raise ServiceForbidden()

		user_attributes = [attr.strip() for attr in ucr.get('self-service/udm_attributes', '').split(',')]
		lo, po = get_user_connection(binddn=dn, bindpw=password)
		user = self.usersmod.object(None, lo, po, dn)
		user.open()
		for propname, value in attributes.items():
			if propname in user_attributes and user.has_property(propname):
				user[propname] = value
		try:
			user.modify()
		except univention.admin.uexceptions.base as exc:
			MODULE.error('set_user_attributes(): modifying the user failed: %s' % (traceback.format_exc(),))
			raise UMC_Error(_('The attributes could not be saved: %s') % (UDM_Error(exc)))
		return _("Successfully changed your profile data.")

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		email=StringSanitizer(required=False),
		mobile=StringSanitizer(required=False))
	@simple_response
	def set_contact(self, username, password, email=None, mobile=None):
		MODULE.info("set_contact(): username: {} password: ***** email: {} mobile: {}".format(username, email, mobile))
		dn, username = self.auth(username, password)
		if self.is_blacklisted(username):
			raise ServiceForbidden()
		if self.set_contact_data(dn, email, mobile):
			raise UMC_Error(_("Successfully changed your contact data."), status=200)
		raise UMC_Error(_('Changing contact data failed.'), status=500)

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		method=StringSanitizer(required=True))
	@simple_response
	def send_token(self, username, method):
		MODULE.info("send_token(): username: '{}' method: '{}'.".format(username, method))
		try:
			plugin = self.send_plugins[method]
		except KeyError:
			MODULE.error("send_token() method '{}' not in {}.".format(method, self.send_plugins.keys()))
			raise UMC_Error(_("Unknown recovery method '{}'.").format(method))

		if self.is_blacklisted(username):
			raise MissingContactInformation()

		# check if the user has the required attribute set
		user = self.get_udm_user(username=username)
		username = user["username"]

		if len(user[plugin.udm_property]) > 0:
			# found contact info
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
				self.send_message(username, method, user[plugin.udm_property], token)
			except:
				MODULE.error("send_token(): Error sending token with via '{method}' to '{username}'.".format(
					method=method, username=username))
				self.db.delete_tokens(username=username)
				raise
			raise UMC_Error(_("Successfully send token.").format(method), status=200)

		# no contact info
		raise MissingContactInformation()

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

		if (datetime.datetime.now() - token_from_db["timestamp"]).seconds >= TOKEN_VALIDITY_TIME:
			# token is correct but expired
			MODULE.info("Receive correct but expired token for '{}'.".format(username))
			self.db.delete_tokens(token=token, username=username)
			raise TokenNotFound()

		# token is correct and valid
		MODULE.info("Receive valid token for '{}'.".format(username))
		if self.is_blacklisted(username):
			# this should not happen
			MODULE.error("Found token in DB for blacklisted user '{}'.".format(username))
			self.db.delete_tokens(token=token, username=username)
			raise ServiceForbidden()  # TokenNotFound() ?
		ret = self.udm_set_password(username, password)
		self.db.delete_tokens(token=token, username=username)
		if ret:
			raise UMC_Error(_("Successfully changed your password."), status=200)
		raise UMC_Error(_('Failed to change password.'), status=500)

	@forward_to_master
	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True, minimum=1))
	@simple_response
	def get_reset_methods(self, username):
		if self.is_blacklisted(username):
			raise NoMethodsAvailable()

		user = self.get_udm_user(username=username)
		if not self.send_plugins:
			raise NoMethodsAvailable()

		# return list of method names, for all LDAP attribs user has data
		reset_methods = [{"id": p.send_method(), "label": p.send_method_label()} for p in self.send_plugins.values() if user[p.udm_property]]
		if not reset_methods:
			raise NoMethodsAvailable()
		return reset_methods

	@staticmethod
	def create_token(length):
		# remove easily confusable characters
		chars = string.ascii_letters.replace("l", "").replace("I", "").replace("O", "") + "".join(map(str, range(2, 10)))
		rand = random.SystemRandom()
		res = ""
		for _ in range(length):
			res += rand.choice(chars)
		return res

	def send_message(self, username, method, address, token):
		MODULE.info("send_message(): username: {} method: {} address: {}".format(username, method, address))
		try:
			plugin = self.send_plugins[method]
			if not plugin.is_enabled:
				raise KeyError
		except KeyError:
			raise UMC_Error("Method not allowed!", status=403)

		plugin.set_data({
			"username": username,
			"address": address,
			"token": token})
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
		return binddn, userdict["uid"][0]

	def set_contact_data(self, dn, email, mobile):
		try:
			user = self.get_udm_user_by_dn(userdn=dn, admin=True)
			if email is not None and email.lower() != user["PasswordRecoveryEmail"].lower():
				try:
					user["PasswordRecoveryEmail"] = email
				except udm_errors.valueInvalidSyntax as err:
					raise UMC_Error(err)
			if mobile is not None and mobile.lower() != user["PasswordRecoveryMobile"].lower():
				user["PasswordRecoveryMobile"] = mobile
			user.modify()
			return True
		except Exception:
			MODULE.error("set_contact_data(): {}".format(traceback.format_exc()))
			raise

	def admember_set_password(self, username, password):
		ldb_url = ucr.get('connector/ad/ldap/host')
		ldb_url = 'ldaps://%s' % (ldb_url,) if ucr.is_true('connector/ad/ldap/ldaps') else 'ldap://%s' % (ldb_url,)
		try:
			reset_username = dict(ucr)['ad/reset/username']
			with open(dict(ucr)['ad/reset/password']) as fd:
				reset_password = fd.readline().strip()
		except (EnvironmentError, KeyError):
			raise UMC_Error(_('The configuration of the password reset service is not complete. The UCR variables "ad/reset/username" and "ad/reset/password" need to be set properly. Please inform an administration.'), status=500)
		process = Popen(['samba-tool', 'user', 'setpassword', '--username', reset_username, '--password', reset_password, '--filter', filter_format('samaccountname=%s', (username,)), '--newpassword', password, '-H', ldb_url], stdout=PIPE, stderr=STDOUT)
		stdouterr = process.communicate()[0]

		if stdouterr:
			MODULE.process('samba-tool user setpassword: %s' % (stdouterr,))

		if process.returncode:
			MODULE.error("admember_set_password(): failed to set password. Return code: %s" % (process.returncode,))
			return False
		return True

	def udm_set_password(self, username, password):
		user = self.get_udm_user(username=username, admin=True)
		if ucr.is_true('ad/member') and 'synced' in user.get('objectFlag', []):
			return self.admember_set_password(username, password)
		try:
			user["password"] = password
			user["pwdChangeNextLogin"] = 0
			user.modify()
			return True
		except (udm_errors.pwToShort, udm_errors.pwQuality) as exc:
			raise UMC_Error(str(exc))
		except udm_errors.pwalreadyused as exc:
			raise UMC_Error(exc.message)
		except Exception:
			MODULE.error("udm_set_password(): failed to set password: {}".format(traceback.format_exc()))
			raise

	# TODO: decoratorize
	@machine_connection
	def is_blacklisted(self, username, ldap_connection=None, ldap_position=None):
		def listize(li):
			return [x.lower() for x in map(str.strip, li.split(",")) if x]

		bl_users = listize(ucr.get("umc/self-service/passwordreset/blacklist/users", ""))
		bl_groups = listize(ucr.get("umc/self-service/passwordreset/blacklist/groups", ""))
		wh_users = listize(ucr.get("umc/self-service/passwordreset/whitelist/users", ""))
		wh_groups = listize(ucr.get("umc/self-service/passwordreset/whitelist/groups", ""))

		username = self.email2username(username)

		# user blacklist
		if username.lower() in bl_users:
			MODULE.info("is_blacklisted({}): match in blacklisted users".format(username))
			return True

		# get groups
		try:
			filter_s = filter_format("(|(uid=%s)(mailPrimaryAddress=%s))", (username, username))
			userdn = ldap_connection.search(filter=filter_s)[0][0]
			groups_dns = self.get_groups(userdn)
			for group_dn in list(groups_dns):
				groups_dns.extend(self.get_nested_groups(group_dn))
			groups_dns = list(set(groups_dns))
			gr_names = map(str.lower, self.dns_to_groupname(groups_dns))
		except IndexError:
			# no user or no group found
			return True

		# group blacklist
		if any(gr in bl_groups for gr in gr_names):
			MODULE.info("is_blacklisted({}): match in blacklisted groups".format(username))
			return True

		# if not on blacklist, check whitelists
		# user whitelist
		if username.lower() in wh_users:
			MODULE.info("is_blacklisted({}): match in whitelisted users".format(username))
			return False

		# group whitelist
		if any(gr in wh_groups for gr in gr_names):
			MODULE.info("is_blacklisted({}): match in whitelisted groups".format(username))
			return False

		# not on either black or white list -> not allowed if whitelist exists, else OK
		MODULE.info("is_blacklisted({}): neither black nor white listed".format(username))
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
		res = group["nestedGroup"] or []
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
		base = ucr["ldap/base"]

		lo, po = get_machine_connection()
		dn = lo.searchDn(filter=filter_s, base=base)[0]
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
			username = userdict["uid"][0]
			self.memcache.set("e2u:{}".format(email), username, 300)

		return username
