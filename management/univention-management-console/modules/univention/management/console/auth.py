#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2006-2010 Univention GmbH
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

import notifier.signals as signals
import notifier.threads as threads

import PAM

__all__ = [ 'AuthHandler' ]

import locales

import univention.debug as ud

_ = locales.Translation( 'univention.management.console' ).translate

class Auth( signals.Provider ):
	def __init__( self, username, password ):
		signals.Provider.__init__( self )
		self._username = username
		self._password = password

		self.signal_new( 'auth_return' )

	def credenticals( self, username = None, password = None ):
		if username:
			self._username = username
		if password:
			self._password = password

	def authenticate( self ):
		return True

class PAM_Auth( Auth ):
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
			self._pam.authenticate()
			self._pam.acct_mgmt()
		except PAM.error, e:
			ud.debug( ud.ADMIN, ud.ERROR, "PAM: authentication error: %s" % str( e ) )
			return False
		except Exception, e: # internal error
			ud.debug( ud.ADMIN, ud.WARN, "PAM: global error: %s" % str( e ) )
			return False

		return True

class Baseconfig_Auth( Auth ):
	def __init__( self, username = None, password = None ):
		Auth.__init__( self, username, password )

	def authenticate( self ):
		self.signal_emit( 'auth_return', True )

# FIXME: Baseconfig authentication is currently not implemented
#_all_modules = ( PAM_Auth, Baseconfig_Auth )
# _all_modules = ( Baseconfig_Auth, )
_all_modules = ( PAM_Auth, )

class AuthHandler( signals.Provider ):
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
