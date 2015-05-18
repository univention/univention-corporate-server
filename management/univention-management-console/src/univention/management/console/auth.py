#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2014-2015 Univention GmbH
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

import notifier
import notifier.signals as signals
import notifier.threads as threads

from univention.management.console.log import AUTH
from univention.management.console.pam import PamAuth, AuthenticationError, AuthenticationFailed, PasswordExpired, PasswordChangeFailed


class AuthenticationResult(object):

	def __init__(self, result):
		from univention.management.console.protocol.definitions import SUCCESS, BAD_REQUEST_AUTH_FAILED, BAD_REQUEST_PASSWORD_EXPIRED
		self.credentials = (None, None)
		self.status = SUCCESS
		self.authenticated = not isinstance(result, BaseException)
		if self.authenticated:
			self.credentials = result
		self.message = None
		self.password_expired = False
		if isinstance(result, AuthenticationError):
			self.status = BAD_REQUEST_AUTH_FAILED
			self.message = str(result)
			if isinstance(result, PasswordExpired):
				self.status = BAD_REQUEST_PASSWORD_EXPIRED
				self.password_expired = True
		elif isinstance(result, BaseException):
			self.status = 500
			self.message = str(result)

	def __nonzero__(self):
		return self.authenticated


class AuthHandler(signals.Provider):

	def __init__(self):
		signals.Provider.__init__(self)
		self.signal_new('authenticated')

	def authenticate(self, username, password, new_password=None, locale=None):
		thread = threads.Simple('pam', notifier.Callback(self.__authenticate_thread, username, password, new_password, locale), self.__authentication_result)
		thread.run()

	def __authenticate_thread(self, username, password, new_password, locale):
		AUTH.info('Trying to authenticate user %r' % (username,))
		pam = PamAuth(locale)
		try:
			pam.authenticate(username, password)
		except AuthenticationFailed as auth_failed:
			AUTH.error(str(auth_failed))
			raise
		except PasswordExpired as pass_expired:
			AUTH.info(str(pass_expired))
			if new_password is None:
				raise

			try:
				pam.change_password(username, password, new_password)
			except PasswordChangeFailed as change_failed:
				AUTH.error(str(change_failed))
				raise
			else:
				AUTH.info('Password change for %r was successful' % (username,))
				return (username, new_password)
		else:
			AUTH.info('Authentication for %r was successful' % (username,))
			return (username, password)

	def __authentication_result(self, thread, result):
		if isinstance(result, BaseException) and not isinstance(result, (AuthenticationFailed, PasswordExpired, PasswordChangeFailed)):
			import traceback
			AUTH.error(''.join(traceback.format_exception(*thread.exc_info)))
		auth_result = AuthenticationResult(result)
		self.signal_emit('authenticated', auth_result)
