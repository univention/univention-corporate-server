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

class CommandError(UvmmError):
	"""UVMM-request was not successful because the comand was not successful."""
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
		"""Check if the UVMMd connection is connected."""
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
		"""Internal function called by the notifier when data is available for reading from the UVMMd socket connection."""
		if not self._socket:
			self.connect()

		data = self._socket.recv( 4096 )

		# connection closed?
		if not data:
			return False

		self._buffer += data
		packet = protocol.Packet.parse( self._buffer )

		# waiting for rest of packet
		if packet is None:
			return True

		( length, res ) = packet
		self._buffer = self._buffer[ length : ]

		if not isinstance( res, protocol.Response ):
			return True

		self.signal_emit( 'received', res )

		return True

	def _signal_received( self, res ):
		"""Internal function called when a full Response packet is available."""
		self._packet = res

	def recv_blocking( self ):
		self._packet = None
		self.signal_connect( 'received', self._signal_received )
		while not self._packet:
			notifier.step()
		self.signal_disconnect( 'received', self._signal_received )

		if isinstance(self._packet, protocol.Response_ERROR):
			raise CommandError(self._packet.msg)

		return self._packet

	def send( self, packet, retry = True ):
		if not self._socket:
			self.connect()

		try:
			self._socket.send( packet )
		except:
			ud.debug( ud.ADMIN, ud.WARN, 'UVMM: send failed' )
			if self.is_connected():
				raise ConnectionError("Faild to send")
			ud.debug( ud.ADMIN, ud.INFO, 'UVMM: try to reconnect' )
			if not self.reconnect():
				raise ConnectionError("Faild to reconnect")
			if retry:
				return self.send( packet, False )

	def get_node_info( self, node_uri ):
		"""Retrieve information for node_uri."""
		if node_uri is None:
			ud.debug(ud.ADMIN, ud.ALL, "Invalid node_uri: %r" % traceback.format_list(traceback.extract_stack()))
			return None
		req = protocol.Request_NODE_QUERY()
		req.uri = node_uri
		try:
			self.send(req.pack())
			node_info = self.recv_blocking()
		except UvmmError, e:
			raise
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
			for domain_info in node_info.domains:
				if domain_info.name == domain_name_or_uuid or domain_info.uuid == domain_name_or_uuid:
					return (node_info, domain_info )
			time.sleep( 0.1 )
			retries -= 1
		return ( None, None )

	def __node_name2uri(self, node_name):
		req = protocol.Request_GROUP_LIST()
		try:
			self.send(req.pack())
			groups = self.recv_blocking()
		except UvmmError, e:
			raise

		tree_data = []
		for group_name in groups.data:
			group = []
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			try:
				self.send(req.pack())
				node_uris = self.recv_blocking()
			except UvmmError, e:
				raise
			for node_uri in node_uris.data:
				domains = []
				req = protocol.Request_NODE_QUERY()
				req.uri = node_uri
				try:
					self.send(req.pack())
					node_info = self.recv_blocking()
				except UvmmError, e:
					continue
				if node_info.data.name == node_name:
					return node_uri

		return None

	def node_uri_name(self, node_uri_or_node_name):
		"""Normalize node_uri_or_node_name to 2-tuple (node_uri, node_name)."""
		pos = node_uri_or_node_name.find('://')
		if pos >= 0:
			node_uri = node_uri_or_node_name
			node_name = node_uri_or_node_name[pos + 3:]
			pos = node_name.find('/')
			if pos >= 0:
				node_name = node_name[:pos]
		else:
			node_name = node_uri_or_node_name
			node_uri = self.__node_name2uri(node_name)
		return (node_uri, node_name)

	def search( self, pattern, option ):
		"""
		Search for instances matching pattern.
		'pattern' is a wildcard-pattern.
		'option' is one of 'all', 'domains', 'contacts', 'description', 'nodes'
		specifying the category where 'pattern' must match.

		Returns a list of 2-tuples: [(nod_info, [domain_info,...]),...].
		"""
		pattern = str2pat( pattern )
		pattern_regex = re.compile( fnmatch.translate( pattern ), re.IGNORECASE )

		req = protocol.Request_GROUP_LIST()
		try:
			self.send(req.pack())
			groups = self.recv_blocking()
		except UvmmError, e:
			raise

		result = []
		groups.data.sort()
		for group_name in groups.data:
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			try:
				self.send(req.pack())
				node_uris = self.recv_blocking()
			except UvmmError, e:
				raise
			for uri in node_uris.data:
				try:
					node = self.get_node_info( uri )
				except UvmmError, e:
					continue

				domain_infos = []
				for domain_info in node_info.domains:
					if domain.name == 'Domain-0':
						continue
					if option in ( 'all', 'domains' ) and pattern_regex.match( domain_info.name ):
						domain_infos.append( domain_info )
						continue
					if option in ( 'all', 'contacts' ) and pattern_regex.match( domain_info.annotations.get( 'contact', '' ) ):
						domain_infos.append( domain_info )
						continue
					if option in ( 'all', 'descriptions' ) and pattern_regex.match( domain_info.annotations.get( 'description', '' ) ):
						domain_infos.append( domain_info )
						continue

				if ( option in ( 'all', 'nodes' ) and pattern_regex.match( node_info.name ) ) or domain_infos:
					result.append( ( node_info, domain_infos ) )

		return result

	def get_group_info(self, group_name):
		"""Return dict {node_uri: node_info} for all available hosts in group."""
		group = {}

		req = protocol.Request_NODE_LIST()
		req.group = group_name
		try:
			self.send(req.pack())
			node_uris = self.recv_blocking()
		except UvmmError, e:
			ud.debug(ud.ADMIN, ud.ERROR, '*** %s' % e)
			return group
		for node_uri in node_uris.data:
			req = protocol.Request_NODE_QUERY()
			req.uri = node_uri
			try:
				self.send(req.pack())
				node_info = self.recv_blocking()
			except UvmmError, e:
				ud.debug(ud.ADMIN, ud.ERROR, '*** %s' % e)
				continue
			group[node_uri] = node_info.data

		return group

	@staticmethod
	def _uri2name(uri, short=False):
		"""Strip schema and path from uri. Optionally return only host-name without domain-name."""
		i = uri.find('://')
		if i >= 0:
			uri = uri[i + 3:]
		i = uri.find('/')
		if i >= 0:
			uri = uri[:i]
		if short:
			i = uri.find('.')
			if i >= 0:
				uri = uri[:i]
		return uri

	def get_node_tree( self ):
		"""Return a 'tree', which is a nested dict of names for all groups,
		nodes and domains including 'age' of node_info and 'state' from
		domain_info.
		tree = {
			group_name: {
				node_uri: (age, {
					domain_uuid: domain_info,
					...
					}),
				node_uri: (age, {}),
				...
			},
			...
		}
		"""

		req = protocol.Request_GROUP_LIST()
		try:
			self.send(req.pack())
			groups = self.recv_blocking()
		except UvmmError, e:
			raise

		tree_data = {}
		for group_name in groups.data:
			req = protocol.Request_NODE_LIST()
			req.group = group_name
			try:
				self.send(req.pack())
				node_uris = self.recv_blocking()
			except UvmmError, e:
				raise

			tree_data[group_name] = group = {}
			for node_uri in node_uris.data:
				domains = {}
				req = protocol.Request_NODE_QUERY()
				req.uri = node_uri
				try:
					self.send(req.pack())
					node_info = self.recv_blocking()
				except UvmmError, e:
					age = float('infinity')
					continue
				else:
					age = node_info.data.last_try - node_info.data.last_update
					for domain_info in node_info.data.domains:
						domains[domain_info.uuid] = domain_info
				group[node_uri] = (age, domains)

		return tree_data

	def domain_set_state( self, node_uri, domain_uuid, state ):
		req = protocol.Request_DOMAIN_STATE()
		req.uri = node_uri
		req.domain = domain_uuid
		# RUN PAUSE SHUTDOWN RESTART
		req.state = state
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

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

	def domain_configure( self, node_uri, data ):
		ud.debug(ud.ADMIN, ud.INFO, 'disks to send: %s' % data.disks)
		ud.debug(ud.ADMIN, ud.INFO, 'interfaces to send: %s' % data.interfaces)
		self._verify_device_files( data )
		req = protocol.Request_DOMAIN_DEFINE()
		req.uri = node_uri
		req.domain = data
		try:
			self.send(req.pack())
			response = self.recv_blocking()
			return response # (.data=UUID, .messages=warnings)
		except UvmmError, e:
			raise

	def domain_migrate( self, source, dest, domain_uuid ):
		req = protocol.Request_DOMAIN_MIGRATE()
		req.uri = source
		req.domain = domain_uuid
		req.target_uri = dest
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_undefine( self, node_uri, domain_uuid, drives ):
		req = protocol.Request_DOMAIN_UNDEFINE()
		req.uri = node_uri
		req.domain = domain_uuid
		req.volumes = drives
		try:
			self.send(req.pack())
			return self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_save(self, node_uri, domain_uuid):
		req = protocol.Request_DOMAIN_SAVE()
		req.uri = node_uri
		req.domain = domain_uuid
		snapshot_dir = umc.registry.get( 'uvmm/pool/default/path', '/var/lib/libvirt/images' )
		req.statefile = os.path.join( snapshot_dir, '%s.snapshot' % domain_uuid )
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_restore(self, node_uri, domain_uuid):
		req = protocol.Request_DOMAIN_RESTORE()
		req.uri = node_uri
		req.domain = domain_uuid
		snapshot_dir = umc.registry.get( 'uvmm/pool/default/path', '/var/lib/libvirt/images' )
		req.statefile = os.path.join( snapshot_dir, '%s.snapshot' % domain_uuid )
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_snapshot_create(self, node_uri, domain_uuid, snapshot_name):
		"""Create new snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_CREATE()
		req.uri = node_uri
		req.domain = domain_uuid
		req.snapshot = snapshot_name
		try:
			self.send(req.pack())
			response = self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_snapshot_revert(self, node_uri, domain_uuid, snapshot_name):
		"""Revert to snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_REVERT()
		req.uri = node_uri
		req.domain = domain_uuid
		req.snapshot = snapshot_name
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

	def domain_snapshot_delete(self, node_uri, domain_uuid, snapshot_name):
		"""Delete snapshot of domain."""
		req = protocol.Request_DOMAIN_SNAPSHOT_DELETE()
		req.uri = node_uri
		req.domain = domain_uuid
		req.snapshot = snapshot_name
		try:
			self.send(req.pack())
			response = self.recv_blocking()
		except UvmmError, e:
			raise

	def storage_pools(self, node_uri):
		"""Get pools of node."""
		req = protocol.Request_STORAGE_POOLS(uri=node_uri)
		try:
			self.send(req.pack())
			response = self.recv_blocking()
			return response.data
		except UvmmError, e:
			raise

	def storage_pool_volumes( self, node_uri, pool, type = None ):
		req = protocol.Request_STORAGE_VOLUMES()
		req.uri = node_uri
		req.pool = pool
		req.type = type
		try:
			self.send(req.pack())
			response = self.recv_blocking()
			return response.data
		except UvmmError, e:
			return []

	def storage_volumes_destroy( self, node_uri, volumes ):
		req = protocol.Request_STORAGE_VOLUMES_DESTROY()
		req.uri = node_uri
		req.volumes = volumes
		try:
			self.send(req.pack())
			self.recv_blocking()
		except UvmmError, e:
			raise

if __name__ == '__main__':
	import doctest
	doctest.testmod()

	notifier.init()

	notifier.timer_add( 1000, lambda: True )
	c = Client()
	import pprint
	pprint.pprint(c.get_node_tree())
	notifier.loop()
