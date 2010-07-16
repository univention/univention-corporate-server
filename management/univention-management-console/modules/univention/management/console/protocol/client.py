# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP client implementation
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

import errno, os, socket, sys, fcntl

from message import *
from definitions import *
from OpenSSL import *

import notifier
import notifier.signals as signals
import univention.debug as ud

import univention.management.console as umc

class UnknownRequestError( Exception ):
	pass

class NotAuthenticatedError( Exception ):
	pass


'''
General client class for connecting to a UMC server.
Provides basic functionality for session-handling, authentication and
request handling.
'''

class Client( signals.Provider ):
	def __verify_cert_cb( self, conn, cert, errnum, depth, ok ):
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: Got certificate subject: %s' % cert.get_subject() )
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer() )
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: errnum=%d  depth=%d  ok=%d' % (errnum, depth, ok) )
		if depth == 0 and ok == 0:
			self.signal_emit( 'authenticated', False, 504, status_information( 504 ) )
		return ok

	def __init__( self, servername = 'localhost', port = 6670, unix = None,
				  ssl = True, auth = True ):
		'''Initialize a socket-connection to the server.'''
		signals.Provider.__init__( self )
		self.__authenticated = ( not auth )
		self.__auth_id = None
		self.__ssl = ssl
		self.__unix = unix
		if self.__ssl and not self.__unix:
			self.__crypto_context = SSL.Context(SSL.SSLv23_METHOD)
			self.__crypto_context.set_cipher_list('DEFAULT')
			self.__crypto_context.set_verify( SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.__verify_cert_cb )
			try:
				self.__crypto_context.load_verify_locations( os.path.join( dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem' ) )
			except SSL.Error, e:
				# SSL is not possible
				ud.debug( ud.ADMIN, ud.ERROR, 'Client: Setting up SSL configuration failed: %s' % str( e ) )
				ud.debug( ud.ADMIN, ud.ERROR, 'Client: Communication will not be encrypted!' )
				self.__crypto_context = None
				self.__ssl = False
		self.__port = port
		self.__server = servername
		self.__resend_queue = {}

		self.__realsocket = self.__socket = None
		self._init_socket()

		self.__buffer = ''
		self.__unfinishedRequests = []
		self.signal_new( 'response' )
		self.signal_new( 'authenticated' )
		self.signal_new( 'error' )
		self.signal_new( 'closed' )

	def __nonzero__( self ):
		if self.__ssl and not self.__crypto_context:
			return False
		return True

	def _init_socket( self ):
		if self.__unix:
			self.__realsocket = socket.socket( socket.AF_UNIX,
											   socket.SOCK_STREAM )
		else:
			self.__realsocket = socket.socket( socket.AF_INET,
											   socket.SOCK_STREAM )
		self.__realsocket.setsockopt( socket.SOL_SOCKET,
									  socket.SO_REUSEADDR, 1 )
		fcntl.fcntl(self.__realsocket.fileno(), fcntl.F_SETFD, 1)

		if self.__ssl and not self.__unix:
			self.__socket = SSL.Connection( self.__crypto_context, self.__realsocket )
		else:
			self.__socket = None

	def disconnect( self, force = True ):
		if not force and self.__unfinishedRequests:
			return False
		if self.__ssl and not self.__unix:
			self.__socket.close()
		self.__realsocket.close()
		self.__socket = None
		self.__realsocket = None
		self.signal_emit( 'closed' )
		return True

	def connect( self ):
		if not self.__realsocket and not self.__socket:
			self._init_socket()
		try:
			if self.__ssl and not self.__unix:
				self.__socket.connect( ( self.__server, self.__port ) )
				self.__socket.setblocking( 0 )
				try:
					self.__socket.set_connect_state()
					notifier.socket_add( self.__socket, self._recv )
					ud.debug( ud.ADMIN, ud.INFO, 'Client.connect: SSL connection established' )
				except SSL.Error, e:
					ud.debug( ud.ADMIN, ud.ERROR, 'Client: Setting up SSL configuration failed: %s' % str( e ) )
					ud.debug( ud.ADMIN, ud.ERROR, 'Client: Communication will not be encrypted!' )
					self.__realsocket.shutdown( socket.SHUT_RDWR )
					self.__ssl = False
					self._init_socket()
 					self.__realsocket.connect( ( self.__server, self.__port ) )
					self.__realsocket.setblocking( 0 )
					notifier.socket_add( self.__realsocket, self._recv )
					ud.debug( ud.ADMIN, ud.INFO, 'Client.connect: connection established' )
			else:
				if self.__unix:
					self.__realsocket.connect( self.__unix )
				else:
					self.__realsocket.connect( ( self.__server, self.__port ) )
				self.__realsocket.setblocking( 0 )
				notifier.socket_add( self.__realsocket, self._recv )
			return True
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, 'Client.connect: failed: %s' % str( e ) )
			return False

	def _resend( self, sock ):
		if self.__resend_queue.has_key(sock):
			while len(self.__resend_queue[sock]) > 0:
				data = str(self.__resend_queue[sock][0])
				try:
					bytessent = sock.send( data )
					if bytessent < len(data):
						# only sent part of message
						self.__resend_queue[sock][0] = data[ bytessent : ]
						return True
					else:
						del self.__resend_queue[sock][0]
				except socket.error, e:
					if e[0] in [104, 107, 9]:
						# Error may happen if module process died and server tries to send request at the same time
						# 104: connection reset by peer
						# 107: socket not connected
						# 9: bad file descriptor
						ud.debug( ud.ADMIN, ud.INFO, 'Client: _resend: socket is damaged: %s' % str( e ) )
						self.signal_emit( 'closed' )
						return False
					if e[0] != 11:
						raise
					return True
				except ( SSL.WantReadError, SSL.WantWriteError,
						 SSL.WantX509LookupError ), e:
					return True
				except SSL.Error, e:
					ud.debug( ud.ADMIN, ud.ERROR,
							  'Client: Setting up SSL configuration failed: %s' % str( e ) )
					ud.debug( ud.ADMIN, ud.ERROR, 'Client: Communication will not be encrypted!' )
					save = self.__resend_queue[ self.__socket ]
					del self.__resend_queue[ self.__socket ]
					self.__realsocket.shutdown( socket.SHUT_RDWR )
					self.__ssl = False
					self._init_socket()
					self.__realsocket.connect( ( self.__server, self.__port ) )
					self.__realsocket.setblocking( 0 )
					self.__resend_queue[ self.__realsocket ] = save
					notifier.socket_add( self.__realsocket, self._recv )
					notifier.socket_add( self.__realsocket, self._resend, notifier.IO_WRITE )
					return False
			if len(self.__resend_queue[sock]) == 0:
				del self.__resend_queue[sock]
		return False

	def request( self, msg ):
		if not self.__authenticated and msg.command != 'AUTH':
			raise NotAuthenticatedError()

		if self.__ssl and not self.__unix:
			sock = self.__socket
		else:
			sock = self.__realsocket

		data = str(msg)

		if self.__resend_queue.has_key( sock ):
			self.__resend_queue[ sock ].append( data )
		else:
			self.__resend_queue[ sock ] = [ data ]

		if self._resend( sock ):
			notifier.socket_add( sock, self._resend, notifier.IO_WRITE )

		self.__unfinishedRequests.append( msg.id() )

	def invalidate_all_requests(self):
		for reqid in self.__unfinishedRequests:
			response = Response()
			response._id = reqid
			response._command = 'COMMAND'
			response.status( 502 ) # module process died unexpectedly
			ud.debug( ud.ADMIN, ud.WARN, 'invalidate_all_requests: request %s' % ( str(reqid) ) )
			self.signal_emit( 'response', response )

	def _recv( self, sock ):
		try:
			recv = ''
			while True:
				recv += sock.recv( 16384 )
				if self.__ssl and not self.__unix:
					if not sock.pending():
						break
				else:
					break
		except socket.error, e:
			ud.debug( ud.ADMIN, ud.WARN, 'Client: _recv: error on socket: %s' % str( e ) )
			recv = None
		except SSL.SysCallError, e:
			# lost connection or any other unfixable error
			recv = None
		except SSL.Error:
			error = sock.getsockopt( socket.SOL_SOCKET, socket.SO_ERROR )
			# lost connection: UMC daemon died probably
			if error == errno.EPIPE:
				recv = None
			else:
				return True

		if not recv:
			self.signal_emit( 'closed' )
			try:
				sock.close()
			except:
				pass
			notifier.socket_remove( sock )
			return False

		response = Response()
		if self.__buffer:
			recv = self.__buffer + recv
			self.__buffer = ''
		try:
			while recv:
				recv = response.parse( recv )
				self._handle( response )
		except IncompleteMessageError:
			self.__buffer = recv
			# waiting for the rest
		except ( ParseError, UnknownCommandError ), e:
			self.signal_emit( 'error', e )

		return True

	def _handle( self, response ):
		if response.command == 'AUTH' and response.id() == self.__auth_id:
			if response.status() == 200:
				self.__authenticated = True
				self.__unfinishedRequests.remove( response.id() )
			self.signal_emit( 'authenticated', self.__authenticated,
							  response.status(),
							  status_information( response.status() ) )
		elif response.id() in self.__unfinishedRequests:
			self.signal_emit( 'response', response )
			if response.isFinal():
				self.__unfinishedRequests.remove( response.id() )
		else:
			self.signal_emit( 'error', UnknownRequestError() )

	def authenticate( self, username, password ):
		'''
		Authenticate against a running server on the local connection.
		'''
		authRequest = Request ('AUTH' )
		authRequest.body['username'] = username
		authRequest.body['password'] = password

		self.request( authRequest )

		self.__auth_id = authRequest.id()

if __name__ == '__main__':
	import notifier
	from getpass import getpass

	notifier.init( notifier.GENERIC )

	def auth( success, status, text ):
		print 'authentication', success, status, text

	client = Client()
	client.signal_connect( 'authenticated', auth )
	if client.connect():
		print 'connected successfully'
	else:
		print 'ERROR connecting to daemon'
	username = raw_input( 'Username: ' )
	password = getpass()
	client.authenticate( username, password )

	notifier.loop()
