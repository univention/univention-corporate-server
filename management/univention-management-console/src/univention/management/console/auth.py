#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2014-2019 Univention GmbH
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

from __future__ import absolute_import

import traceback

import ldap
from ldap.filter import filter_format

import notifier
import notifier.signals as signals
import notifier.threads as threads

import univention.admin.uexceptions as udm_errors

from univention.management.console.log import AUTH
from univention.management.console.ldap import get_machine_connection, reset_cache
from univention.management.console.pam import PamAuth, AuthenticationError, AuthenticationFailed, AuthenticationInformationMissing, PasswordExpired, AccountExpired, PasswordChangeFailed


class AuthenticationResult(object):

	def __init__(self, result):
		from univention.management.console.protocol.definitions import SUCCESS, BAD_REQUEST_UNAUTH
		self.credentials = None
		self.status = SUCCESS
		self.authenticated = not isinstance(result, BaseException)
		if self.authenticated:
			self.credentials = result
		self.message = None
		self.result = None
		self.password_expired = False
		if isinstance(result, AuthenticationError):
			self.status = BAD_REQUEST_UNAUTH
			self.message = str(result)
			self.result = {}
			if isinstance(result, PasswordExpired):
				self.result['password_expired'] = True
			elif isinstance(result, AccountExpired):
				self.result['account_expired'] = True
			elif isinstance(result, AuthenticationInformationMissing):
				self.result['missing_prompts'] = result.missing_prompts
		elif isinstance(result, BaseException):
			self.status = 500
			self.message = str(result)
		else:
			self.result = {'username': result['username']}

	def __nonzero__(self):
		return self.authenticated


class AuthHandler(signals.Provider):

	def __init__(self):
		signals.Provider.__init__(self)
		self.signal_new('authenticated')

	def authenticate(self, msg):
		# PAM MUST be initialized outside of a thread. Otherwise it segfaults e.g. with pam_saml.so.
		# See http://pam-python.sourceforge.net/doc/html/#bugs

		args = msg.body.copy()
		locale = args.pop('locale', None)
		args.pop('auth_type', None)
		args.setdefault('new_password', None)
		args.setdefault('username', '')
		args.setdefault('password', '')

		self.pam = PamAuth(locale)
		thread = threads.Simple('pam', notifier.Callback(self.__authenticate_thread, **args), notifier.Callback(self.__authentication_result, msg))
		thread.run()

	def __authenticate_thread(self, username, password, new_password, **custom_prompts):
		AUTH.info('Trying to authenticate user %r' % (username,))
		username = self.__canonicalize_username(username)
		try:
			self.pam.authenticate(username, password, **custom_prompts)
		except AuthenticationFailed as auth_failed:
			AUTH.error(str(auth_failed))
			raise
		except PasswordExpired as pass_expired:
			AUTH.info(str(pass_expired))
			if new_password is None:
				raise

			try:
				self.pam.change_password(username, password, new_password)
			except PasswordChangeFailed as change_failed:
				AUTH.error(str(change_failed))
				raise
			else:
				AUTH.info('Password change for %r was successful' % (username,))
				return (username, new_password)
		else:
			AUTH.info('Authentication for %r was successful' % (username,))
			return (username, password)

	def __canonicalize_username(self, username):
		try:
			lo, po = get_machine_connection(write=False)
			result = None
			if lo:
				attr = 'mailPrimaryAddress' if '@' in username else 'uid'
				result = lo.search(filter_format('(&(%s=%s)(objectClass=person))', (attr, username)), attr=['uid'], unique=True)
			if result and result[0][1].get('uid'):
				username = result[0][1]['uid'][0]
				AUTH.info('Canonicalized username: %r' % (username,))
		except (ldap.LDAPError, udm_errors.ldapError) as exc:
			# /etc/machine.secret missing or LDAP server not reachable
			AUTH.warn('Canonicalization of username was not possible: %s' % (exc,))
			reset_cache()
		except:
			AUTH.error('Canonicalization of username failed: %s' % (traceback.format_exc(),))
		finally:  # ignore all exceptions, even in except blocks
			return username

	def __authentication_result(self, thread, result, request):
		if isinstance(result, BaseException) and not isinstance(result, (AuthenticationFailed, AuthenticationInformationMissing, PasswordExpired, PasswordChangeFailed, AccountExpired)):
			msg = ''.join(thread.trace + traceback.format_exception_only(*thread.exc_info[:2]))
			AUTH.error(msg)
		if isinstance(result, tuple):
			username, password = result
			result = {'username': username, 'password': password, 'auth_type': request.body.get('auth_type')}
		auth_result = AuthenticationResult(result)
		self.signal_emit('authenticated', auth_result, request)
