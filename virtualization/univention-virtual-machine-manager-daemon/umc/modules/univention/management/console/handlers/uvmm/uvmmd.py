#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: UVMM client
#
# Copyright (C) 2010 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

import socket
import time

import notifier
import notifier.signals

import univention.management.console.tools as umct

from univention.uvmm import protocol

import univention.debug as ud

class ConnectionError( Exception ):
	pass

class Client( notifier.signals.Provider ):
	def __init__( self, unix_socket = '/var/run/uvmm.socket', auto_connect = True ):
		notifier.signals.Provider.__init__( self )
		self._socket = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
		self._buffer = ''
		self._response = None
		self._unix_socket = unix_socket
		self.connection_wait = 10
		# provide signals
		self.signal_new( 'received' )

		if auto_connect:
			self.connect()

	def is_connected( self ):
		try:
			self.socket.getpeername()
			return True
		except:
			return False

	def connect( self ):
		# we need to provide a dispatcher function to activate the minimal timeout
		def fake_dispatcher(): return True
		notifier.dispatcher_add( fake_dispatcher )

		countdown = umct.CountDown( self.connection_wait * 1000 )
		errno = self._socket.connect_ex( self._unix_socket )
		while errno and countdown():
			notifier.step()
			errno = self._socket.connect_ex( self._unix_socket )

		if errno:
			ret = False
		else:
			ret = True
			self._socket.setblocking( 0 )
			notifier.socket_add( self._socket, self._receive )

		# remove dspatcher function
		notifier.dispatcher_remove( fake_dispatcher )

		return ret

	def _receive( self, socket ):
		data = self._socket.recv( 4096 )
	
		# connection closed?
		if not data:
			return False

		self._buffer += data
		packet = protocol.Packet.parse( self._buffer )

		# waiting for rest of packet
		if packet == None:
			return True

		( length, res ) = packet
		self._buffer = self._buffer[ length : ]

		if not isinstance( res, protocol.Response ):
			return True

		self.signal_emit( 'received', res )

		return True

	def _signal_received( self, res ):
		self._packet = res

	def recv_blocking( self ):
		self._packet = None
		self.signal_connect( 'received', self._signal_received )
		while not self._packet:
			notifier.step()
		self.signal_disconnect( 'received', self._signal_received )

		if self.is_error( self._packet ):
			ud.debug( ud.ADMIN, ud.ERROR, 'UVMM: request failed: %s' % self._packet.msg )
			
		return self._packet

	def send( self, packet, retry = True ):
		try:
			self._socket.send( packet )
		except:
			ud.debug( ud.ADMIN, ud.WARN, 'UVMM: send failed' )
			if not self.is_connected():
				ud.debug( ud.ADMIN, ud.INFO, 'UVMM: try to reconnect' )
				if not self.connect():
					return False
				if retry:
					return self.send( packet, False )
			else:
				return False
		return True

	def is_error( self, response ):
		return isinstance( response, protocol.Response_ERROR )

	def get_node_info( self, node ):
		req = protocol.Request_NODE_QUERY()
		req.uri = node
		if not self.send( req.pack() ):
			raise ConnectionError()
		node_info = self.recv_blocking()

		if self.is_error( node_info ):
			return None

		return node_info.data

	def get_domain_info( self, node, domain ):
		node_info = self.get_node_info( node )
		if self.is_error( node_info ):
			return None
		for dom in node_info.domains:
			if dom.name == domain:
				return dom

		return None

	def node_name2uri( self, name ):
		req = protocol.Request_GROUP_LIST()
		if not self.send( req.pack() ):
			raise ConnectionError()
		
		groups = self.recv_blocking()

		tree_data = []
		for grp in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = grp
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_uris = self.recv_blocking()
			for node in node_uris.data:
				domains = []
				req = protocol.Request_NODE_QUERY()
				req.uri = node
				if not self.send( req.pack() ):
					raise ConnectionError()
				node_info = self.recv_blocking()
				if self.is_error( node_info ):
					continue
				if node_info.data.name == name:
					return node

		return None

	def get_group_info( self, group ):
		req = protocol.Request_NODE_LIST()
		req.group = group
		if not self.send( req.pack() ):
			raise ConnectionError()
		node_uris = self.recv_blocking()
		group = []
		if self.is_error( node_uris ):
			return group
		for node in node_uris.data:
			req = protocol.Request_NODE_QUERY()
			req.uri = node
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_info = self.recv_blocking()
			if not self.is_error( node_info ):
				group.append( node_info.data )

		return group
		
	def get_node_tree( self ):
		req = protocol.Request_GROUP_LIST()
		if not self.send( req.pack() ):
			raise ConnectionError()
		
		groups = self.recv_blocking()

		tree_data = []
		groups.data.sort()
		for grp in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = grp
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_uris = self.recv_blocking()
			node_uris.data.sort(lambda a, b: cmp(a[a.find('://')+3:], b[b.find('://')+3:]))
			for node in node_uris.data:
				domains = []
				req = protocol.Request_NODE_QUERY()
				req.uri = node
				if not self.send( req.pack() ):
					raise ConnectionError()
				node_info = self.recv_blocking()

				if self.is_error( node_info ):
					group.extend( [ node[ node.find( '://' ) + 3 : node.rfind( '/' ) ], None ]  )
				else:
					node_info.data.domains.sort(lambda a, b: cmp(a.name, b.name))
					for dom in node_info.data.domains:
						domains.append( dom.name )
					group.extend( [ node_info.data.name, domains ] )
			tree_data.append( [ grp, group ] )

		return tree_data

	def domain_set_state( self, node, domain, state ):
		uri = self.node_name2uri( node )
		domain_info = self.get_domain_info( uri, domain )
		req = protocol.Request_DOMAIN_STATE()
		req.uri = uri
		req.domain = domain_info.uuid
		# RUN PAUSE SHUTDOWN RESTART
		req.state = state
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_configure( self, node, data ):
		req = protocol.Request_DOMAIN_DEFINE()
		req.uri = self.node_name2uri( node )
		ud.debug( ud.ADMIN, ud.ERROR, 'disks to send: %s' % data.disks )
		ud.debug( ud.ADMIN, ud.ERROR, 'interfaces to send: %s' % data.interfaces )
		req.domain = data
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_migrate( self, source, dest, domain ):
		req = protocol.Request_DOMAIN_MIGRATE()
		req.uri = source
		req.domain = domain
		req.target_uri = dest
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_undefine( self, node, domain, drives ):
		req = protocol.Request_DOMAIN_UNDEFINE()
		req.uri = node
		req.domain = domain
		req.volumes = drives
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()
		
if __name__ == '__main__':
	notifier.init()

	notifier.timer_add( 1000, lambda: True )
	c = Client()
	print c.get_node_tree()
	notifier.loop()
