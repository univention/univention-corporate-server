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
import os
import os.path
import subprocess
import json
from functools import wraps

from univention.lib.i18n import Translation
from univention.uldap import getMachineConnection
import univention.admin.uldap
import univention.admin.uexceptions
import univention.admin.config
import univention.admin.objects
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer, EmailSanitizer
from univention.management.console.modules import UMC_CommandError, UMC_OptionMissing, UMC_OptionTypeError

from univention.management.console.modules.passwordreset.tokendb import TokenDB, MultipleTokensInDB

_ = Translation('univention-management-console-module-passwordreset').translate

METHODS = {
	# method: (LDAP attribute, tolken length, UCRV)
	"email": ("e-mail", 64, "self-service/email/"),
	"sms": ("mobileTelephoneNumber", 12, "self-service/sms/")}
TOKEN_VALIDITY_TIME = 3600

GRP_BLACKLIST = ["Domain Admins", "Windows Hosts", "DC Backup Hosts", "DC Slave", "Hosts", "Computers", "Backup Join", "Slave Join", "World Authority", "Null Authority", "Nobody", "Enterprise Domain Controllers", "Remote Interactive Logon", "SChannel Authentication", "Digest Authentication", "Terminal Server User", "NTLM Authentication", "Other Organization", "This Organization", "Anonymous Logon", "Network Service", "Creator Group", "Creator Owner", "Local Service", "Owner Rights", "Interactive", "Restricted", "Network", "Service", "System", "Batch", "Proxy", "IUSR", "Self", "Performance Log Users", "DnsUpdateProxy", "Cryptographic Operators", "Schema Admins", "Backup Operators", "Administrators", "Domain Computers", "Windows Authorization Access Group", "IIS_IUSRS", "RAS and IAS Servers", "Network Configuration Operators", "Account Operators", "Distributed COM Users", "Read-Only Domain Controllers", "Terminal Server License Servers", "Replicator", "Allowed RODC Password Replication Group", "Denied RODC Password Replication Group", "Enterprise Admins", "Group Policy Creator Owners", "Server Operators", "Domain Controllers", "DnsAdmins", "Cert Publishers", "Incoming Forest Trust Builders", "Event Log Readers", "Pre-Windows 2000 Compatible Access", "Remote Desktop Users", "Performance Monitor Users", "Certificate Service DCOM Access", "Enterprise Read-Only Domain Controllers"]

USER_BLACKLIST = ["Administrator", "krbtgt"]

def prevent_denial_of_service(func):
	def _decorated(self, request, *args, **kwargs):
		self.prevent_denial_of_service()
		return func(self, request, *args, **kwargs)


class ContactChangingFailed(Exception):
	pass
class UnknownMethodError(Exception):
	pass
class MethodDisabledError(Exception):
	pass


class Instance(Base):

	def init(self):
		MODULE.info("init()")
		if not ucr.is_true("umc/self-service/passwordreset/enabled"):
			err = "Module is disabled by UCR."
			MODULE.error(err)
			raise UMC_CommandError(err, status=500)

		self.db = TokenDB(MODULE)
		self.conn = self.db.conn
		atexit.register(self.db.close_db)
		if not self.db.table_exists():
			self.db.create_table()

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), password=StringSanitizer(required=True), email=EmailSanitizer(required=False), mobile=StringSanitizer(required=False))
	@simple_response
	def set_contact(self, username, password, email=None, mobile=None):
		MODULE.info("set_contact(): username: {} password: {} email: {} mobile: {}".format(username, password, email, mobile))
		if self.is_blacklisted(username):
			raise UMC_CommandError("User is blacklisted.")
		try:
			succ, dn = self.auth(username, password)
			if succ:
				return self.set_contact_data(dn, email, mobile)
			else:
				return False
		except ContactChangingFailed as exc:
			raise UMC_CommandError(str(exc), status=500)

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), method=StringSanitizer(required=True))
	@simple_response
	def send_token(self, username, method):
		MODULE.info("send_token(): username: '{}' method: '{}'.".format(username, method))
		if self.is_blacklisted(username):
			raise UMC_CommandError("User is blacklisted.")
		if method not in METHODS.keys():
			MODULE.error("send_token() method '{}' not in {}.".format(method, METHODS.keys()))
			raise UMC_OptionTypeError(_("Unknown method '{}'.".format(method)))
		# check if the user has the required attribute set
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		try:
			user = usersmod.lookup(config, lo, 'uid={}'.format(username))[0]
		except IndexError:
			# no user found
			raise UMC_CommandError(_("Unknown user '{}'.".format(username)))
		user.open()

		ldap_attr = METHODS[method][0]
		token_length = METHODS[method][1]
		if len(user[ldap_attr]) > 0:
			# found contact info
			try:
				token_from_db = self.db.get_one(username=username)
			except MultipleTokensInDB as e:
				# this should not happen, delete all tokens
				MODULE.error("send_token(): {}".format(e))
				self.db.delete_tokens(username=username)
				token_from_db = None

			token = self.create_token(token_length)
			if token_from_db:
				if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
					# token is still valid
					MODULE.info("send_token(): Token for user '{}' still valid.".format(username))
					return False
				else:
					# replace with fresh token
					MODULE.info("send_token(): Updating token for user '{}'...".format(username))
					self.db.update_token(username, method, token)
			else:
				# store a new token
				MODULE.info("send_token(): Adding new token for user '{}'...".format(username))
				self.db.insert_token(username, method, token)
			try:
				self.send_message(username, method, user[ldap_attr], token)
			except Exception as e:
				MODULE.error("send_token(): Error sending token with via '{method}' to '{username}': {ex}".format(
					method=method, username=username, ex=e))
				self.db.delete_tokens(username=username)
				return False
			return True
		else:
			# no contact info
			return False

#	@prevent_denial_of_service
	@sanitize(token=StringSanitizer(required=True), password=StringSanitizer(required=True))
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
				return False
		if token_from_db:
			if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
				# token is correct and valid
				MODULE.info("Receive valid token for '{username}'.".format(**token_from_db))
				if self.is_blacklisted(token_from_db["username"]):
					# this should not happen
					MODULE.error("Found token in DB for blacklisted user {}.".format(token_from_db["username"]))
					self.db.delete_tokens(token=token)
					raise UMC_CommandError("User is blacklisted.")
				ret = self.udm_set_password(token_from_db["username"], password)
				self.db.delete_tokens(token=token)
				return ret
			else:
				# token is correct but expired
				MODULE.info("Receive correct but expired token for '{username}'.".format(**token_from_db))
				self.db.delete_tokens(token=token)
				return False
		else:
			# no token in DB
			MODULE.info("Token '{}' not found in DB.".format(token))
			return False

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True))
	def get_reset_methods(self, request):
		username = request.options.get("username")
		if not username:
			raise UMC_OptionMissing(_("Empty username supplied."))
		MODULE.info("get_reset_methods(): username: '{}'".format(username))
		if self.is_blacklisted(username):
			raise UMC_CommandError("User is blacklisted.")
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		try:
			user = usersmod.lookup(config, lo, 'uid={}'.format(username))[0]
		except IndexError:
			# no user found
			raise UMC_CommandError(_("Unknown user '{}'.".format(username)))
		user.open()
		res = list()
		# return list of method names, for all LDAP attribs user has data
		self.finished(request.id, [k for k, v in METHODS.items() if user[v[0]]])

	@staticmethod
	def create_token(length):
		# remove easily confusable characters
		chars = string.ascii_letters.replace("l", "").replace("I", "").replace("O", "") + string.digits
		rand = random.SystemRandom()
		res = ""
		for _ in xrange(length):
			res += rand.choice(chars)
		MODULE.info("create_token(%d): %r" % (length, res))
		return res

	def send_message(self, username, method, addresses, token):
		MODULE.info("send_message(): username: {} method: {} addresses: {} token: {}".format(username, method, addresses, token))
		try:
			method_cmd = ucr.get(METHODS[method][2]+"cmd")
			method_enabled = ucr.is_true(METHODS[method][2]+"enabled")
			method_server = ucr.get(METHODS[method][2]+"server")
		except KeyError:
			raise UnknownMethodError("send_message(): Unknown method '{}'.".format(method))
		if not method_enabled:
			raise MethodDisabledError("send_message(): Method '{}' is disabled by UCR.".format(method))
		if os.path.isfile(method_cmd) and os.access(method_cmd, os.X_OK):
			infos = json.dumps({
				"server": method_server,
				"username": username,
				"addresses": addresses,
				"token": token})
			MODULE.info("send_message(): Running {}...".format(method_cmd))
			cmd_proc = subprocess.Popen(method_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			cmd_out, cmd_err = cmd_proc.communicate(input=infos)
			cmd_exit = cmd_proc.wait()
			MODULE.info("send_message(): EXIT code of {}: {}".format(method_cmd, cmd_exit))
			if cmd_out:
				MODULE.info("send_message(): STDOUT of {}:\n{}".format(method_cmd, cmd_out))
			if cmd_err:
				MODULE.info("send_message(): STDERR of {}:\n{}".format(method_cmd, cmd_err))
			if cmd_exit != 0:
				MODULE.info("send_message(): Sending not successful, deleting token...")
				self.db.delete_tokens(username=username)
			return cmd_exit == 0
		else:
			raise IOError("send_message(): Cannot execute '{}'.".format(method_cmd))

	@staticmethod
	def auth(username, password):
		MODULE.info("auth(): username: {} password: {}".format(username, password))
		try:
			lo = getMachineConnection()
			binddn = lo.search(filter="(uid={})".format(username))[0][0]
			MODULE.info("auth(): Connecting as {} to LDAP...".format(binddn))
			lo = univention.admin.uldap.access(
				host=ucr.get("ldap/server/name"),
				port=int(ucr.get("ldap/server/port", "7389")),
				base=ucr.get("ldap/base"),
				binddn=binddn,
				bindpw=password)
			MODULE.info("auth(): OK.")
		except IndexError:
			MODULE.error("auth(): ERROR: user {} does not exist".format(username))
			return False, ""
		except univention.admin.uexceptions.authFail:
			MODULE.error("auth(): ERROR: username or password is incorrect")
			return False, ""
		return True, binddn

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
			return False

	@staticmethod
	def udm_set_password(username, password):
		MODULE.info("udm_set_password(): username: {} password: {}".format(username, password))
		try:
			lo = getMachineConnection()
			dn = lo.search(filter="(uid={})".format(username))[0][0]
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
		except:
			MODULE.info("udm_set_password(): failed to set password: {}".format(traceback.format_exc()))
			return False

	#TODO: decoratorize
	def is_blacklisted(self, username):
		def listize(li):
			return [x.lower() for x in map(str.strip, li.split(",")) if x]

		bl_users = listize(ucr.get("umc/self-service/blacklist/users", ""))
		bl_groups = listize(ucr.get("umc/self-service/blacklist/group", ""))
		wh_users = listize(ucr.get("umc/self-service/whitelist/users", ""))
		wh_groups = listize(ucr.get("umc/self-service/whitelist/groups", ""))

		bl_users.extend(map(str.lower, USER_BLACKLIST))
		bl_groups.extend(map(str.lower, GRP_BLACKLIST))

		# user blacklist
		if username.lower() in bl_users:
			MODULE.info("is_blacklisted({}): match in blacklisted users".format(username))
			return True

		# get groups
		lo = getMachineConnection()
		userdn = lo.search(filter="(uid={})".format(username))[0][0]
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
			raise UMC_CommandError(_("Unknown user '{}'.".format(userdn)))
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
			raise UMC_CommandError(_('There have been too many requests in the last time. Please wait 5 minutes for the next request.'))
