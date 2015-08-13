#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for actions needing credentials
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
#

from getpass import getpass, getuser
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from copy import deepcopy
import time

import ldap

from univention.config_registry import ConfigRegistry

from univention.appcenter.actions import UniventionAppAction, Abort
from univention.appcenter.udm import search_objects, get_machine_connection, get_admin_connection, get_connection

class CredentialsAction(UniventionAppAction):
	def __init__(self):
		super(CredentialsAction, self).__init__()
		self._username = None
		self._userdn = None
		self._password = None

	def setup_parser(self, parser):
		parser.add_argument('--noninteractive', action='store_true', help='Do not prompt for anything, just agree or skip')
		parser.add_argument('--username', default='Administrator', help='The username used for registering the app. Default: %(default)s')
		parser.add_argument('--pwdfile', help='Filename containing the password for registering the app. See --username')

	def _get_username(self, args):
		if self._username is not None:
			return self._username
		if args.username:
			return args.username
		if not args.noninteractive:
			try:
				username = raw_input('Username [Administrator]: ') or 'Administrator'
			except (EOFError, KeyboardInterrupt):
				raise Abort()
			self._username = username
		return username

	def _get_password(self, args):
		username = self._get_username(args)
		if not username:
			return None
		if self._password is not None:
			return self._password
		if args.pwdfile:
			password = open(args.pwdfile).read()
			if password.endswith('\n'):
				password = password[:-1]
			return password
		if not args.noninteractive:
			self._password = self._get_password_for(username)
		return self._password

	def _get_password_for(self, username):
		try:
			return getpass('Password for %s: ' % username)
		except (EOFError, KeyboardInterrupt):
			raise Abort()

	@contextmanager
	def _get_password_file(self, args=None, password=None):
		if password is None:
			password = self._get_password(args)
		if not password:
			yield None
		else:
			with NamedTemporaryFile('w+b') as password_file:
				password_file.write(password)
				password_file.flush()
				yield password_file.name

	def _get_userdn(self, args):
		username = self._get_username(args)
		if not username:
			return None
		lo, pos = self._get_ldap_connection(args=None, allow_machine_connection=True)
		users = search_objects('users/user', lo, pos, uid=username)
		if users:
			return users[0].dn
		else:
			self.fatal('Cannot find user %s' % username)

	def _get_machine_connection(self):
		try:
			return get_machine_connection()
		except IOError:
			self.fatal('/etc/machine.secret not readable')
			raise Abort()
		except ldap.INVALID_CREDENTIALS:
			self.fatal('LDAP server does not accept machine password!')
			raise Abort()
		except ldap.SERVER_DOWN:
			self.fatal('LDAP server is not running!')
			raise Abort()

	def _get_admin_connection(self):
		try:
			return get_admin_connection()
		except IOError:
			self.fatal('/etc/machine.secret not readable')
			raise Abort()
		except ldap.INVALID_CREDENTIALS:
			self.fatal('LDAP server does not accept admin password!')
			raise Abort()
		except ldap.SERVER_DOWN:
			self.fatal('LDAP server is not running!')
			raise Abort()

	def _get_ldap_connection(self, args, allow_machine_connection=False, allow_admin_connection=True):
		ucr = ConfigRegistry()
		ucr.load()
		if allow_admin_connection:
			if ucr.get('server/role') == 'domaincontroller_master' and getuser() == 'root':
				try:
					return self._get_admin_connection()
				except Abort:
					# let the user try to get a connection
					pass
		if allow_machine_connection:
			try:
				return self._get_machine_connection()
			except Abort:
				# let the user try to get a connection
				pass
		attempts = 0
		if args is not None:
			args = deepcopy(args)
			while attempts < 3:
				attempts += 1
				userdn = self._get_userdn(args)
				password = self._get_password(args)
				try:
					if not userdn or not password:
						raise ldap.INVALID_CREDENTIALS()
					return get_connection(userdn, password)
				except ldap.SERVER_DOWN:
					self.fatal('LDAP server is not running!')
					raise Abort()
				except ldap.INVALID_CREDENTIALS:
					time.sleep(0.1)
					self.warn('Invalid credentials')
					args.username = None
					self._username = None
					args.pwdfile = None
					self._password = None
			self.fatal('Too many failed attempts!')
		raise Abort()

