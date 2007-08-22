#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  simple UMCP server implementation
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

# python packages
import socket, os, sys, fcntl

# external packages
import notifier
import notifier.signals as signals
from OpenSSL import *

# internal packages
import session
import message
import univention.debug as ud

import univention.management.console as umc

class MagicBucket( object ):
	def __init__( self, processorClass = session.Processor ):
		self.__states = {}
		self.__processorClass = processorClass

	def __del__( self ):
		self.exit()

	def new( self, client, socket ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'established connection: %s' % client )
		state = session.State( client, socket )
		state.signal_connect( 'authenticated', self._authenticated )
		self.__states[ socket ] = state
		notifier.socket_add( socket , self._receive )

	def exit( self ):
		# remove all sockets
		for sock in self.__states.keys():
			notifier.socket_remove( sock )
		# delete states
		for state in self.__states.values():
			del state
		self.__states = {}

	def _authenticated( self, success, state ):
		if success:
			state.authResponse.status( 200 )
		else:
			state.authResponse.status( 411 ) # authentication failure
		state.authenticated = success
		self._response( state.authResponse, state )
		state.authResponse = None

	def _receive( self, socket ):
		state = self.__states[ socket ]
		data = ''

		try:
			data = socket.recv( 16384 )
		except SSL.WantReadError:
			# this error can be ignored (SSL need to do something)
			return True
		except ( SSL.SysCallError, SSL.Error ), error:
			ud.debug( ud.ADMIN, ud.INFO, 'SSL error: %s. Probably the socket was closed by the client.' % str( error ) )
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
				msg = message.Message()
				state.buffer = msg.parse( state.buffer )
				self._handle( state, msg )
		except message.IncompleteMessageError, e:
			ud.debug( ud.ADMIN, ud.INFO, 'MagicBucket: incomplete message: %s' % str( e ) )
		except ( message.ParseError, message.UnknownCommandError ), e:
			res = message.Response( msg )
			res.id( -1 )
			res.status( e.args[ 0 ] )
			self._response( res, state )

		return True

	def _handle( self, state, msg ):
		if not state.authenticated and msg.command != 'AUTH':
			res = message.Response( msg )
			res.status( 410 ) # unauthorized
			self._response( res, state )
		elif msg.command == 'AUTH':
			state.requests[ msg.id() ] = msg
			state.authResponse = message.Response( msg )
			state.authenticate( msg.body[ 'username' ],	msg.body[ 'password' ] )
		else:
			# inform processor
			if not state.processor:
				state.processor = self.__processorClass( *state.credentials() )
				cb = notifier.Callback( self._response, state )
				state.processor.signal_connect( 'response', cb )
			state.requests[ msg.id() ] = msg
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
			ud.debug( ud.ADMIN, ud.INFO, 'UMCP: SSL error during re-send' )
			state.resend_queue.insert( 0, ( id, first ) )
			return True

		return ( len( state.resend_queue ) > 0 )

	def _response( self, msg, state ):
		# FIXME: error handling is missing!!
		if not state.requests.has_key( msg.id() ) and msg.id() != -1:
			return

		try:
			data = str( msg )
			ret = state.socket.send( data )
			# not all data could be send; retry later
			if ret < len( data ):
				if not state.resend_queue:
					notifier.socket_add( state.socket, self._do_send,
										 notifier.IO_WRITE )
				state.resend_queue.append( ( msg.id(), data[ ret : ] ) )
		except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
			ud.debug( ud.ADMIN, ud.INFO, 'UMCP: SSL error need to re-send chunk' )
			notifier.socket_add( state.socket, self._do_send, notifier.IO_WRITE )
			state.resend_queue.append( data )

class Server( signals.Provider ):
	def __verify_cert_cb( self, conn, cert, errnum, depth, ok ):
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: Got certificate: %s' % cert.get_subject() )
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer() )
		ud.debug( ud.ADMIN, ud.INFO, '__verify_cert_cb: errnum=%d  depth=%d  ok=%d' % (errnum, depth, ok) )
		return ok

	def __init__( self, port = 6670, ssl = True, unix = None, magic = True,
				  magicClass = MagicBucket ):
		signals.Provider.__init__( self )
		self.__port = port
		self.__unix = unix
		self.__ssl = ssl
		if self.__unix:
			self.__realsocket = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
		else:
			self.__realsocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

		self.__realsocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		self.__realsocket.setblocking( 0 )
		fcntl.fcntl(self.__realsocket.fileno(), fcntl.F_SETFD, 1)

		if self.__ssl and not self.__unix:
			self.crypto_context = SSL.Context( SSL.SSLv23_METHOD )
			self.crypto_context.set_cipher_list('DEFAULT')
			self.crypto_context.set_options( SSL.OP_NO_SSLv2 )
			self.crypto_context.set_verify( SSL.VERIFY_PEER, self.__verify_cert_cb )
			dir = '/etc/univention/ssl/%s' % umc.baseconfig[ 'hostname' ]
# used for debugging purposes ==> cert that is not trustworthy
#			self.crypto_context.use_privatekey_file( '/root/server.pkey' )
#			self.crypto_context.use_certificate_file( '/root/server.cert' )
			try:
				self.crypto_context.use_privatekey_file( os.path.join( dir, 'private.key' ) )
				self.crypto_context.use_certificate_file( os.path.join( dir, 'cert.pem' ) )
				self.crypto_context.load_verify_locations( os.path.join( dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem' ) )
			except SSL.Error, e:
				# SSL is not possible
				ud.debug( ud.ADMIN, ud.ERROR, 'Setting up SSL configuration failed: %s' % str( e ) )
				ud.debug( ud.ADMIN, ud.ERROR, 'Communication will not be encrypted!' )
				self.__ssl = False
				self.crypto_context = None
				self.__realsocket.bind( ( '', self.__port ) )
				ud.debug( ud.ADMIN, ud.INFO, 'Server listening to connects' )
				self.__realsocket.listen( 10 )

			if self.crypto_context:
				self.connection = SSL.Connection( self.crypto_context , self.__realsocket )
				self.connection.setblocking(0)
				self.connection.bind( ( '', self.__port ) )
				self.connection.set_accept_state()
				ud.debug( ud.ADMIN, ud.INFO, 'Server listening to SSL connects' )
				self.connection.listen( 10 )
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
			ud.debug( ud.ADMIN, ud.INFO, 'Server listening to connects' )
			self.__realsocket.listen( 10 )

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

	def _connection( self, socket ):
		socket, addr = socket.accept()
		socket.setblocking( 0 )
		if addr:
			client = '%s:%d' % ( addr[ 0 ], addr[ 1 ] )
		else:
			client = ''
		if self.__magic:
			self.__bucket.new( client, socket )
		else:
			self.signal_emit( 'session_new', client, socket )
		return True

	def exit( self ):
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
