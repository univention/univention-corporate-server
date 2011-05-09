#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Base class for UMC 2.0 modules
#
# Copyright 2006-2011 Univention GmbH
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

import univention.debug as ud

import univention.management.console.protocol as umcp
import univention.management.console.locales as umcl

_ = umcl.Translation( 'univention.management.console' ).translate

class Base( signals.Provider ):
	'''The base class for UMC modules of version 2 or higher'''
	def __init__( self ):
		signals.Provider.__init__( self )
		self.signal_new( 'success' )
		self.signal_new( 'partial' )
		self.signal_new( 'failure' )
		self._username = None
		self._password = None
		self._sessionid = None
		self.__acls = None
		self.__requests = {}

	def _set_username( self, username ):
		self._username = username
	username = property( fset = _set_username )

	def _set_password( self, password ):
		self._password = password
	password = property( fset = _set_password )

	def _set_sessionid( self, sessionid ):
		self._sessionid = sessionid
	sessionid = property( fset = _set_sessionid )

	def _set_acls( self, acls ):
		self.__acls = acls
	acls = property( fset = _set_acls )

	def execute( self, method, object ):
		self.__requests[ object.id() ] = ( object, method )

		ud.debug( ud.ADMIN, ud.INFO, 'Execute: %s' % str( object.arguments ) )
		try:
			func = getattr( self, method )
			func( object )
		except Exception, e:
			print 'EXECUTE', str( e )
			import traceback

			res = umcp.Response( object )
			res.message = _( "Execution of command '%(command)s' has failed:\n\n%(text)s" ) % \
							{ 'command' : object.arguments[ 0 ],
							  'text' : unicode( traceback.format_exc() ) }
			ud.debug( ud.ADMIN, ud.ERROR, res.message )
			res.status = 500
			self.signal_emit( 'failure', res )
			if object.id() in self.__requests:
				del self.__requests[ object.id() ]

	def permitted( self, command, options ):
		if not self.__acls:
			return False
		return self.__acls.is_command_allowed( command, options = options )

	def __execution_failed( self, object, text ):
		res = umcp.Response( object )
		res.dialog = None
		res.message = _( "Execution of command '%(command)s' has failed:\n\n%(text)s" ) % \
						{ 'command' : object.arguments[ 0 ], 'text' : unicode( text ) }
		res.status = 500
		self.signal_emit( 'failure', res )
		del self.__requests[ object.id() ]

	def finished( self, id, response, message = None, success = True ):
		"""this method should be invoked by module to finish the
		processing of a request. 'id' is the request command identifier,
		'dialog' should contain the result as UMC dialog and 'success'
		defines if the request could be fulfilled or not. If there is a
		definition of a '_post' processing function it is called
		immediately. After that a 'revamp' function is invoked if it
		exists. In that cause the result is passed to this function and
		not returned to the client, otherwise the result is encapsulated
		in a dialog and send to the client."""
		if not id in self.__requests:
			return
		object, method = self.__requests[ id ]

		# FIXME: where to put the answer in this response
		if not isinstance( response, umcp.Response ):
			res = umcp.Response( object )
			res.result = response
			res.message = message

		if not res.status:
			if success:
				res.status = 200
			else:
				res.status = 600

		self.result( res )

	def result( self, response ):
		if response.id() in self.__requests:
			object, method = self.__requests[ response.id() ]
			if response.status in ( 200, 210 ):
				response.module = [ 'ready' ]
				self.signal_emit( 'success', response )
			else:
				response.module = [ 'failure' ]
				self.signal_emit( 'failure', response )
			del self.__requests[ response.id() ]


