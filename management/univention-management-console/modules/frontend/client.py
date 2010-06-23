#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: UMCP client
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

import univention.management.console.protocol as umcp
import univention.management.console.queue as umcq

import univention.debug as ud

import threading

import notifier

import copy
import sys

NOERROR, ERROR_CONNECT = range( 0, 2 )
_queue = umcq.RequestQueue()
_error = NOERROR

class UMCP_Client( object ):
	"""This class mainly wraps the real UMCP client implementation and
	manages a thread-safe queue for UMCP requests"""
	def __init__( self ):
		ud.debug( ud.ADMIN, ud.INFO, "creating new UMCP client" )
		self._client = None
		if not self.__init_client():
			return
		# check queue for new requests
		notifier.dispatcher_add( self._check_queue )
		ud.debug( ud.ADMIN, ud.INFO, "created new UMCP client" )
		self.kill = False
	
	def __nonzero__( self ):
		return self._client != None

	def __init_client( self ):
		if self._client:
			del self._client
		self._client = umcp.Client()
		if not self._client:
		  	self._client = None
			error_set( ERROR_CONNECT )
			return False
		# handling authentication
		self._client.signal_connect( 'authenticated', self._authenticated )
		self._auth_response = None

		# handle other responses
		self._client.signal_connect( 'response', self._response )

		# handle lost connection
		self._client.signal_connect( 'closed', self._closed )
		error_set( ERROR_CONNECT )

		return True

	def connect( self ):
		ud.debug( ud.ADMIN, ud.INFO, "connecting to UMCP server" )
		try:
			if not self._client.connect():
				error_set( ERROR_CONNECT )
				return False
			else:
				error_set( NOERROR )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.INFO, "ERROR: connect: %s" % str( e ) )

		return True

	def disconnect( self ):
		try:
			ud.debug( ud.ADMIN, ud.INFO, "disconnecting from UMCP server" )
			self.__init_client()
		except Exception, e:
			ud.debug( ud.ADMIN, ud.INFO, "ERROR: disconnect: %s" % str( e ) )

		return True

	def _closed( self ):
		ud.debug( ud.ADMIN, ud.INFO, "connection to UMCP server closed" )
		error_set( ERROR_CONNECT )

	def _response( self, response ):
		global _queue
		ud.debug( ud.ADMIN, ud.INFO, "client._response: Got response for %s, status: %d" % ( str( response.id() ), response.status() ) )
		_queue.appendResponse( response )

	def _authenticated( self, success, status, message ):
		global _queue
		ud.debug( ud.ADMIN, ud.INFO, "client._authenticated: status: %s" % str( status ) )
		self._auth_response.status( status )
		_queue.appendResponse( self._auth_response )

	def _check_queue( self ):
		if self.kill:
			sys.exit( 0 )
		global _queue, _error
		req = _queue.getUnseenRequest()
		if req:
			if not isinstance( req, basestring ):
				if req.command == 'AUTH':
					self._auth_response = umcp.Response( req )
					self._client.authenticate( req.body[ 'username' ],
											   req.body[ 'password' ] )
				else:
					self._client.request( req )

			else:
				if req == 'connect':
					ud.debug( ud.ADMIN, ud.INFO, "client._check_queue: connect to server" )
					res = self.connect()
					ud.debug( ud.ADMIN, ud.INFO, "client._check_queue: server response: %s" % str( res ) )
					_queue.setActionResult( req, res )
				elif req == 'disconnect':
					ud.debug( ud.ADMIN, ud.INFO, "client._check_queue: disconnect from server" )
					res = self.disconnect()
					ud.debug( ud.ADMIN, ud.INFO, "client._check_queue: server response: %s" % str( res ) )
					_queue.setActionResult( req, res )

		return True

_client = None
_thread = None
_sessionId = None

def __loop():
	notifier.loop()

def set_sessionid( sessid ):
	global _sessionId
	_sessionId = sessid

def run():
	global _thread, _client

	notifier.init( notifier.GENERIC )
	_client = UMCP_Client()
	if not _client:
		return False
	_thread = threading.Thread( target = __loop )
	_thread.start()

	return True

def stop():
	global _client
	_client.kill = True

def request_group_send( requests ):
	global _queue, _request_group

	id = _queue.newRequestGroup( requests )
	ud.debug( ud.ADMIN, ud.INFO, "client.request_group_send: NEW! %s" % id )

	return id

def request_send( request ):
	global _queue
# 	request = copy.deepcopy( request )
# 	request.recreate_id()
	id =  _queue.newRequest( request )
	ud.debug( ud.ADMIN, ud.INFO, "client.request_send: NEW! %s" % id )

	return id

def response_group_wait( id, timeout = 4 ):
	global _queue
	ud.debug( ud.ADMIN, ud.INFO, "client.response_group_wait: NEW! %s" % id )

	# is there already a response available?
	if _queue.isResponseGroupAvailable( id ):
		return _queue.getGroupResponse( id )

	# let's wait for a response
	event = threading.Event()
	if not _queue.setGroupEvent( id, event ):
		ud.debug( ud.ADMIN, ud.INFO, "client.response_group_wait: Request ID %s not found!" % str( id ) )

	event.wait( timeout )
	if event.isSet():
		return _queue.getGroupResponse( id )
	ud.debug( ud.ADMIN, ud.INFO, "client.response_group_wait: NO EVENT!" )

	return None

def response_wait( id, timeout = 2 ):
	global _queue
	ud.debug( ud.ADMIN, ud.INFO, "client.response_wait: NEW! %s" % id )

	# is there already a response available?
	if _queue.isResponseAvailable( id ):
		return _queue.getLastResponse( id )

	# let's wait for a response
	event = threading.Event()
	if not _queue.setEvent( id, event ):
		ud.debug( ud.ADMIN, ud.INFO, "client.response_wait: Request ID %s not found!" % str( id ) )

	event.wait( timeout )
	if event.isSet():
		return _queue.getLastResponse( id )
	ud.debug( ud.ADMIN, ud.INFO, "client.response_wait: NO EVENT!" )

	return None

def __action( action, timeout ):
	global _queue
	event = threading.Event()
	_queue.newAction( action, event )
	event.wait( timeout )
	if event.isSet():
		return _queue.getActionResult( action )
	return False

def connect( timeout = 2 ):
	return __action( 'connect', timeout )

def disconnect( timeout = 2 ):
	return __action( 'disconnect', timeout )

def error_set( id ):
	global _error
	_error = id

def error_get():
	global _error
	ret = _error
	_error = NOERROR
	return ret
