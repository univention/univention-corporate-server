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

import psycopg2
import psycopg2.extras

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


_ = Translation('univention-management-console-module-passwordreset').translate

DB_USER = "selfservice"
DB_NAME = "selfservice"
DB_SECRETS_FILE = "/etc/self-service-db.secret"
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
class DbException(Exception):
	pass
class MultipleTokensInDB(Exception):
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

		self.conn = self.db_open()
		atexit.register(self.close_database)
		if not self.db_table_exists():
			self.db_create_table()

	def close_database(self):
		#TODO: remove this is it works: move conn.close into init()
		MODULE.info("close_database(): closing database...")
		self.conn.close()
		MODULE.info("close_database(): done.")

	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), password=StringSanitizer(required=True),
		email=EmailSanitizer(required=True), mobile=StringSanitizer(required=True))
	@simple_response
	def editcontact(self, username, password, email, mobile):
		MODULE.info("editcontact(): username: {} password: {} email: {} mobile: {}".format(username, password, email, mobile))
		try:
			succ, dn = self.auth(username, password)
			if succ:
				return self.set_contact(dn, email, mobile)
			else:
				return False
		except ContactChangingFailed as exc:
			raise univention.management.console.base.UMC_Error(str(exc), status=500)

	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True), method=StringSanitizer(required=True))
	@simple_response
	def reset_request(self, username, method):
		MODULE.info("reset_request(): username: {} method: {} ".format(username, method))
		if method not in ["email", "sms"]:
			MODULE.error("reset_request() method '{}' not in [email, sms]".format(method))
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
			MODULE.error("reset_request(): bad method name '{}'".format(method))
			return False
		if len(user[ldap_attr]) > 0:
			# found contact info
			try:
				token_from_db = self.db_get_token(username)
			except MultipleTokensInDB as e:
				# this should not happen, delete all tokens
				MODULE.error("reset_request(): {}".format(e))
				self.db_delete_tokens(username)
				token_from_db = None

			token = self.create_token(token_length)
			if token_from_db:
				if datetime.datetime.now() - token_from_db["timestamp"] < TOKEN_VALIDITY_TIME:
					# token is still valid
					return False
				else:
					# replace with fresh token
					self.db_update_token(username, method, token)
			else:
				# store a new token
				self.db_insert_token(username, method, token)
			try:
				self.send_token(username, method, user[ldap_attr], token)
			except Exception as e:
				MODULE.error("Error sending token with via '{method}' to '{username}': {ex}".format(
					method=method, username=username, ex=e))
				return False
			return True
		else:
			# no contact info
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

	def db_insert_token(self, username, method, token):
		sql = "INSERT INTO tokens (username, method, timestamp, token) VALUES ('{username}', '{method}', '{ts}', '{token}');".format(
			username=username, method=method, ts=datetime.datetime.now(), token=token)
		cur = self.conn.cursor()
		cur.execute(sql)
		self.conn.commit()
		cur.close()

	def db_update_token(self, username, method, token):
		sql = "UPDATE tokens SET method='{method}', timestamp='{ts}', token='{token}' WHERE username='{username}';".format(
			username=username, method=method, ts=datetime.datetime.now(), token=token)
		cur = self.conn.cursor()
		cur.execute(sql)
		self.conn.commit()
		cur.close()

	def db_delete_tokens(self, username):
		sql = "DELETE FROM tokens WHERE username='{}';".format(username)
		cur = self.conn.cursor()
		cur.execute(sql)
		self.conn.commit()
		cur.close()

	def db_get_token(self, username):
		sql = "SELECT * FROM tokens WHERE username='{}';".format(username)
		cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute(sql)
		rows = cur.fetchall()
		cur.close()
		if len(rows) > 1:
			raise MultipleTokensInDB("Found {} tokens in DB for '{}'.".format(len(rows), username))
		return rows[0]

	def db_create_table(self):
		MODULE.info("db_create_table(): Creating table 'tokens' and constraints...")
		cur = self.conn.cursor()
		cur.execute("""CREATE TABLE tokens
(id SERIAL PRIMARY KEY NOT NULL,
username VARCHAR(255) NOT NULL,
method VARCHAR(255) NOT NULL,
timestamp TIMESTAMP NOT NULL,
token VARCHAR(255) NOT NULL);""")
		cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_id UNIQUE (id);")
		cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_username UNIQUE (username);")
		self.conn.commit()
		cur.close()

	@staticmethod
	def db_open():
		try:
			with open(DB_SECRETS_FILE) as pw_file:
				password = pw_file.readline().strip()
		except (OSError, IOError) as e:
			MODULE.error("open_db(): Could not read {}: {}".format(DB_SECRETS_FILE, e))
			raise
		try:
			conn = psycopg2.connect("dbname={db_name} user={db_user} host='localhost' password='{db_pw}'".format(
				db_name=DB_NAME, db_user=DB_USER, db_pw=password))
			MODULE.info("open_db(): Connected to database '{}' on server with version {} using protocol version {}.".format(
				DB_NAME, conn.server_version, conn.protocol_version))
			return conn
		except:
			MODULE.error("open_db(): Error connecting to database '{}': {}".format(DB_NAME, traceback.format_exc()))
			raise

	def db_table_exists(self):
		cur = self.conn.cursor()
		cur.execute("SELECT * FROM pg_catalog.pg_tables WHERE tablename='tokens'")
		rows = cur.fetchall()
		cur.close()
		return len(rows) < 1

	def send_token(self, username, method, addresses, token):
		MODULE.info("send_token(): username: {} method: {} addresses: {} token: {}".format(username, method, addresses, token))
		try:
			method_cmd = ucr.get(METHODS[method][2]+"cmd")
			method_enabled = ucr.is_true(METHODS[method][2]+"enabled")
			method_server = ucr.get(METHODS[method][2]+"server")
		except KeyError:
			raise UnknownMethodError("Unknown method '{}'.".format(method))
		if not method_enabled:
			raise MethodDisabledError("Method '{}' is disabled by UCR.".format(method))
		if os.path.isfile(method_cmd) and os.access(method_cmd, os.X_OK):
			infos = json.dumps({
				"server": method_server,
				"username": username,
				"addresses": addresses,
				"token": token})
			cmd_proc = subprocess.Popen(method_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			cmd_out, cmd_err = cmd_proc.communicate(input=infos)
			cmd_exit = cmd_proc.wait()
			MODULE.info("EXIT code of {}: {}".format(method_cmd, cmd_exit))
			if cmd_out:
				MODULE.info("STDOUT of {}:\n{}\n-------------".format(method_cmd, cmd_out))
			if cmd_err:
				MODULE.info("STDERR of {}:\n{}\n-------------".format(method_cmd, cmd_err))
			if cmd_exit != 0:
				self.db_delete_tokens(username)
			return cmd_exit == 0
		else:
			raise IOError("Cannot execute '{}'.".format(method_cmd))

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
			MODULE.info("set_contact(): failed to set contact in LDAP: {}".format(traceback.format_exc()))
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
