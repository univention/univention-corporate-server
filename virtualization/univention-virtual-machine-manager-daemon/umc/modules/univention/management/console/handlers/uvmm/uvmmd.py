#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: UVMM client
#
# Copyright 2010, 2011 Univention GmbH
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

import fnmatch
import os
import socket
import time

import notifier
import notifier.signals

import univention.management.console as umc
import univention.management.console.tools as umct

from univention.uvmm import protocol, node

import univention.debug as ud
import traceback

from tools import *

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class UvmmError(Exception):
	"""UVMM-request was not successful."""
	pass

class ConnectionError(UvmmError):
	"""UVMM-request was not successful because of broken connection."""
	pass

class Bus( object ):
	"""Periphery bus like IDE-, SCSI-, Xen-, VirtIO- und FDC-Bus."""
	def __init__( self, name, prefix, default = False, unsupported = ( node.Disk.DEVICE_FLOPPY, ) ):
		self._next_letter = 'a'
		self._connected = set()
		self.name = name
		self.prefix = prefix
		self.default = default
		self.unsupported = unsupported

	def compatible( self, dev ):
		'''Checks the compatibility of the given device with the bus
		specification: the device type must be supported by the bus and
		if the bus of the device is set it must match otherwise the bus
		must be defined as default.'''
		return ( not dev.device in self.unsupported ) and ( dev.target_bus == self.name or ( not dev.target_bus and self.default ) )

	def attach( self, devices ):
		"""Register each device in devices list at bus."""
		for dev in devices:
			if dev.target_dev and ( dev.target_bus == self.name or ( not dev.target_bus and self.default ) ):
				letter = dev.target_dev[ -1 ]
				self._connected.add(letter)

	def connect( self, dev ):
		"""Connect new device at bus and assign new drive letter."""
		if not self.compatible( dev ) or dev.target_dev:
			return False
		self.next_letter()
		dev.target_dev = self.prefix % self._next_letter
		ud.debug( ud.ADMIN, ud.INFO, 'Connected device: %s, %s' % ( dev.target_bus, dev.target_dev ) )
		self._connected.add(self._next_letter)
		self.next_letter()
		return True

	def next_letter( self ):
		"""Find and return next un-used drive letter.
		>>> b = Bus('', '')
		>>> b._next_letter = 'a' ; b._connected.add('a') ; b.next_letter()
		'b'
		>>> b._next_letter = 'z' ; b._connected.add('z') ; b.next_letter()
		'aa'
		"""
		while self._next_letter in self._connected:
			self._next_letter = chr( ord( self._next_letter ) + 1 )
		return self._next_letter

class Client( notifier.signals.Provider ):
	"""Connection to UVMMd."""
	def __init__( self, unix_socket = '/var/run/uvmm.socket', auto_connect = True ):
		notifier.signals.Provider.__init__( self )
		self._socket = None
		self._buffer = ''
		self._response = None
		self._unix_socket = unix_socket
		self.connection_wait = 10
		# provide signals
		self.signal_new( 'received' )

		if auto_connect:
			self.connect()

	def is_connected( self ):
		if not self._socket:
			return False

		try:
			self.socket.getpeername()
			return True
		except:
			return False

	def connect( self ):
		# we need to provide a dispatcher function to activate the minimal timeout
		def fake_dispatcher(): return True
		notifier.dispatcher_add( fake_dispatcher )

		self._socket = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )

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

	def reconnect( self ):
		# the uvmmd start may take a few seconds
		time.sleep(6)

		# reinitialise the socket
		self._socket = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )

		return self.connect()

	def _receive( self, socket ):
		if not self._socket:
			self.connect()

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
			ud.debug( ud.ADMIN, ud.INFO, 'UVMM: failure received: %s' % self._packet.msg )

		return self._packet

	def send( self, packet, retry = True ):
		if not self._socket:
			self.connect()

		try:
			self._socket.send( packet )
		except:
			ud.debug( ud.ADMIN, ud.WARN, 'UVMM: send failed' )
			if not self.is_connected():
				ud.debug( ud.ADMIN, ud.INFO, 'UVMM: try to reconnect' )
				if not self.reconnect():
					return False
				if retry:
					return self.send( packet, False )
			else:
				return False
		return True

	def is_error( self, response ):
		return isinstance( response, protocol.Response_ERROR )

	def get_node_info( self, node_uri ):
		"""Retrieve information for node_uri."""
		if node_uri is None:
			ud.debug(ud.ADMIN, ud.ALL, "Invalid node_uri: %r" % traceback.format_list(traceback.extract_stack()))
			return None
		req = protocol.Request_NODE_QUERY()
		req.uri = node_uri
		if not self.send( req.pack() ):
			raise ConnectionError()
		node_info = self.recv_blocking()

		if self.is_error( node_info ):
			return None

		return node_info.data

	def is_domain_name_unique( self, node_uri, domain_name ):
		node_info = self.get_node_info( node_uri )
		if not node_info:
			return None

		for domain_info in node_info.domains:
			if domain_info.name == domain_name:
				return False
		return True

	def is_image_used( self, node_uri, image, relative = False ):
		"""Return name of domain using image."""
		node_info = self.get_node_info( node_uri )
		if not node_info:
			return None

		if relative:
			func = os.path.basename
		else:
			func = lambda x: x
		for domain_info in node_info.domains:
			for disk in domain_info.disks:
				if func( disk.source ) == image:
					return domain_info.name
		return None

	def next_drive_name(self, node_uri, domain_name, suffix='.img', temp_drives=[]):
		"""Return next unused image name."""
		i = 0
		pattern = '%s-%d' + suffix
		ud.debug(ud.ADMIN, ud.INFO, 'NEXT DRIVE: dn=%s bl=%s s=%s' % (domain_name, temp_drives, suffix))
		#ud.debug(ud.ADMIN, ud.INFO, 'NEXT DRIVE: dn=%s bl=%s s=%s p=%s' % (domain_name, temp_drives, suffix, pattern))
		while True:
			name = pattern % ( domain_name, i )
			ud.debug(ud.ADMIN, ud.INFO, 'NEXT DRIVE: p=%s' % name)
			if name in temp_drives or self.is_image_used(node_uri, name, relative=True):
				i += 1
			else:
				return name

	def get_domain_info_ext( self, node_uri, domain_name_or_uuid ):
		retries = 10
		while retries:
			node_info = self.get_node_info( node_uri )
			if not node_info:
				return ( None, None )
			for domain_info in node_info.domains:
				if domain_info.name == domain_name_or_uuid or domain_info.uuid == domain_name_or_uuid:
					return (node_info, domain_info )
			time.sleep( 0.1 )
			retries -= 1
		return ( None, None )

	def get_domain_info( self, node_uri, domain_name ):
		node_info, domain_info = self.get_domain_info_ext( node_uri, domain_name )
		return domain_info

	def node_name2uri( self, node_name ):
		req = protocol.Request_GROUP_LIST()
		if not self.send( req.pack() ):
			raise ConnectionError()

		groups = self.recv_blocking()

		tree_data = []
		for group_name in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_uris = self.recv_blocking()
			for node_uri in node_uris.data:
				domains = []
				req = protocol.Request_NODE_QUERY()
				req.uri = node_uri
				if not self.send( req.pack() ):
					raise ConnectionError()
				node_info = self.recv_blocking()
				if self.is_error( node_info ):
					continue
				if node_info.data.name == node_name:
					return node_uri

		return None

	def search( self, pattern, option ):
		req = protocol.Request_GROUP_LIST()
		if not self.send( req.pack() ):
			raise ConnectionError()

		pattern = str2pat( pattern )
		pattern_regex = re.compile( fnmatch.translate( pattern ), re.IGNORECASE )
		groups = self.recv_blocking()

		result = []
		groups.data.sort()
		for group_name in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_uris = self.recv_blocking()
			for uri in node_uris.data:
				node = self.get_node_info( uri )
				if not node:
					continue
				node.uri = uri

				domains = []
				for domain in node.domains:
					if domain.name == 'Domain-0':
						continue
					if option in ( 'all', 'domains' ) and pattern_regex.match( domain.name ):
						domains.append( domain )
						continue
					if option in ( 'all', 'contacts' ) and pattern_regex.match( domain.annotations.get( 'contact', '' ) ):
						domains.append( domain )
						continue
					if option in ( 'all', 'descriptions' ) and pattern_regex.match( domain.annotations.get( 'description', '' ) ):
						domains.append( domain )
						continue

				if ( option in ( 'all', 'nodes' ) and pattern_regex.match( node.name ) ) or domains:
					result.append( ( node, domains ) )

		return result

	def get_group_info( self, group ):
		req = protocol.Request_NODE_LIST()
		req.group = group
		if not self.send( req.pack() ):
			raise ConnectionError()
		node_uris = self.recv_blocking()
		group = []
		if self.is_error( node_uris ):
			return group
		for node_uri in node_uris.data:
			req = protocol.Request_NODE_QUERY()
			req.uri = node_uri
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_info = self.recv_blocking()
			if not self.is_error( node_info ):
				group.append( node_info.data )

		return group

	@staticmethod
	def _uri2name( uri ):
		"""Strip schema and path from uri."""
		i = uri.find('://')
		if i >= 0:
			uri = uri[i + 3:]
		j = uri.find('/')
		if j >= 0:
			uri = uri[:j]
		return uri

	def get_node_tree( self ):
		"""Return tree of names for all groups, nodes, and domains.
		[
		 [group_name, [
		               node_name, [domain, ...],
		               node_name, None,
		               ...
		              ],
		 ],
		]"""
		req = protocol.Request_GROUP_LIST()
		if not self.send( req.pack() ):
			raise ConnectionError()

		groups = self.recv_blocking()

		tree_data = []
		groups.data.sort()
		for group_name in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			if not self.send( req.pack() ):
				raise ConnectionError()
			node_uris = self.recv_blocking()
			nodes = [(Client._uri2name( uri ), uri) for uri in node_uris.data]
			nodes.sort()
			for (node_name, node_uri) in nodes:
				domains = []
				req = protocol.Request_NODE_QUERY()
				req.uri = node_uri
				if not self.send( req.pack() ):
					raise ConnectionError()
				node_info = self.recv_blocking()

				if self.is_error( node_info ):
					group.extend( [node_name, None ]  )
				else:
					node_info.data.domains.sort(lambda a, b: cmp(a.name, b.name))
					for domain_info in node_info.data.domains:
						domains.append( domain_info.name )
					group.extend( [ node_name, domains ] )
			tree_data.append( [ group_name, group ] )

		return tree_data

	def domain_set_state( self, node_name, domain_name, state ):
		node_uri = self.node_name2uri( node_name )
		domain_info = self.get_domain_info( node_uri, domain_name )
		req = protocol.Request_DOMAIN_STATE()
		req.uri = node_uri
		req.domain = domain_info.uuid
		# RUN PAUSE SHUTDOWN RESTART
		req.state = state
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def __next_letter( self, char, exclude = [] ):
		char = chr( ord( char ) + 1 )
		while char in exclude:
			char = chr( ord( char ) + 1 )

		exclude.append( char )
		return char

	# def _verify_device_files( self, domain_info ):
	# 	cdrom_name = 'a'
	# 	cdrom_prefix = 'hd%s'
	# 	dev_name = 'a'
	# 	device_prefix = 'hd%s'
	# 	if domain_info.domain_type == 'xen' and domain_info.os_type in ('linux', 'xen'):
	# 		device_prefix = 'xvd%s'
	# 	elif domain_info.domain_type == 'kvm':
	# 		device_prefix = 'vd%s' # virtio instead of ide

	# 	dev_exclude = []
	# 	cdrom_exclude = []
	# 	for dev in domain_info.disks:
	# 		if dev.target_dev:
	# 			if dev.device == node_info.Disk.DEVICE_CDROM and domain_info.domain_type == 'kvm':
	# 				cdrom_exclude.append( dev.target_dev[ -1 ] )
	# 			else:
	# 				dev_exclude.append( dev.target_dev[ -1 ] )

	# 	if cdrom_name in cdrom_exclude:
	# 		cdrom_name = self.__next_letter( cdrom_name, cdrom_exclude )
	# 	if dev_name in dev_exclude:
	# 		dev_name = self.__next_letter( dev_name, dev_exclude )

	# 	for dev in domain_info.disks:
	# 		# CDROM drive need to use the ide driver as booting from virtio devices does not work
	# 		if dev.device == node_info.Disk.DEVICE_CDROM and domain_info.domain_type == 'kvm':
	# 			if not dev.target_dev:
	# 				dev.target_dev = cdrom_prefix % cdrom_name
	# 				cdrom_name = self.__next_letter( cdrom_name, cdrom_exclude )
	# 		else:
	# 			if not dev.target_dev:
	# 				dev.target_dev = device_prefix % dev_name
	# 				dev_name = self.__next_letter( dev_name, dev_exclude )

	# FIXME: currently we need to use IDE only for KVM as Windows is
	# not able to handle virtio drives!!! The profile should contain the
	# information which platform will be installed.
	# def _verify_device_files( self, domain_info ):
	# 	dev_name = 'a'
	# 	device_prefix = 'hd%s'
	# 	if domain_info.domain_type == 'xen' and domain_info.os_type == 'linux':
	# 		device_prefix = 'xvd%s'

	# 	dev_exclude = []
	# 	for dev in domain_info.disks:
	# 		if dev.target_dev:
	# 			dev_exclude.append( dev.target_dev[ -1 ] )

	# 	if dev_name in dev_exclude:
	# 		dev_name = self.__next_letter( dev_name, dev_exclude )

	# 	for dev in domain_info.disks:
	# 		if not dev.target_dev:
	# 			dev.target_dev = device_prefix % dev_name
	# 			dev_name = self.__next_letter( dev_name, dev_exclude )

	def _verify_device_files( self, domain_info ):
		if domain_info.domain_type == 'xen' and domain_info.os_type in ( 'linux', 'xen' ):
			busses = ( Bus( 'ide', 'hd%s' ), Bus( 'xen', 'xvd%s', default = True ), Bus( 'virtio', 'vd%s' ) )
		else:
			busses = ( Bus( 'ide', 'hd%s', default = True ), Bus( 'xen', 'xvd%s' ), Bus( 'virtio', 'vd%s' ), Bus( 'fdc', 'fd%s', default = True, unsupported = ( node.Disk.DEVICE_DISK, node.Disk.DEVICE_CDROM ) ) )

		for bus in busses:
			bus.attach( domain_info.disks )

		for dev in domain_info.disks:
			for bus in busses:
				if bus.connect( dev ):
					break

	def domain_configure( self, node_name, data ):
		req = protocol.Request_DOMAIN_DEFINE()
		req.uri = self.node_name2uri( node_name )
		ud.debug(ud.ADMIN, ud.INFO, 'disks to send: %s' % data.disks)
		ud.debug(ud.ADMIN, ud.INFO, 'interfaces to send: %s' % data.interfaces)
		self._verify_device_files( data )
		req.domain = data
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_migrate( self, source, dest, domain_uuid ):
		req = protocol.Request_DOMAIN_MIGRATE()
		req.uri = source
		req.domain = domain_uuid
		req.target_uri = dest
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_undefine( self, node_uri, domain_uuid, drives ):
		req = protocol.Request_DOMAIN_UNDEFINE()
		req.uri = node_uri
		req.domain = domain_uuid
		req.volumes = drives
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_save( self, node_name, domain_info ):
		req = protocol.Request_DOMAIN_SAVE()
		req.uri = self.node_name2uri( node_name )
		req.domain = domain_info.uuid
		snapshot_dir = umc.registry.get( 'uvmm/pool/default/path', '/var/lib/libvirt/images' )
		req.statefile = os.path.join( snapshot_dir, '%s.snapshot' % domain_info.uuid )
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_restore( self, node_name, domain_info ):
		req = protocol.Request_DOMAIN_RESTORE()
		req.uri = self.node_name2uri( node_name )
		req.domain = domain_info.uuid
		snapshot_dir = umc.registry.get( 'uvmm/pool/default/path', '/var/lib/libvirt/images' )
		req.statefile = os.path.join( snapshot_dir, '%s.snapshot' % domain_info.uuid )
		if not self.send( req.pack() ):
			raise ConnectionError()
		return self.recv_blocking()

	def domain_snapshot_create(self, node_uri, domain_info, snapshot_name):
		"""Create new snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_CREATE()
		req.uri = node_uri
		req.domain = domain_info.uuid
		req.snapshot = snapshot_name
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if self.is_error(response):
			raise UvmmError(response.msg)

	def domain_snapshot_revert(self, node_uri, domain_info, snapshot_name):
		"""Revert to snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_REVERT()
		req.uri = node_uri
		req.domain = domain_info.uuid
		req.snapshot = snapshot_name
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if self.is_error(response):
			raise UvmmError(response.msg)

	def domain_snapshot_delete(self, node_uri, domain_info, snapshot_name):
		"""Delete snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_DELETE()
		req.uri = node_uri
		req.domain = domain_info.uuid
		req.snapshot = snapshot_name
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if self.is_error(response):
			raise UvmmError(response.msg)

	def storage_pools(self, node_uri):
		"""Get pools of node."""
		req = protocol.Request_STORAGE_POOLS(uri=node_uri)
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if self.is_error( response ):
			raise UvmmError(response.msg)
		return response.data

	def storage_pool_volumes( self, node_uri, pool, type = None ):
		req = protocol.Request_STORAGE_VOLUMES()
		req.uri = node_uri
		req.pool = pool
		req.type = type
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if not self.is_error( response ):
			return response.data

		return []

	def storage_volumes_destroy( self, node_uri, volumes ):
		req = protocol.Request_STORAGE_VOLUMES_DESTROY()
		req.uri = node_uri
		req.volumes = volumes
		if not self.send( req.pack() ):
			raise ConnectionError()
		response = self.recv_blocking()
		if not self.is_error( response ):
			return True

		return False

if __name__ == '__main__':
	import doctest
	doctest.testmod()

	notifier.init()

	notifier.timer_add( 1000, lambda: True )
	c = Client()
	import pprint
	pprint.pprint(c.get_node_tree())
	notifier.loop()
