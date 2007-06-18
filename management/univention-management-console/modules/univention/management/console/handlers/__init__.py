# -*- coding: utf-8 -*-
#
# Univention Management Console
#  sub-module: UMCP modules
#
# Copyright (C) 2006, 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import notifier

import notifier.signals as signals

import univention.management.console as umc
import univention.management.console.protocol as umcp
import univention.management.console.dialog as umcd

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers' ).translate

# UMC module command
class command( object ):
	'''Describes a command of UMC daemon module'''
	def __init__( self, short_description, long_description = '', method = None, values = {},
				  startup = False, caching = False, priority = 0 ):
		self.short_description = short_description
		self.long_description = long_description
		self.method = method
		self.values = values
		self.startup = startup
		self.caching = caching
		self.priority = priority

	def __getitem__( self, option ):
		if self.values.has_key( option ):
			return ( option, self.values[ option ] )
		return ( None, None )

class simpleHandler( signals.Provider ):
	'''This is the base class for UMC daemon modules'''
	def __init__( self, commands ):
		signals.Provider.__init__( self )
		self.signal_new( 'success' )
		self.signal_new( 'partial' )
		self.signal_new( 'failure' )
		self.__commands = commands
		self.__requests = {}
		self.__timer = {}
		self.__message = _( 'The Operation is still in progress' )
		self.__acls = None
		self.__interface = None
		self._username = None
		self._password = None

	def __getitem__( self, command ):
		'''returns a tuple of a valid command argument name and its
		syntax description. If not found None is returned'''
		if self.__commands.has_key( command ):
			return self.__commands[ command ]
		return None

	def set_interface( self, ui ):
		self.__interface = ui

	def set_username( self, username ):
		self._username = username

	def set_password( self, pwd ):
		self._password = pwd

	def _exec_if( self, prefix, method, args ):
		symbol = '%s_%s' % ( prefix, method )

		func = getattr( self, symbol, None )

		if not func:
			return None

		try:
			if isinstance( args, tuple ):
				func( *args )
			else:
				func( args )
		except Exception, e:
			import traceback
			ud.debug( ud.ADMIN, ud.INFO, "EXCEPTION: %s" % traceback.format_exc() )
			return traceback.format_exc()

		return True

	def _start_response_timer( self, id, message ):
		cb = notifier.Callback( self._partial_response, id, message )
		self.__timer[ id ] = notifier.timer_add( 1500, cb )

	def _stop_response_timer( self, id ):
		if self.__timer.has_key( id ):
			notifier.timer_remove( id )
			del self.__timer[ id ]

	def _partial_response( self, id, message ):
		lst = umcd.List()
		lst.setHeader( [ umcd.Text( _( 'Information' ) ) ] )
		lst.appendRow( [ umcd.Text( message ) ] )
		self.message( id, umcd.Dialog( [ lst ] ) )
		self._stop_response_timer( id )

		return False

	def execute( self, method, object ):
# 		self._start_response_timer( object.id(), self.__message )
		self.__requests[ object.id() ] = ( object, method )
		ret = self._exec_if( '_pre', method, object )
		if isinstance( ret, basestring ):
			self.__execution_failed( object, ret )
			return

		try:
			func = getattr( self, method )
			func( object )
		except Exception, e:
			import traceback

			res = umcp.Response( object )
			res.dialog = None
			res.report = _( "Execution of command '%(command)s' has failed:\n\n%(text)s" ) % \
							{ 'command' : object.arguments[ 0 ],
							  'text' : unicode( traceback.format_exc() ) }
			res.status( 500 )
			self.signal_emit( 'failure', res )
			del self.__requests[ object.id() ]

	def __partial( self, id, dialog, type ):
		if self.__requests.has_key( id ):
			self._stop_response_timer( id )
			object, method = self.__requests[ id ]
			res = umcp.Response( object )
			res.dialog = dialog
			res.module = [ 'active', type ]
			res.status( 210 )
			self.signal_emit( 'partial', res )

	def set_acls( self, acls ):
		self.__acls = acls

	def permitted( self, command, options ):
		if not self.__acls:
			return False
		return self.__acls.is_command_allowed( command, options = options )

	def message( self, id, dialog ):
		self.__partial( id, dialog, 'message' )

	def warning( self, id, dialog ):
		self.__partial( id, dialog, 'warning' )

	def __verify_dialog( self, dialog ):
		if isinstance( dialog, umcd.DialogTypes ):
			return dialog
		else:
			if isinstance( dialog, ( tuple, list ) ) and \
				   not isinstance( dialog, umcd.ListTypes ):
				return umcd.Dialog( dialog )
			else:
				return umcd.Dialog( [ dialog ] )

	def __execution_failed( self, object, text ):
		res = umcp.Response( object )
		res.dialog = None
		res.report = _( "Execution of command '%(command)s' has failed:\n\n%(text)s" ) % \
						{ 'command' : object.arguments[ 0 ], 'text' : unicode( text ) }
		res.status( 500 )
		self.signal_emit( 'failure', res )
		del self.__requests[ object.id() ]

	def finished( self, id, dialog, report = None, success = True ):
		"""this method should be invoked by module to finish the
		processing of a request. 'id' is the request command identifier,
		'dialog' should contain the result as UMC dialog and 'success'
		defines if the request could be fulfilled or not. If there is a
		definition of a '_post' processing function it is called
		immediately. After that a 'revamp' function is invoked if it
		exists. In that cause the result is passed to this function and
		not returned to the client, otherwise the result is encapsulated
		in a dialog and send to the client."""
		if self.__requests.has_key( id ):
			object, method = self.__requests[ id ]
			res = umcp.Response( object )

			ret = self._exec_if( '_post', method, object )
			if isinstance( ret, basestring ):
				self.__execution_failed( object, ret )
				return
			res.dialog = dialog
			if report:
				res.report = report
			if success:
				res.status( 200 )
			else:
				res.status( 600 )

			ret =  self._exec_if( '_%s' % self.__interface, method, ( object, res ) )
			if ret == None:
				res.dialog = self.__verify_dialog( dialog )
				self.result( res )
			elif isinstance( ret, basestring ):
				self.__execution_failed( object, ret )
				return



	def revamped( self, id, res ):
		"""this method should in invoked by '_revamp' functions that are
		called after a command was successfully processed. It should be
		used to modify the result dialog to fit the specified client
		interface"""
		if self.__requests.has_key( id ):
			res.dialog = self.__verify_dialog( res.dialog )
			self.result( res )

	def result( self, response ):
		if self.__requests.has_key( response.id() ):
			self._stop_response_timer( response.id() )
			object, method = self.__requests[ response.id() ]
			if response.status() in ( 200, 210 ):
				response.module = [ 'ready' ]
				self.signal_emit( 'success', response )
			else:
				response.module = [ 'failure' ]
				self.signal_emit( 'failure', response )
			del self.__requests[ response.id() ]
