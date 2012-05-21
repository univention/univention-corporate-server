#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
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

from .server import *
from .message import *
from .definitions import *

from ..acl import ACLs
from ..module import Module
from ..log import MODULE

from univention.lib.i18n import Locale, NullTranslation

_ = NullTranslation( 'univention.management.console' ).translate

import locale
import notifier
import notifier.threads as threads

class ModuleServer( Server ):
	def __init__( self, socket, module, timeout = 300, check_acls = True ):
		self.__name = module
		self.__module = module
		self.__commands = Module()
		self.__comm = None
		self.__client = None
		self.__buffer = ''
		self.__acls = None
		self.__timeout = timeout * 1000
		self.__timer = notifier.timer_add( self.__timeout, self._timed_out )
		self.__active_requests = 0
		self.__check_acls = check_acls
		self.__queue = ''
		self.__username = None
		self.__user_dn = None
		self.__password = None
		self._load_module()
		Server.__init__( self, ssl = False, unix = socket, magic = False, load_ressources = False )
		self.signal_connect( 'session_new', self._client )

	def _load_module( self ):
		try:
			modname = self.__module
			self.__module = None
			for type in ( 'modules', 'wizards' ):
				try:
					file = 'univention.management.console.%s.%s' % ( type, modname )
					self.__module = __import__( file, [], [], modname )
					break
				except BaseException, e:
					MODULE.error( 'Failed to import module %s: %s' % ( modname, str( e ) ) )
					import traceback
					traceback.print_exc()
			if not self.__module:
				raise Exception( "Module '%s' could not be found. Exiting ..." % modname )
			self.__handler = self.__module.Instance()
			self.__handler.signal_connect( 'success', notifier.Callback( self._reply, True ) )
			self.__handler.signal_connect( 'failure', notifier.Callback( self._reply, True ) )
		except Exception, e:
			import traceback
			traceback.print_exc()
			sys.exit( 5 )

	def _reply( self, msg, final ):
		if final:
			self.__active_requests -= 1
		self.response( msg )
		if not self.__active_requests and self.__timer == None:
			self.__timer = notifier.timer_add( self.__timeout, self._timed_out )

	def _timed_out( self ):
		MODULE.info( "Commiting suicide" )
		self.__handler.destroy()
		self.exit()
		sys.exit( 0 )

	def _client( self, client, socket ):
		self.__comm = socket
		self.__client = client
		notifier.socket_add( self.__comm, self._recv )

	def _recv( self, socket ):
		if self.__timer:
			notifier.timer_remove( self.__timer )
			self.__timer == None

		data = socket.recv( RECV_BUFFER_SIZE )

		# connection closed?
		if not len( data ):
			socket.close()
			# remove socket from notifier
			return False

		self.__buffer += data

		msg = None
		try:
			while self.__buffer:
				msg = Message()
				self.__buffer = msg.parse( self.__buffer )
				MODULE.info( "Received request %s" % msg.id )
				self.handle( msg )
		except IncompleteMessageError, e:
			MODULE.info( 'Failed to parse incomplete message' )
		except ( ParseError, UnknownCommandError ), e:
			MODULE.error( 'Failed to parse message: %s' % str( e ) )
			res = Response( msg )
			res.id = -1
			res.status = e.args[ 0 ]
			self.response( res )

		return True

	def handle( self, msg ):
		PROTOCOL.info( 'Received UMCP %s REQUEST %s' % ( msg.command, msg.id ) )
		if msg.command == 'EXIT':
			shutdown_timeout = 100
			MODULE.info( "EXIT: module shutdown in %dms" % shutdown_timeout )
			# shutdown module after one second
			resp = Response( msg )
			resp.body = { 'status': 'module %s will shutdown in %dms' % (str(msg.arguments[0]), shutdown_timeout) }
			resp.status = SUCCESS
			self.response( resp )
			self.__timer = notifier.timer_add( shutdown_timeout, self._timed_out )
			return

		if msg.command == 'SET':
			resp = Response( msg )
			resp.status = SUCCESS
			for key, value in msg.options.items():
				if key == 'acls':
					self.__acls = ACLs( acls = value )
					self.__handler.acls = self.__acls
				elif key == 'commands':
					self.__commands.fromJSON( value[ 'commands' ] )
				elif key == 'username':
					self.__username = value
					self.__handler.username = self.__username
				elif key == 'credentials':
					self.__username = value[ 'username' ]
					self.__user_dn = value[ 'user_dn' ]
					self.__password = value[ 'password' ]
					self.__handler.username = self.__username
					self.__handler.user_dn = self.__user_dn
					self.__handler.password = self.__password
				elif key == 'locale' and value is not None:
					self.__locale = value
					try:
						locale_obj = Locale( value )
						locale.setlocale( locale.LC_MESSAGES, str( locale_obj ) )
						MODULE.info( "Setting specified locale (%s)" % str( locale_obj ) )
					except locale.Error:
						MODULE.warn( "Specified locale is not available (%s)" % str( locale_obj ) )
						MODULE.warn( "Falling back to C" )
						# specified locale is not available -> falling back to C
						locale.setlocale( locale.LC_MESSAGES, 'C' )
						self.__locale = 'C'
					self.__handler.set_language( self.__locale )
				else:
					resp.status = BAD_REQUEST_INVALID_OPTS
					break

			# if SET command contains 'acls', commands' and
			# 'credentials' it is the initialization of the module
			# process
			if 'acls' in msg.options and 'commands' in msg.options and 'credentials' in msg.options:
				try:
					self.__handler.init()
				except BaseException, e:
					import traceback, sys
					resp.status = MODULE_ERR
					exc_info = sys.exc_info()
					resp.message = _( 'The init function of the module has failed: %s: %s\n%s' ) % ( exc_info[ 0 ].__name__, exc_info[ 1 ], '\n'.join( traceback.format_tb( exc_info[ 2 ] ) ) )
			self.response( resp )

			if not self.__active_requests and self.__timer == None:
				self.__timer = notifier.timer_add( self.__timeout, self._timed_out )
			return

		if msg.arguments:
			cmd = msg.arguments[ 0 ]
			cmd_obj = self.command_get( cmd )
			if cmd_obj and ( not self.__check_acls or self.__acls.is_command_allowed( cmd, options = msg.options, flavor = msg.flavor ) ):
				self.__active_requests += 1
				self.__handler.execute( cmd_obj.method, msg )
				if not self.__active_requests and self.__timer == None:
					self.__timer = notifier.timer_add( self.__timeout, self._timed_out )
				return
			else:
				resp = Response( msg )
				# status 415 (command not allowed) should be checked by the server
				resp.status = BAD_REQUEST_NOT_FOUND
				resp.message = status_description( resp.status )
				self.response( resp )

		if not self.__active_requests and self.__timer == None:
			self.__timer = notifier.timer_add( self.__timeout, self._timed_out )

	def command_get( self, command_name ):
		for cmd in self.__commands.commands:
			if cmd.name == command_name:
				return cmd
		return None

	def command_is_known( self, command_name ):
		for cmd in self.__commands.commands:
			if cmd.name == command_name:
				return True
		return False

	def _do_send( self, sock ):
		if len(self.__queue) > 0:
			length = len( self.__queue )
			try:
				ret = self.__comm.send( self.__queue )
			except socket.error, e:
				if e[0] == 11:
					return True
				raise

			if ret < length:
				self.__queue = self.__queue[ ret : ]
				return True
			else:
				self.__queue = ''
				return False
		else:
			return False

	def response( self, msg ):
		PROTOCOL.info( 'Sending UMCP RESPONSE %s' % msg.id )
		data = str( msg )
		self.__queue += str(msg)

		if self._do_send( self.__comm ):
			notifier.socket_add( self.__comm, self._do_send, notifier.IO_WRITE )
