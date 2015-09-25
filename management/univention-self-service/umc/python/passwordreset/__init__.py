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
import univention.management.console.base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer, EmailSanitizer

from univention.management.console.modules.passwordreset.tokendb import TokenDB, MultipleTokensInDB

_ = Translation('univention-management-console-module-passwordreset').translate

METHODS = {
	# method: (LDAP attribute, tolken length, UCRV)
	"email": ("e-mail", 64, "self-service/email/"),
	"sms": ("mobileTelephoneNumber", 12, "self-service/sms/")}
TOKEN_VALIDITY_TIME = 3600


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


class Instance(univention.management.console.base.Base):

	def init(self):
		MODULE.info("init()")
		if not ucr.is_true("umc/self-service/enabled"):
			err = "Module is disabled by UCR."
			MODULE.error(err)
			raise univention.management.console.base.UMC_Error(err, status=500)

		self.db = TokenDB(MODULE)
		self.conn = self.db.conn
		atexit.register(self.db.close_db)
		if not self.db.table_exists():
			self.db.create_table()

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), password=StringSanitizer(required=True), email=EmailSanitizer(required=False), mobile=StringSanitizer(required=False))
	@simple_response
	def edit_contact(self, username, password, email=None, mobile=None):
		MODULE.info("editcontact(): username: {} password: {} email: {} mobile: {}".format(username, password, email, mobile))

		try:
			succ, dn = self.auth(username, password)
			if succ:
				return self.set_contact(dn, email, mobile)
			else:
				return False
		except ContactChangingFailed as exc:
			raise univention.management.console.base.UMC_Error(str(exc), status=500)

#	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), method=StringSanitizer(required=True))
	@simple_response
	def request_reset(self, username, method):
		MODULE.info("request_reset(): username: '{}' method: '{}'.".format(username, method))
		if method not in METHODS.keys():
			MODULE.error("request_reset() method '{}' not in {}.".format(method, METHODS.keys()))
			return False
		# check if the user has the required attribute set
		config = univention.admin.config.config()
		univention.admin.modules.update()
		usersmod = univention.admin.modules.get("users/user")
		lo, position = univention.admin.uldap.getMachineConnection()
		univention.admin.modules.init(lo, position, usersmod)
		user = usersmod.lookup(config, lo, 'uid={}'.format(username))[0]
		user.open()
		try:
			ldap_attr = METHODS[method][0]
			token_length = METHODS[method][1]
		except KeyError:
			#raise UnknownMethodError
			MODULE.error("request_reset(): bad method name '{}'".format(method))
			return False
		if len(user[ldap_attr]) > 0:
			# found contact info
			try:
				token_from_db = self.db.get_one(username=username)
			except MultipleTokensInDB as e:
				# this should not happen, delete all tokens
				MODULE.error("request_reset(): {}".format(e))
				self.db.delete_tokens(username)
				token_from_db = None

			token = self.create_token(token_length)
			if token_from_db:
				if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
					# token is still valid
					MODULE.info("request_reset(): Token for user '{}' still valid.".format(username))
					return False
				else:
					# replace with fresh token
					MODULE.info("request_reset(): Updating token for user '{}'...".format(username))
					self.db.update_token(username, method, token)
			else:
				# store a new token
				MODULE.info("request_reset(): Adding new token for user '{}'...".format(username))
				self.db.insert_token(username, method, token)
			try:
				self.send_token(username, method, user[ldap_attr], token)
			except Exception as e:
				MODULE.error("request_reset(): Error sending token with via '{method}' to '{username}': {ex}".format(
					method=method, username=username, ex=e))
				return False
			return True
		else:
			# no contact info
			return False

#	@prevent_denial_of_service
	@sanitize(token=StringSanitizer(required=True), password=StringSanitizer(required=True))
	@simple_response
	def submit_token(self, token, password):
		MODULE.info("submit_token(): token: '{}' password: '{}'.".format(token, password))
		try:
			token_from_db = self.db.get_one(token=token)
		except MultipleTokensInDB as e:
				# this should not happen, delete all tokens, return False
				# regardless of correctness of token
				MODULE.error("submit_token(): {}".format(e))
				self.db.delete_tokens(token=token)
				return False
		if token_from_db:
			if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
				# token is correct and valid
				MODULE.info("Receive valid token for '{username}'.".format(token_from_db))
				ret = self.set_password(token_from_db["username"], password)
				self.db.delete_tokens(token=token)
				return ret
			else:
				# token is correct but expired
				MODULE.info("Receive correct but expired token for '{username}'.".format(token_from_db))
				self.db.delete_tokens(token=token)
				return False
		else:
			# no token in DB
			MODULE.info("Token '{}' not found in DB.".format(token))
			return False

	@staticmethod
	def create_token(length):
		chars = string.ascii_letters + string.digits
		rand = random.SystemRandom()
		res = ""
		for _ in xrange(length):
			res += rand.choice(chars)
		MODULE.info("create_token(%d): %r" % (length, res))
		return res

	def send_token(self, username, method, addresses, token):
		MODULE.info("send_token(): username: {} method: {} addresses: {} token: {}".format(username, method, addresses, token))
		try:
			method_cmd = ucr.get(METHODS[method][2]+"cmd")
			method_enabled = ucr.is_true(METHODS[method][2]+"enabled")
			method_server = ucr.get(METHODS[method][2]+"server")
		except KeyError:
			raise UnknownMethodError("send_token(): Unknown method '{}'.".format(method))
		if not method_enabled:
			raise MethodDisabledError("send_token(): Method '{}' is disabled by UCR.".format(method))
		if os.path.isfile(method_cmd) and os.access(method_cmd, os.X_OK):
			infos = json.dumps({
				"server": method_server,
				"username": username,
				"addresses": addresses,
				"token": token})
			MODULE.info("send_token(): Running {}...".format(method_cmd))
			cmd_proc = subprocess.Popen(method_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			cmd_out, cmd_err = cmd_proc.communicate(input=infos)
			cmd_exit = cmd_proc.wait()
			MODULE.info("send_token(): EXIT code of {}: {}".format(method_cmd, cmd_exit))
			if cmd_out:
				MODULE.info("send_token(): STDOUT of {}:\n{}".format(method_cmd, cmd_out))
			if cmd_err:
				MODULE.info("send_token(): STDERR of {}:\n{}".format(method_cmd, cmd_err))
			if cmd_exit != 0:
				MODULE.info("send_token(): Sending not successful, deleting token...")
				self.db.delete_tokens(username)
			return cmd_exit == 0
		else:
			raise IOError("send_token(): Cannot execute '{}'.".format(method_cmd))

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
	def set_contact(dn, email, mobile):
		MODULE.info("set_contact(): dn: {} email: {} mobile: {}".format(dn, email, mobile))
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
			MODULE.info("set_contact(): failed to add contact: {}".format(traceback.format_exc()))
			return False

	@staticmethod
	def set_password(username, password):
		MODULE.info("set_password(): username: {} password: {}".format(username, password))
		try:
			lo = getMachineConnection()
			dn = lo.search(filter="(uid={})".format(username))[0][0]
			if dn:
				MODULE.info("set_password(): DN: {}.".format(dn))
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
			MODULE.info("set_password(): failed to set password: {}".format(traceback.format_exc()))
			return False

	def prevent_denial_of_service(self):
		# TODO: implement
		MODULE.error("prevent_denial_of_service(): implement me")
		if False:
			raise univention.management.console.base.UMC_Error(_('There have been too many requests in the last time. Please wait 5 minutes for the next request.'))


	# def load_plugins(self):
	# 	pass # e.g. SMTP or SMS service
	#
	# def open_database_connection(self):
	# 	# see <http://www.postgresql.org/docs/8.4/static/libpq-connect.html>
	# 	connection_info = {
	# 		'dbname': 'pkgdb',
	# 		#'sslmode': 'require'
	# 		}
	# 	connection_info['host'] = db_server
	# 	connection_info['user'] = db_user
	# 	password_file = ''
	# 	with open(password_file, 'rb') as fd:
	# 		connection_info['password'] = fd.read().rstrip('\n')
	# 	connectstring = ' '.join(["%s='%s'" % (key, value.replace('\\', '\\\\').replace("'", "\\'"),) for (key, value, ) in connection_info.items()])
	# 	self.connection = pgdb.connect(database=connectstring)
	#
	# @prevent_denial_of_service
	# @sanitize(
	# 	username=StringSanitizer(required=True),
	# 	mailaddress=EmailSanitizer(required=True),
	# )
	# @simple_response
	# def request_token(self, username, mailaddress):
	# 	if invalid:
	# 		raise UMC_Error(_('This user is not allowed to reset its password.'))
	# 	return 'token'
	#
	# @prevent_denial_of_service
	# @sanitize(
	# 	token=StringSanitizer(required=True),
	# )
	# @simple_response
	# def submit_token(self, token):
	# 	username = self.get_username_by_token(token)
	# 	try:
	# 		self.reset_password(username)
	# 	except PasswordChangingFailed as exc:
	# 		raise UMC_Error(str(exc), status=500)
	# 	return True
	#
