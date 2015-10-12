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
from ldap import LDAPError
from ldap.filter import escape_filter_chars

from univention.lib.i18n import Translation
from univention.uldap import getMachineConnection
import univention.admin.uldap
import univention.admin.uexceptions
import univention.admin.config
import univention.admin.objects
import univention.admin.uexceptions as udm_errors
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer, EmailSanitizer
from univention.management.console.modules import UMC_Error
from univention.management.console.ldap import get_user_connection

from univention.management.console.modules.passwordreset.tokendb import TokenDB, MultipleTokensInDB
from univention.management.console.modules.passwordreset.sending import get_plugins as get_sending_plugins

_ = Translation('univention-management-console-module-passwordreset').translate

TOKEN_VALIDITY_TIME = 3600

GRP_BLACKLIST = ["Domain Admins", "Windows Hosts", "DC Backup Hosts", "DC Slave", "Hosts", "Computers", "Backup Join", "Slave Join", "World Authority", "Null Authority", "Nobody", "Enterprise Domain Controllers", "Remote Interactive Logon", "SChannel Authentication", "Digest Authentication", "Terminal Server User", "NTLM Authentication", "Other Organization", "This Organization", "Anonymous Logon", "Network Service", "Creator Group", "Creator Owner", "Local Service", "Owner Rights", "Interactive", "Restricted", "Network", "Service", "System", "Batch", "Proxy", "IUSR", "Self", "Performance Log Users", "DnsUpdateProxy", "Cryptographic Operators", "Schema Admins", "Backup Operators", "Administrators", "Domain Computers", "Windows Authorization Access Group", "IIS_IUSRS", "RAS and IAS Servers", "Network Configuration Operators", "Account Operators", "Distributed COM Users", "Read-Only Domain Controllers", "Terminal Server License Servers", "Replicator", "Allowed RODC Password Replication Group", "Denied RODC Password Replication Group", "Enterprise Admins", "Group Policy Creator Owners", "Server Operators", "Domain Controllers", "DnsAdmins", "Cert Publishers", "Incoming Forest Trust Builders", "Event Log Readers", "Pre-Windows 2000 Compatible Access", "Remote Desktop Users", "Performance Monitor Users", "Certificate Service DCOM Access", "Enterprise Read-Only Domain Controllers"]

USER_BLACKLIST = ["Administrator", "krbtgt"]


def prevent_denial_of_service(func):
	def _decorated(self, request, *args, **kwargs):
		self.prevent_denial_of_service()
		return func(self, request, *args, **kwargs)


class ContactChangingFailed(UMC_Error):
	status = 500

	def __init__(self, msg):
		super(ContactChangingFailed, self).__init__(_(msg))


class UnknownMethodError(UMC_Error):
	status = 500

	def __init__(self, msg):
		super(UnknownMethodError, self).__init__(_(msg))


class MethodDisabledError(UMC_Error):
	status = 500

	def __init__(self, msg):
		super(MethodDisabledError, self).__init__(_(msg))


class Instance(Base):

	def init(self):
		MODULE.info("init()")
		if not ucr.is_true("umc/self-service/passwordreset/enabled"):
			err = "Module is disabled by UCR."
			MODULE.error(err)
			raise UMC_Error(err, status=500)

		self.db = TokenDB(MODULE)
		self.conn = self.db.conn
		atexit.register(self.db.close_db)
		if not self.db.table_exists():
			self.db.create_table()

		self.send_plugins = get_sending_plugins(MODULE.info)

#	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		email=EmailSanitizer(required=False),
		mobile=StringSanitizer(required=False))
	@simple_response
	def set_contact(self, username, password, email=None, mobile=None):
		MODULE.info("set_contact(): username: {} password: {} email: {} mobile: {}".format(username, password, email, mobile))
		if self.is_blacklisted(username):
			raise UMC_Error(_("User is blacklisted."))
		dn = self.auth(username, password)
		return self.set_contact_data(dn, email, mobile)

#	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		method=StringSanitizer(required=True))
	@simple_response
	def send_token(self, username, method):
		MODULE.info("send_token(): username: '{}' method: '{}'.".format(username, method))
		if self.is_blacklisted(username):
			raise UMC_Error(_("User is blacklisted."))
		try:
			plugin = self.send_plugins[method]
		except KeyError:
			MODULE.error("send_token() method '{}' not in {}.".format(method, self.send_plugins.keys()))
			raise UMC_Error(_("Unknown method '{}'.".format(method)))
		# check if the user has the required attribute set
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		try:
			user = usersmod.lookup(config, lo, 'uid={}'.format(escape_filter_chars(username)))[0]
		except IndexError:
			# no user found
			raise UMC_Error(_("Unknown user '{}'.".format(username)))
		user.open()

		if len(user[plugin.ldap_attribute]) > 0:
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
				if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
					raise UMC_Error(_("Token for user '{}' still valid. Please retry in one hour.".format(username)))
				else:
					# replace with fresh token
					MODULE.info("send_token(): Updating token for user '{}'...".format(username))
					self.db.update_token(username, method, token)
			else:
				# store a new token
				MODULE.info("send_token(): Adding new token for user '{}'...".format(username))
				self.db.insert_token(username, method, token)
			try:
				self.send_message(username, method, user[plugin.ldap_attribute], token)
			except:
				MODULE.error("send_token(): Error sending token with via '{method}' to '{username}'.".format(
					method=method, username=username))
				self.db.delete_tokens(username=username)
				raise
			return True
		else:
			# no contact info
			raise UMC_Error(_("No contact information to send a token to has been found."))

#	@prevent_denial_of_service
	@sanitize(
		token=StringSanitizer(required=True),
		password=StringSanitizer(required=True))
	@simple_response
	def set_password(self, token, password):
		MODULE.info("set_password(): token: '{}' password: '{}'.".format(token, password))
		try:
			token_from_db = self.db.get_one(token=token)
		except MultipleTokensInDB as e:
				# this should not happen, delete all tokens, return False
				# regardless of correctness of token
				MODULE.error("set_password(): {}".format(e))
				self.db.delete_tokens(token=token)
				raise UMC_Error(_("A problem occurred on the server and hsa been corrected, please retry."), status=500)
		if token_from_db:
			if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
				# token is correct and valid
				MODULE.info("Receive valid token for '{username}'.".format(**token_from_db))
				if self.is_blacklisted(token_from_db["username"]):
					# this should not happen
					MODULE.error("Found token in DB for blacklisted user {}.".format(token_from_db["username"]))
					self.db.delete_tokens(token=token)
					raise UMC_Error(_("User is blacklisted."))
				ret = self.udm_set_password(token_from_db["username"], password)
				self.db.delete_tokens(token=token)
				return ret
			else:
				# token is correct but expired
				MODULE.info("Receive correct but expired token for '{username}'.".format(**token_from_db))
				self.db.delete_tokens(token=token)
				raise UMC_Error(_("The token you supplied has expired. Please request a new one."))
		else:
			# no token in DB
			MODULE.info("Token '{}' not found in DB.".format(token))
			raise UMC_Error(_("The token you supplied could not be found. Please request a new one."))

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True))
	def get_reset_methods(self, request):
		username = request.options.get("username")
		if not username:
			raise UMC_Error(_("Empty username supplied."))
		MODULE.info("get_reset_methods(): username: '{}'".format(username))
		if self.is_blacklisted(username):
			raise UMC_Error(_("User is blacklisted."))
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		try:
			user = usersmod.lookup(config, lo, 'uid={}'.format(escape_filter_chars(username)))[0]
		except IndexError:
			# no user found
			raise UMC_Error(_("Unknown user '{}'.".format(username)))
		user.open()
		# return list of method names, for all LDAP attribs user has data
		for k, v in self.send_plugins.items():
			MODULE.info("get_reset_methods(): k: {} v: {} v.ldap_attribute".format(k, v, v.ldap_attribute))
		self.finished(request.id, [k for k, v in self.send_plugins.items() if user[v.ldap_attribute]])

	@staticmethod
	def create_token(length):
		# remove easily confusable characters
		chars = string.ascii_letters.replace("l", "").replace("I", "").replace("O", "") + string.digits
		rand = random.SystemRandom()
		res = ""
		for _ in xrange(length):
			res += rand.choice(chars)
		MODULE.info("create_token({}): {}".format(length, res))
		return res

	def send_message(self, username, method, addresses, token):
		MODULE.info("send_message(): username: {} method: {} addresses: {} token: {}".format(username, method, addresses, token))
		try:
			plugin = self.send_plugins[method]
		except KeyError:
			raise UnknownMethodError("send_message(): Unknown method '{}'.".format(method))
		if not plugin.is_enabled:
			raise MethodDisabledError("send_message(): Method '{}' is disabled by UCR.".format(method))
		data = {
			"username": username,
			"addresses": addresses,
			"token": token}
		plugin.set_data(data)
		MODULE.info("send_message(): Running plugin of class {}...".format(plugin.__class__.__name__))
		try:
			ret = plugin.send()
		except Exception as ex:
			raise UMC_Error(_("Failed while sending token: {}".format(ex)), status=500)
		if ret:
			return True
		else:
			raise UMC_Error(_("Failed sending token."), status=500)

	@staticmethod
	def auth(username, password):
		MODULE.info("auth(): username: {} password: {}".format(username, password))
		lo = None
		try:
			lo = getMachineConnection()
			binddn = lo.search(filter="(uid={})".format(escape_filter_chars(username)))[0][0]
			MODULE.info("auth(): Connecting as {} to LDAP...".format(binddn))
			get_user_connection(binddn=binddn, bindpw=password)
		except univention.admin.uexceptions.authFail:
			raise UMC_Error(_("Username or password is incorrect."))
		except (LDAPError, udm_errors.ldapError, udm_errors.base):
			MODULE.error("auth(): ERROR: connecting to LDAP: {}".format(traceback.format_exc()))
			raise UMC_Error(_("Could not connect to the LDAP server."))
		finally:
			lo.lo.unbind()
		return binddn

	@staticmethod
	def set_contact_data(dn, email, mobile):
		MODULE.info("set_contact_data(): dn: {} email: {} mobile: {}".format(dn, email, mobile))
		try:
			config = univention.admin.config.config()
			univention.admin.modules.update()
			usersmod = univention.admin.modules.get("users/user")
			lo, position = univention.admin.uldap.getAdminConnection()
			univention.admin.modules.init(lo, position, usersmod)
			dn_part = dn.partition(",")
			user = usersmod.lookup(config, lo, dn_part[0], base=dn_part[-1])[0]
			user.open()
			if email and email not in user["e-mail"]:
				user["e-mail"].append(email)
			if mobile and mobile not in user["mobileTelephoneNumber"]:
				user["mobileTelephoneNumber"].append(mobile)
			user.modify()
			return True
		except:
			MODULE.info("set_contact_data(): failed to add contact: {}".format(traceback.format_exc()))
			raise ContactChangingFailed("Failed to change contact information.")

	@staticmethod
	def udm_set_password(username, password):
		MODULE.info("udm_set_password(): username: {} password: {}".format(username, password))
		try:
			lo = getMachineConnection()
			dn = lo.search(filter="(uid={})".format(escape_filter_chars(username)))[0][0]
			if dn:
				MODULE.info("udm_set_password(): DN: {}.".format(dn))
			config = univention.admin.config.config()
			univention.admin.modules.update()
			usersmod = univention.admin.modules.get("users/user")
			lo, position = univention.admin.uldap.getAdminConnection()
			univention.admin.modules.init(lo, position, usersmod)
			dn_part = dn.partition(",")
			user = usersmod.lookup(config, lo, dn_part[0], base=dn_part[-1])[0]
			user.open()
			user["password"] = password
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
	def is_blacklisted(self, username):
		def listize(li):
			return [x.lower() for x in map(str.strip, li.split(",")) if x]

		bl_users = listize(ucr.get("umc/self-service/passwordreset/blacklist/users", ""))
		bl_groups = listize(ucr.get("umc/self-service/passwordreset/blacklist/group", ""))
		wh_users = listize(ucr.get("umc/self-service/passwordreset/whitelist/users", ""))
		wh_groups = listize(ucr.get("umc/self-service/passwordreset/whitelist/groups", ""))

		bl_users.extend(map(str.lower, USER_BLACKLIST))
		bl_groups.extend(map(str.lower, GRP_BLACKLIST))

		# user blacklist
		if username.lower() in bl_users:
			MODULE.info("is_blacklisted({}): match in blacklisted users".format(username))
			return True

		# get groups
		lo = getMachineConnection()
		try:
			userdn = lo.search(filter="(uid={})".format(escape_filter_chars(username)))[0][0]
		except IndexError:
			raise UMC_Error(_("Unknown user '{}'.".format(username)))
		groups_dns= Instance.get_groups(userdn)
		for group_dn in list(groups_dns):
			groups_dns.extend(Instance.get_nested_groups(group_dn))
		groups_dns = list(set(groups_dns))
		gr_names = map(str.lower, Instance.dns_to_groupname(groups_dns))

		# group blacklist
		if any([gr in bl_groups for gr in gr_names]):
			MODULE.info("is_blacklisted({}): match in blacklisted groups".format(username))
			return True

		# if not on blacklist, check whitelists
		# user whitelist
		if username.lower() in wh_users:
			MODULE.info("is_blacklisted({}): match in whitelisted users".format(username))
			return False

		# group whitelist
		if any([gr in wh_groups for gr in gr_names]):
			MODULE.info("is_blacklisted({}): match in whitelisted groups".format(username))
			return False

		# not on either black or white list -> not allowed if whitelist exists, else OK
		MODULE.info("is_blacklisted({}): neither black nor white listed".format(username))
		return not (wh_users or wh_groups)

	@staticmethod
	def get_groups(userdn):
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		dn_part = userdn.partition(",")
		try:
			user = usersmod.lookup(config, lo, dn_part[0], base=dn_part[-1])[0]
		except IndexError:
			# no user found
			raise UMC_Error(_("Unknown user '{}'.".format(userdn)))
		user.open()
		groups = user["groups"]
		prim_group = user["primaryGroup"]
		if prim_group not in groups:
			groups.append(prim_group)
		return groups

	@staticmethod
	def get_nested_groups(groupdn):
		config = univention.admin.config.config()
		univention.admin.modules.update()
		groupmod = univention.admin.modules.get("groups/group")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, groupmod)
		dn_part = groupdn.partition(",")
		group = groupmod.lookup(config, lo, dn_part[0], base=dn_part[-1])[0]
		res = group["nestedGroup"] or []
		for ng in list(res):
			res.extend(Instance.get_nested_groups(ng))
		return res

	@staticmethod
	def dns_to_groupname(dns):
		config = univention.admin.config.config()
		univention.admin.modules.update()
		groupmod = univention.admin.modules.get("groups/group")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, groupmod)
		names = list()
		for groupdn in dns:
			dn_part = groupdn.partition(",")
			group = groupmod.lookup(config, lo, dn_part[0], base=dn_part[-1])[0]
			names.append(group["name"])
		return names

	def prevent_denial_of_service(self):
		# TODO: implement
		MODULE.error("prevent_denial_of_service(): implement me")
		if False:
			raise UMC_Error(_('There have been too many requests in the last time. Please wait 5 minutes for the next request.'))
