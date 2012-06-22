#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2006-2012 Univention GmbH
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

from .log import *

from univention.lib.i18n import Translation

_ = Translation( 'univention.management.console' ).translate

class Auth( signals.Provider ):
	"""
	This is the base class for authentication modules.

	**Signals:**

	* *auth_return* -- is emitted when the authentication process has finished. As argument a boolean is passed defining if the authentication was successful. This signal is used internally only by the :class:`AuthHandler`.
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

	def authenticate( self ):
		"""This method should be overwritten when implementing an
		authentication module. It is invoked by the UMC core when
		verifiying the credentials of a user."""
		return True

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

	def _conv( self, auth, query_list, data ):
		resp = []
		for query, qt in query_list:
			if qt == PAM.PAM_PROMPT_ECHO_ON:
				resp.append( ( self._password, 0 ) )
			elif qt == PAM.PAM_PROMPT_ECHO_OFF:
				resp.append( ( self._password, 0 ) )
			elif qt == PAM.PAM_PROMPT_ERROR_MSG or qt == PAM.PAM_PROMPT_TEXT_INFO:
				resp.append( ( '', 0 ) )
			else:
				return None
		return resp

	def authenticate( self ):
		self._pam.set_item( PAM.PAM_USER, self._username )
		ask = threads.Simple( 'pam', self._ask_pam, self._auth_result )
		ask.run()

	def _auth_result( self, thread, success ):
		self.signal_emit( 'auth_return', success )

	def _ask_pam( self ):
		try:
			AUTH.info( 'PAM: trying to authenticate %s' % self._username )
			self._pam.authenticate()
			self._pam.acct_mgmt()
		except PAM.error, e:
			AUTH.error( "PAM: authentication error: %s" % str( e ) )
			return False
		except Exception, e: # internal error
			AUTH.warn( "PAM: global error: %s" % str( e ) )
			return False

		AUTH.info( 'Authentication for %s was succcessful' % self._username )
		return True

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
			self._modules.append( instance )
		self._modules.reverse()

	def authenticate( self, username, password ):
		self._create_modules( username, password )
		self._current = self._modules.pop()
		self._current.authenticate()
		self.__credentials = ( username, password )

	def credentials( self ):
		return self.__credentials

	def _auth_return( self, success ):
		if not success:
			try:
				self._current = self._modules.pop()
				self._current.authenticate()
			except:
				self.signal_emit( 'authenticated', False )
		else:
			self._modules = []
			self.signal_emit( 'authenticated', True )
