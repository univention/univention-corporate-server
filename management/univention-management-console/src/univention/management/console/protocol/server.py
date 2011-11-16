#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  simple UMCP server implementation
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

# python packages
import datetime
import fcntl
import gzip
import os
import pwd
import re
import socket
import sys

# external packages
import notifier
import notifier.signals as signals
from OpenSSL import *

# internal packages
from .message import Message, Response, IncompleteMessageError, ParseError, UnknownCommandError, InvalidArgumentsError
from .session import State, Processor
from .definitions import *

from ..resources import moduleManager, syntaxManager, categoryManager
from ..log import CORE, CRYPT, RESOURCES
from ..config import ucr, SERVER_MAX_CONNECTIONS
from ..statistics import statistics

class MagicBucket( object ):
	'''Manages a connection (session) to the UMC server. Therefor it
	ensures that without successful authentication no other command is
	excepted. After the user has authenticated the commands a are passed
	on to the Processor.'''
	def __init__( self ):
		self.__states = {}

	def __del__( self ):
		self.exit()

	def new( self, client, socket ):
		'''Is called by the Server object to annouce a new incoming
		connetion.'''
		CORE.info( 'Established connection: %s' % client )
		state = State( client, socket )
		state.signal_connect( 'authenticated', self._authenticated )
		self.__states[ socket ] = state
		notifier.socket_add( socket , self._receive )
		statistics.connections.new()

	def exit( self ):
		'''Closes all open connections.'''
		# remove all sockets
		for sock, state in self.__states.items():
			CORE.info( 'Shutting down connection %s' % sock )
			if state.processor is not None:
				state.processor.shutdown()
			notifier.socket_remove( sock )
			statistics.connections.inactive()
		# delete states
		for state in self.__states.values():
			del state
		self.__states = {}

	def _authenticated( self, success, state ):
		'''Signal callback: Invoked when a authentication has been
		tried. This function generates the UMCP response.'''
		if success:
			statistics.users.add( state.username )
			state.authResponse.status = SUCCESS
		else:
			state.authResponse.status = BAD_REQUEST_AUTH_FAILED
		state.authenticated = success
		self._response( state.authResponse, state )
		state.authResponse = None

	def _receive( self, socket ):
		'''Handles incoming data. Processes SSL events and parses the
		incoming data. If a vaild UMCP was found it is passed to
		_handle.'''
		state = self.__states[ socket ]
		data = ''

		try:
			data = socket.recv( RECV_BUFFER_SIZE )
		except SSL.WantReadError:
			# this error can be ignored (SSL need to do something)
			return True
		except ( SSL.SysCallError, SSL.Error ), error:
			statistics.connections.inactive()
			if self.__states[ socket ].username in statistics.users:
				statistics.users.remove( self.__states[ socket ].username )
			CRYPT.warn( 'SSL error: %s. Probably the socket was closed by the client.' % str( error ) )
			if self.__states[ socket ].processor is not None:
				self.__states[ socket ].processor.shutdown()
			notifier.socket_remove( socket )
			del self.__states[ socket ]
			socket.close()
			return False

		if not len( data ):
			notifier.socket_remove( socket )
			del self.__states[ socket ]
			socket.close()
			return False

		state.buffer += data

		msg = None
		try:
			while state.buffer:
				msg = Message()
				state.buffer = msg.parse( state.buffer )
				self._handle( state, msg )
		except IncompleteMessageError, e:
			CORE.info( 'MagicBucket: incomplete message: %s' % str( e ) )
		except ParseError, e:
			CORE.process( 'Parser error: %s' % str( e ) )
			state.requests[ msg.id ] = msg
			res = Response( msg )
			res.status = UMCP_ERR_UNPARSABLE_BODY
			self._response( res, state )
		except UnknownCommandError, e:
			CORE.process( 'Unknown Command message: %s' % str( e ) )
			state.requests[ msg.id ] = msg
			res = Response( msg )
			res.status = BAD_REQUEST_NOT_FOUND
			self._response( res, state )
		except InvalidArgumentsError, e:
			CORE.process( 'Invalid arguments to UMCP command: %s' % str( e ) )
			state.requests[ msg.id ] = msg
			res = Response( msg )
			res.status = BAD_REQUEST_INVALID_ARGS
			self._response( res, state )

		return True

	CHANGELOG_VERSION = re.compile( '^[^(]*\(([^)]*)\).*' )
	def _handle( self, state, msg ):
		'''Ensures that commands are only passed to the processor if a
		successful authentication has been completed.'''
		state.requests[ msg.id ] = msg
		statistics.requests.new()
		CORE.info( 'Incoming request of type %s' % msg.command )
		if not state.authenticated and msg.command != 'AUTH':
			res = Response( msg )
			res.status = BAD_REQUEST_UNAUTH
			self._response( res, state )
		elif msg.command == 'AUTH':
			state.authResponse = Response( msg )
			state.authenticate( msg.body[ 'username' ],	msg.body[ 'password' ] )
		elif msg.command == 'GET' and ( 'ucr' in msg.arguments or 'info' in msg.arguments ):
			response = Response( msg )
			response.result = {}
			response.status = SUCCESS
			if 'ucr' in msg.arguments:
				for value in msg.options:
					if value[ -1 ] == '*':
						value = value[ : -1 ]
						for var in filter( lambda x: x.startswith( value ), ucr.keys() ):
							response.result[ var ] = ucr.get( var )
					else:
						response.result[ value ] = ucr.get( value )
			elif 'info' in msg.arguments:
				try:
					fd = gzip.open( '/usr/share/doc/univention-management-console-server/changelog.Debian.gz' )
					line = fd.readline()
					fd.close()
					match = MagicBucket.CHANGELOG_VERSION.match( line )
					if not match:
						raise IOError
					response.result[ 'umc_version' ] = match.groups()[ 0 ]
					response.result[ 'ucs_version' ] = '{0}-{1} errata{2} ({3})'.format( ucr.get( 'version/version', '' ), ucr.get( 'version/patchlevel', '' ), ucr.get( 'version/erratalevel', '0' ), ucr.get( 'version/releasename', '' ) )
					response.result[ 'server' ] = '{0}.{1}'.format( ucr.get( 'hostname', '' ), ucr.get( 'domainname', '' ) )
					import locale
					locale.setlocale( locale.LC_ALL, 'de_DE.UTF-8' )
					response.result[ 'ssl_validity_date' ] = datetime.datetime.fromtimestamp( int( ucr.get( 'ssl/validity/days', '0' ) ) * 24 * 60 * 60 ).strftime( "%x" )
				except IOError:
					response.status = BAD_REQUEST_FORBIDDEN
					pass

			self._response( response, state )
		elif msg.command == 'STATISTICS':
			response = Response( msg )
			try:
				pwent = pwd.getpwnam( state.username )
				if not pwent.pw_uid in ( 0, ):
					raise KeyError
				CORE.info( 'Sending statistic data to client' )
				response.status = SUCCESS
				response.result = statistics.json()
			except KeyError:
				CORE.info( 'User not allowed to retrieve statistics' )
				response.status = BAD_REQUEST_FORBIDDEN
			self._response( response, state )
		else:
			# inform processor
			if not state.processor:
				state.processor = Processor( *state.credentials() )
				cb = notifier.Callback( self._response, state )
				state.processor.signal_connect( 'response', cb )
			state.processor.request( msg )

	def _do_send( self, socket ):
		state = self.__states[ socket ]
		id, first = state.resend_queue.pop( 0 )
		try:
			ret = socket.send( first )
			if ret < len( first ):
				state.resend_queue.insert( 0, ( id, first[ ret : ] ) )
			else:
				if id != -1:
					del state.requests[ id ]
		except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
			CRYPT.info( 'UMCP: SSL error during re-send' )
			state.resend_queue.insert( 0, ( id, first ) )
			return True
		except ( SSL.SysCallError, SSL.Error ), error:
			statistics.connections.inactive()
			if self.__states[ socket ].username in statistics.users:
				statistics.users.remove( self.__states[ socket ].username )
			CRYPT.warn( 'SSL error: %s. Probably the socket was closed by the client.' % str( error ) )
			if self.__states[ socket ].processor is not None:
				self.__states[ socket ].processor.shutdown()
			notifier.socket_remove( socket )
			del self.__states[ socket ]
			socket.close()
			return False

		return ( len( state.resend_queue ) > 0 )

	def _response( self, msg, state ):
		''' Send UMCP response to client. If the status code is 250 the
		module process is asking for exit. This method forfills the
		request.'''
		# FIXME: error handling is missing!!
		if not msg.id in state.requests and msg.id != -1:
			CORE.process( 'The given response is invalid or not known' )
			return

		try:
			statistics.requests.inactive()
			data = str( msg )
			# there is not data from another request in the send queue
			if not state.resend_queue:
				ret = state.socket.send( data )
			else:
				ret = 0
			# not all data could be send; retry later
			if ret < len( data ):
				if not state.resend_queue:
					notifier.socket_add( state.socket, self._do_send, notifier.IO_WRITE )
				state.resend_queue.append( ( msg.id, data[ ret : ] ) )
		except ( SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError ):
			CRYPT.info( 'UMCP: SSL error need to re-send chunk' )
			notifier.socket_add( state.socket, self._do_send, notifier.IO_WRITE )
			state.resend_queue.append( data )
		except ( SSL.SysCallError, SSL.Error ), error:
			statistics.connections.inactive()
			# clean up if not already done
			if state.socket in self.__states:
				if state.username in statistics.users:
					statistics.users.remove( state.username )
					CRYPT.warn( 'SSL error: %s. Probably the socket was closed by the client.' % str( error ) )
					if state.processor is not None:
						state.processor.shutdown()
					notifier.socket_remove( state.socket )
					del self.__states[ state.socket ]
					socket.close()
			return

		# module process wants to exit
		if msg.status == 250:
			module_name = state.processor.get_module_name( msg.arguments[ 0 ] )
			if module_name:
				state.processor._purge_child( module_name )

class Server( signals.Provider ):
	'''Handles incoming connections on UNIX or TCP sockets and passes
	the control to the MagicBucket'''

	def __init__( self, port = 6670, ssl = True, unix = None, magic = True, magicClass = MagicBucket, load_ressources = True ):
		'''Initializes the socket to listen for requests'''
		signals.Provider.__init__( self )

		# loading resources
		if load_ressources:
			CORE.info( 'Loading resources ...' )
			self.reload()

		# register timer to update UCR variables
		try:
			ucr_reload_timer = int( ucr.get( 'umc/server/ucr/update', 600 ) )
		except ValueError:
			CORE.warn( 'Failed to read interval for UCR reloads. Using default of 600 seconds' )
			ucr_reload_timer = 600
		notifier.timer_add( ucr_reload_timer * 1000, lambda: ucr.load() or True )

		CORE.info( 'Initialising server process' )
		self.__port = port
		self.__unix = unix
		self.__ssl = ssl
		if self.__unix:
			CORE.info( 'Using a UNIX socket' )
			self.__realsocket = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
		else:
			CORE.info( 'Using a TCP socket' )
			self.__realsocket = socket.socket( socket.AF_INET6, socket.SOCK_STREAM )

		self.__realsocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		self.__realsocket.setblocking( 0 )
		fcntl.fcntl(self.__realsocket.fileno(), fcntl.F_SETFD, 1)

		if self.__ssl and not self.__unix:
			CORE.info( 'Setting up SSL configuration' )
			self.crypto_context = SSL.Context( SSL.SSLv23_METHOD )
			self.crypto_context.set_cipher_list('DEFAULT')
			self.crypto_context.set_options( SSL.OP_NO_SSLv2 )
			self.crypto_context.set_verify( SSL.VERIFY_PEER, self.__verify_cert_cb )
			dir = '/etc/univention/ssl/%s.%s' % ( ucr[ 'hostname' ], ucr[ 'domainname' ] )
			try:
				self.crypto_context.use_privatekey_file( os.path.join( dir, 'private.key' ) )
				self.crypto_context.use_certificate_file( os.path.join( dir, 'cert.pem' ) )
				self.crypto_context.load_verify_locations( os.path.join( dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem' ) )
			except SSL.Error, e:
				# SSL is not possible
				CRYPT.process( 'Setting up SSL configuration failed: %s' % str( e ) )
				CRYPT.warn( 'Communication will not be encrypted!' )
				self.__ssl = False
				self.crypto_context = None
				self.__realsocket.bind( ( '', self.__port ) )
				CRYPT.info( 'Server listening to unencrypted connections' )
				self.__realsocket.listen( SERVER_MAX_CONNECTIONS )

			if self.crypto_context:
				self.connection = SSL.Connection( self.crypto_context , self.__realsocket )
				self.connection.setblocking(0)
				self.connection.bind( ( '', self.__port ) )
				self.connection.set_accept_state()
				CRYPT.info( 'Server listening to SSL connections' )
				self.connection.listen( SERVER_MAX_CONNECTIONS )
		else:
			self.crypto_context = None
			if self.__unix:
				try:
					# ensure that the UNIX socket is only accessable by root
					old_umask = os.umask( 0077 )
					self.__realsocket.bind( self.__unix )
					# restore old umask
					os.umask( old_umask )
				except:
					os.unlink( self.__unix )
			else:
				self.__realsocket.bind( ( '', self.__port ) )
			CRYPT.info(  'Server listening to connections' )
			self.__realsocket.listen( SERVER_MAX_CONNECTIONS )

		self.__magic = magic
		self.__magicClass = magicClass
		self.__bucket = None
		if self.__magic:
			self.__bucket = self.__magicClass()
		else:
			self.signal_new( 'session_new' )

		if self.__ssl and not self.__unix:
			notifier.socket_add( self.connection, self._connection )
		else:
			notifier.socket_add( self.__realsocket, self._connection )

	def __del__( self ):
		if self.__bucket:
			del self.__bucket

	def __verify_cert_cb( self, conn, cert, errnum, depth, ok ):
		CORE.info( '__verify_cert_cb: Got certificate: %s' % cert.get_subject() )
		CORE.info( '__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer() )
		CORE.info( '__verify_cert_cb: errnum=%d  depth=%d	 ok=%d' % (errnum, depth, ok) )
		return ok

	def _connection( self, socket ):
		'''Signal callback: Invoked on incoming connections.'''
		socket, addr = socket.accept()
		socket.setblocking( 0 )
		if addr:
			client = '%s:%d' % ( addr[ 0 ], addr[ 1 ] )
		else:
			client = ''
		CORE.info( 'Incoming connection from %s' % client )
		if self.__magic:
			self.__bucket.new( client, socket )
		else:
			self.signal_emit( 'session_new', client, socket )
		return True

	def exit( self ):
		'''Shutdowns all open connections.'''
		CORE.warn( 'Shutting down all open connections' )
		if self.__ssl and not self.__unix:
			notifier.socket_remove( self.connection )
			self.connection.close()
		else:
			notifier.socket_remove( self.__realsocket )
			self.__realsocket.close()
		if self.__unix:
			os.unlink( self.__unix )

		if self.__magic:
			self.__bucket.exit()

	def reload( self ):
		CORE.info( 'Reloading resources: modules, syntax definitions, categories' )
		moduleManager.load()
		syntaxManager.load()
		categoryManager.load()
		RESOURCES.info( 'Reloading UCR variables' )
		ucr.load()
