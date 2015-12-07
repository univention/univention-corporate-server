#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: password reset service
#
# Copyright 2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import traceback
import datetime
import random
import string
import atexit
from functools import wraps
from ldap.filter import filter_format
import pylibmc

from univention.lib.i18n import Translation
import univention.admin.uexceptions
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
				username = args[0].options.get("username")
		except (IndexError, AttributeError, KeyError, TypeError):
			# args[0] is not the expected 'request'
			MODULE.error("prevent_denial_of_service() could not find username argument. self: %r args: %r kwargs: %r exception: %s" % (self, args, kwargs, traceback.format_exc()))
			raise
			# TODO: return func(self, *args, **kwargs) here?!

		if len(username) > MEMCACHED_MAX_KEY - 9:  # "_hour:exp"
			raise ServiceForbidden()

		username = self.email2username(username)
		user_limits = [
			("{}_min".format(username), 60, self.limit_user_min),
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
		super(ServiceForbidden, self).__init__(
		_("Either username or password is incorrect or you are not allowed to use this service.")
	)


class TokenNotFound(UMC_Error):
	status = 400

	def __init__(self):
		super(TokenNotFound, self).__init__(
			_("The token you supplied is either expired or invalid. Please request a new one."))


class NoMethodsAvailable(UMC_Error):

	def __init__(self):
		super(NoMethodsAvailable, self).__init__(_('No password reset method available for this user.'))


class MissingContactInformation(UMC_Error):

	def __init__(self):
		super(MissingContactInformation, self).__init__(_("No contact information to send a token for password recovery to has been found."))  # FXME: string typo


class Instance(Base):

	def init(self):
		if not ucr.is_true("umc/self-service/passwordreset/enabled"):
			err = "Module is disabled by UCR."
			MODULE.error(err)
			raise UMC_Error(err, status=500)

		self.usersmod = None
		self.usersmod_rw = None
		self.groupmod = None
		self.lo = None
		self.lo_rw = None
		self.position = None
		self.position_rw = None

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

		limit_total_min = ucr_try_int("umc/self-service/passwordreset/limit/total/min", 0)
		limit_total_hour = ucr_try_int("umc/self-service/passwordreset/limit/total/hour", 0)
		limit_total_day = ucr_try_int("umc/self-service/passwordreset/limit/total/day", 0)
		self.limit_user_min = ucr_try_int("umc/self-service/passwordreset/limit/per_user/min", 0)
		self.limit_user_hour = ucr_try_int("umc/self-service/passwordreset/limit/per_user/hour", 0)
		self.limit_user_day = ucr_try_int("umc/self-service/passwordreset/limit/per_user/day", 0)

		self.total_limits = [
			("t:c_min", 60, limit_total_min),
			("t:c_hour", 3600, limit_total_hour),
			("t:c_day", 86400, limit_total_day)
		]

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
		} for p in self.send_plugins.values() if user[p.udm_property]]

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
		for _ in xrange(length):
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
		except (univention.admin.uexceptions.authFail, IndexError):
			raise ServiceForbidden()
		return binddn, userdict["uid"][0]

	def set_contact_data(self, dn, email, mobile):
		try:
			user = self.get_udm_user_dn(userdn=dn, admin=True)
			if email is not None and email.lower() != user["PasswordRecoveryEmail"].lower():
				user["PasswordRecoveryEmail"] = email
			if mobile is not None and mobile.lower() != user["PasswordRecoveryMobile"].lower():
				user["PasswordRecoveryMobile"] = mobile
			user.modify()
			return True
		except Exception:
			MODULE.error("set_contact_data(): {}".format(traceback.format_exc()))
			raise

	def udm_set_password(self, username, password):
		try:
			user = self.get_udm_user(username=username, admin=True)
			user["password"] = password
			user["pwdChangeNextLogin"] = 0
			user.modify()
			return True
		except udm_errors.pwToShort as ex:
			raise UMC_Error(str(ex))
		except udm_errors.pwalreadyused:
			raise UMC_Error(_("The Password has been used already. Please supply a new one."))
		except:
			MODULE.info("udm_set_password(): failed to set password: {}".format(traceback.format_exc()))
			raise

	#TODO: decoratorize
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
		return not (wh_users or wh_groups)

	def get_groups(self, userdn):
		user = self.get_udm_user_dn(userdn=userdn)
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

	def get_udm_user_dn(self, userdn, admin=False):
		if admin:
			lo, po = get_admin_connection()
		else:
			lo, po = get_machine_connection()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		univention.admin.modules.init(lo, po, usersmod)
		user = usersmod.object(None, lo, po, userdn)
		user.open()
		return user

	def get_udm_user(self, username, admin=False):
		filter_s = filter_format('(|(uid=%s)(mailPrimaryAddress=%s))', (username, username))
		base = ucr["ldap/base"]

		lo, po = get_machine_connection()
		dn = lo.searchDn(filter=filter_s, base=base)[0]
		return self.get_udm_user_dn(dn)

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
				return username
			username = userdict["uid"][0]
			self.memcache.set("e2u:{}".format(email), username, 300)

		return username
