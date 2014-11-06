#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2006-2014 Univention GmbH
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

"""
Authentication mechanisms
=========================

This module defines a :class:`.AuthHandler` that provides access to
authentication modules for the UMC core. Currently it implements a
module using PAM.
"""

import notifier.signals as signals
import notifier.threads as threads

import PAM
import functools

from .log import AUTH

class AuthenticationResult(object):
	def __init__(self, success, password_valid=None, password_expired=False, error_message=None):
		from univention.management.console.protocol.definitions import status_description, BAD_REQUEST_AUTH_FAILED, BAD_REQUEST_PASSWORD_EXPIRED
		self.success = success
		if password_valid is None:
			password_valid = success
		if not success and error_message is None:
			if password_expired is True:
				self.error_message = status_description(BAD_REQUEST_PASSWORD_EXPIRED)
			else:
				self.error_message = status_description(BAD_REQUEST_AUTH_FAILED)
		else:
			self.error_message = error_message
		self.password_valid = password_valid
		self.password_expired = password_expired

	def password_is_expired(self):
		return bool(self.password_expired)

	def __nonzero__(self):
		return self.success

class Auth( signals.Provider ):
	"""
	This is the base class for authentication modules.

	**Signals:**

	* *auth_return* -- is emitted when the authentication process has finished. As argument a boolean is passed defining if the authentication was successful. This signal is used internally only by the :class:`AuthHandler`.
	* *password_changed* -- is emitted when the authentication process changed an expired password. As argument the new password is passed. This signal is used internally only by the :class:`AuthHandler`.
	"""
	def __init__( self, username, password ):
		"""This class is not meant to be instanciated directly. It is
		just a base class to define the interface for authentication
		modules.

		:param username: username to authenticate
		:param password: the secret to use for authentcation. Normally this will be a cleartext password.
		"""
		signals.Provider.__init__( self )
		self._username = username
		self._password = password

		self.signal_new( 'auth_return' )
		self.signal_new( 'password_changed' )

	def authenticate( self ):
		"""This method should be overwritten when implementing an
		authentication module. It is invoked by the UMC core when
		verifiying the credentials of a user."""
		return True

	def may_change_password( self ):
		"""This method may be overwritten when implementing an
		authentication module. It is invoked by the UMC core when
		checking if an unsuccessful authentication may be retried with
		a new password, e.g. in case of an expired password."""
		return False

	def change_expired_password( self, new_password ):
		"""This method may be overwritten when implementing an
		authentication module. It is invoked by the UMC core when
		changing an expired password to a new one."""
		return False

class PAM_Auth( Auth ):
	"""This class implements the interface :class:`Auth` to provide
	authentcation using PAM. It uses the PAM service
	*univention-management-console*.

	:param username: username to authenticate
	:param password: the secret to use for authentcation. Normally this will be a cleartext password.
	"""

	def __init__( self, username = None, password = None ):
		Auth.__init__( self, username, password )
		self._pam = PAM.pam()
		self._pam.start( 'univention-management-console' )
		self._pam.set_item( PAM.PAM_CONV, self._conv )
		self._may_change_password = False
		self.__workaround_pw_expired = False

	def may_change_password( self ):
		return self._may_change_password

	def _talk_to_pam( self, answers, save_prompts_to=None ):
		def _conv( auth, query_list, data ):
			resp = []
			if any(b == PAM.PAM_TEXT_INFO or b == PAM.PAM_ERROR_MSG for a, b in query_list):
				self.__workaround_pw_expired = True

			for query, qt in query_list:
				try:
					if save_prompts_to is not None:
						save_prompts_to.append(query)
					answer = answers[qt]
					if isinstance(answer, (list, tuple)):
						answer, others = answer[0], answer[1:]
						if len(others) == 1:
							others = others[0]
						answers[qt] = others
					resp.append( ( answer, 0 ) )
				except KeyError:
					return None
			return resp
		return _conv

	@property
	def _conv( self ):
		return self._talk_to_pam( {
			PAM.PAM_PROMPT_ECHO_ON : self._password,
			PAM.PAM_PROMPT_ECHO_OFF : self._password,
			# 'Your password will expire at ...\n' 'Changing password' 'Error: Password does not meet complexity requirements\n'
			PAM.PAM_TEXT_INFO: ['', '', ''],
			# 'You are required to change your password immediately (password aged)'
			PAM.PAM_ERROR_MSG: ['']
		} )

	def authenticate( self ):
		self._pam.set_item( PAM.PAM_USER, self._username )
		ask = threads.Simple( 'pam', self._ask_pam, self._auth_result )
		ask.run()

	def _auth_result( self, thread, success ):
		if isinstance(success, BaseException):
			success = AuthenticationResult(false)
		self.signal_emit( 'auth_return', success )

	def _ask_pam( self, new_password=None ):
		self._may_change_password = False
		try:
			AUTH.info( 'PAM: trying to authenticate %s' % self._username )
			self._pam.authenticate()
			AUTH.info( 'PAM: running acct_mgmt' )
			self._pam.acct_mgmt()
		except PAM.error, e:
			if not self.__workaround_pw_expired:
				AUTH.error( "PAM: authentication error: %s" % str( e ) )
				return AuthenticationResult(False)

			## Start workaround for broken "defer_pwchange" implementation in pam_krb5
			try:
				## This may be the second time we run it, but ok..
				self._pam.acct_mgmt()
			except PAM.error as e:
				if e[1] == PAM.PAM_NEW_AUTHTOK_REQD: # error: ('Authentication token is no longer valid; new one required', 12)
					if new_password is not None:
						prompts = []
						new_pam = PAM.pam()
						new_pam.start( 'univention-management-console' )
						new_pam.set_item( PAM.PAM_USER, self._username )
						new_pam.set_item( PAM.PAM_CONV, self._talk_to_pam( {
							PAM.PAM_PROMPT_ECHO_ON : self._username,
							PAM.PAM_PROMPT_ECHO_OFF : [self._password, new_password, new_password], # old, new, retype
						}, save_prompts_to=prompts ) )
						try:
							new_pam.chauthtok()
						except PAM.error, e:
							AUTH.warn('Change password failed (%s). Prompts: %r' % (e, prompts))
							# okay, check prompts, maybe they have a hint why it failed?
							# prompts are localised, i.e. if the operating system uses German, the prompts are German!
							# try to be exhaustive. otherwise the errors will not be presented to the user.
							known_errors = [
								([': Es ist zu kurz', ': Es ist VIEL zu kurz', ': it is WAY too short', ': Password is too short'], 'The password is too short'),
								([': Es ist zu einfach/systematisch', ': it is too simplistic/systematic', ': Password does not meet complexity requirements'], 'The password is too simple'),
								([': is a palindrome'], 'The password is a palindrome'),
								([': Es basiert auf einem Wörterbucheintrag', ': it is based on a dictionary word'], 'The password is based on a dictionary word'),
								([': Password already used'], 'The password was already used'),
								([': Es enthält nicht genug unterschiedliche Zeichen', ': it does not contain enough DIFFERENT characters'], 'The password does not contain enough different characters'),
							]
							important_prompt = prompts[-1] # last prompt is some kind of internal error message
							for possible_responses, user_friendly_response in known_errors:
								if any(resp == important_prompt for resp in possible_responses):
									message = user_friendly_response
									break
							else:
								message = important_prompt # best guess: just show the prompt
							return AuthenticationResult(False, error_message=message)

						AUTH.info('Password changed successfully for %s' % self._username)

						self.signal_emit('password_changed', new_password)
						return AuthenticationResult(True)
					else:
						AUTH.error( "PAM: password expired" )
						self._may_change_password = True
						return AuthenticationResult(False, password_valid=True, password_expired=True)

				AUTH.error( "PAM: error in acct_mgmt check for expired password: %s" % str( e ) )
				return AuthenticationResult(False)

			return AuthenticationResult(False)
		except BaseException, e: # internal error
			AUTH.warn( "PAM: global error: %s" % str( e ) )
			return AuthenticationResult(False)
		else:
			self.__workaround_pw_expired = False

		AUTH.info( 'Authentication for %s was successful' % self._username )
		return AuthenticationResult(True)

	def change_expired_password( self, new_password ):
		function = functools.partial( self._ask_pam, new_password )
		ask = threads.Simple( 'pam', function, self._auth_result )
		ask.run()

_all_modules = ( PAM_Auth, )

class AuthHandler( signals.Provider ):
	"""
	This class is instanciated by the UMC core to access the
	authentication modules.

	**Signals:**

	* *authenticated* -- is emitted when the authentication process has finished. As argument a boolean is passed defining if the authentication was successful.
	"""
	def __init__( self ):
		signals.Provider.__init__( self )
		self._modules = []
		self._current = None
		self.signal_new( 'authenticated' )
		self.__credentials = None

	def _create_modules( self, username, password ):
		global _all_modules
		self._modules = []
		for mod in _all_modules:
			instance = mod( username, password )
			instance.signal_connect( 'auth_return', self._auth_return )
			instance.signal_connect( 'password_changed', self._password_changed )
			self._modules.append( instance )
		self._modules.reverse()

	def authenticate( self, username, password, new_password=None ):
		self._create_modules( username, password )
		self._current = self._modules.pop()
		self.__new_password = new_password
		self._current.authenticate()
		self.__credentials = ( username, password )

	def credentials( self ):
		return self.__credentials

	def _password_changed( self, new_password ):
		credentials = self.__credentials
		if credentials is None:
			AUTH.warn('Password changed without credentials set!')
		else:
			self.__credentials = ( credentials[0], new_password )

	def _auth_return( self, success ):
		if success:
			self._modules = []
		else:
			current_auth_module = self._current
			if self.__new_password is not None and current_auth_module.may_change_password():
				try:
					current_auth_module.change_expired_password(self.__new_password)
					return # dont emit here. change_expired_password will emit
				except:
					pass
			else:
				try:
					self._current = self._modules.pop()
					self._current.authenticate()
					return # dont emit here. the next authenticate will emit
				except:
					pass
		self.signal_emit( 'authenticated', success )

