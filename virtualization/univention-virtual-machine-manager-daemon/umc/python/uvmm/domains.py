#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2011 Univention GmbH
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

import os
import socket

from univention.lib.i18n import Translation

from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import MODULE_ERR_COMMAND_FAILED

from univention.uvmm.protocol import Data_Domain, Disk, Graphic, Interface
# for urlparse extensions
from univention.uvmm import helpers
import urlparse

from notifier import Callback

from .tools import object2dict, MemorySize

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Domains( object ):
	STATES = ( 'NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED' )

	def domain_query( self, request ):
		"""Returns a list of domains matching domainPattern on the nodes matching nodePattern.

		options: { 'nodepattern': <node name pattern>, 'domainPattern' : <domain pattern> }

		return: { 'id': <domain uri>, 'name' : <name>, 'nodeName' : <node>, 'mem' : <ram>, 'state' : <state>, 'cpu_usage' : <percentage>, 'type' : 'domain' }, ... ], ... }
		"""

		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result

			if success:
				domain_list = []
				for node_uri, domains in data.items():
					uri = urlparse.urlsplit( node_uri )
					for domain in domains:
						domain_uri = '%s#%s' % ( node_uri, domain[ 'uuid' ] )
						domain_list.append( { 'id' : domain_uri, 'label' : domain[ 'name' ], 'nodeName' : uri.netloc, 'state' : domain[ 'state' ], 'type' : 'domain',
											  'mem' : domain[ 'mem' ], 'cpuUsage' : domain[ 'cpu_usage' ], 'vnc' : domain[ 'vnc' ], 'suspended' : bool( domain[ 'suspended' ] ) } )
				self.finished( request.id, domain_list )
			else:
				self.finished( request.id, None, str( data ), status = MODULE_ERR_COMMAND_FAILED )

		self.uvmm.send( 'DOMAIN_LIST', Callback( _finished, request ), uri = request.options.get( 'nodePattern', '*' ), pattern = request.options.get( 'domainPattern', '*' ) )

	def domain_get( self, request ):
		"""Returns details about a domain domainUUID.

		options: { 'domainURI': <domain uri> }

		return:
		"""
		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result
			if not success:
				self.finished( request.id, None, message = str( data ), status = MODULE_ERR_COMMAND_FAILED )
				return

			node_uri = urlparse.urlsplit( request.options[ 'domainURI' ] )
			uri, uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
			json = object2dict( data )
			## re-arrange a few attributes for the frontend
			# RAM
			json[ 'maxMem' ] = MemorySize.num2str( json[ 'maxMem' ] )
			# disks
			for disk in json[ 'disks' ]:
				if disk[ 'type' ] != Disk.TYPE_BLOCK:
					disk[ 'volumeFilename' ] = os.path.basename( disk[ 'source' ] )
					disk[ 'pool' ] = self.get_pool_name( uri, os.path.dirname( disk[ 'source' ] ) )
				else:
					disk[ 'volumeFilename' ] = disk[ 'source' ]
					disk[ 'pool' ] = None
				disk[ 'paravirtual' ] = disk[ 'target_bus' ] in ( 'virtio', 'xen' )
				disk[ 'volumeType' ] = disk[ 'type' ]
				if isinstance( disk[ 'size' ], ( int, long ) ):
					disk[ 'size' ] = MemorySize.num2str( disk[ 'size' ] )

			# graphics
			if json[ 'graphics' ]:
				try:
					json[ 'vnc' ] = True
					json[ 'kblayout' ] = json[ 'graphics' ][ 0 ][ 'keymap' ]
					json[ 'vnc_remote' ] = json[ 'graphics' ][ 0 ][ 'listen' ] == '0.0.0.0'
					# vnc_password will not be send to frontend
					port = int( json[ 'graphics' ][ 0 ][ 'port' ] )
					if port == -1:
						raise ValueError
					VNC_LINK_BY_NAME, VNC_LINK_BY_IPV4, VNC_LINK_BY_IPV6 = range(3)
					vnc_link_format = VNC_LINK_BY_IPV4
					if vnc_link_format == VNC_LINK_BY_IPV4:
						addrs = socket.getaddrinfo( node_uri.netloc, port, socket.AF_INET )
						(family, socktype, proto, canonname, sockaddr) = addrs[0]
						host = sockaddr[0]
					elif vnc_link_format == VNC_LINK_BY_IPV6:
						addrs = socket.getaddrinfo( node_uri.netloc, port, socket.AF_INET6 )
						(family, socktype, proto, canonname, sockaddr) = addrs[0]
						host = '[%s]' % sockaddr[0]
					json[ 'vncHost' ] = host
					json[ 'vncPort' ] = port
				except ValueError: # port is not valid
					json[ 'vncHost' ] = None
					json[ 'vncPort' ] = None

			# annotations
			for key in json[ 'annotations' ]:
				if key == 'uuid':
					continue
				json[ key ] = json[ 'annotations' ][ key ]

			# profile (MUST be after mapping annotations)
			profile_dn = json.get( 'profile' )
			profile = None
			if profile_dn:
				for dn, pro in self.profiles:
					if dn == profile_dn:
						profile = pro
						break
				if profile:
					json[ 'profileData' ] = object2dict( profile )

			# type
			json[ 'type' ] = '%(domain_type)s-%(os_type)s' % json

			MODULE.info( 'Got domain description: success: %s, data: %s' % ( success, json ) )
			self.finished( request.id, json )

		self.required_options( request, 'domainURI' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_INFO', Callback( _finished, request ), uri = node_uri, domain = domain_uuid )

	def _create_disks( self, node_uri, disks, domain_info ):
		drives = []

		uri = urlparse.urlsplit( node_uri )
		for disk in disks:
			drive = Disk()
			drive.device = disk[ 'device' ]
			drive.driver_type = disk[ 'driver_type' ]
			pool_path = self.get_pool_path( node_uri, disk.get( 'pool' ) )
			file_pool = self.is_file_pool( node_uri, disk.get( 'pool' ) )

			if pool_path:
				drive.source = os.path.join( pool_path, disk[ 'volumeFilename' ] )
			elif not file_pool and disk.get( 'volumeType', Disk.TYPE_BLOCK ) and disk[ 'volumeFilename' ]:
				drive.source = disk[ 'volumeFilename' ]
			elif 'source' in disk and disk[ 'source' ]:
				drive.source = disk[ 'source' ]
			else:
				raise ValueError( _( 'No valid source for disk "%s" found' ) % drive.device )

			if file_pool:
				drive.type = Disk.TYPE_FILE
			else:
				drive.type = Disk.TYPE_BLOCK
				drive.target_bus = 'ide'
				if 'source' in disk and disk[ 'source' ]:
					drive.source = disk[ 'source' ]
				else:
					drive.source = disk[ 'volumeFilename' ]

			driver_pv = None
			if drive.device in ( Disk.DEVICE_DISK, Disk.DEVICE_CDROM ):
				driver_pv = disk.get( 'paravirtual', False ) # by default no paravirtual devices
				if drive.device == Disk.DEVICE_CDROM:
					drive.driver_type = Disk.TYPE_RAW # ISOs need driver/@type='raw'
			elif drive.device == Disk.DEVICE_FLOPPY:
				drive.target_bus = 'fdc'
			else:
				raise ValueError('Invalid drive-type "%s"' % drive.device)

			if uri.scheme.startswith( 'qemu' ):
				drive.driver = 'qemu'
				if driver_pv and drive.device != Disk.DEVICE_FLOPPY and drive.type != Disk.TYPE_BLOCK:
					drive.target_bus = 'virtio'
			elif uri.scheme.startswith( 'xen' ):
				pv_domain = domain_info.os_type == 'xen'
				if driver_pv and drive.device != Disk.DEVICE_FLOPPY and drive.type != Disk.TYPE_BLOCK:
					disk.target_bus = 'xen'
				elif pv_domain and not driver_pv:
					# explicitly set ide bus
					drive.target_bus = 'ide'
				# block devices of para-virtual xen instances must use bus xen
				if pv_domain and drive.type == Disk.TYPE_BLOCK:
					drive.target_bus = 'xen'
				# Since UCS 2.4-2 Xen 3.4.3 contains the blktab2 driver
				# from Xen 4.0.1
				if file_pool:
					# Use tapdisk2 by default, but not for empty CDROM drives
					if drive.source is not None and ucr.is_true( 'uvmm/xen/images/tap2', True ):
						drive.driver = 'tap2'
						drive.driver_type = 'aio'
						# if drive.type == Disk.TYPE_RAW:
						# 	drive.driver_type = 'aio'
					else:
						drive.driver = 'file'
						drive.driver_type = None # only raw support
				else:
					drive.driver = 'phy'
			else:
				raise ValueError( 'Unknown virt-tech "%s"' % node_uri )

			if disk[ 'size' ]:
				drive.size = MemorySize.str2num( disk[ 'size' ], unit = 'MB' )

			drives.append( drive )

		return drives

	def domain_add( self, request ):
		"""Creates a new domain on nodeURI.

		options: { 'nodeURI': <node uri>, 'domain' : {} }

		return:
		"""
		self.required_options( request, 'nodeURI', 'domain' )

		domain = request.options.get( 'domain' )

		domain_info = Data_Domain()
		# when we edit a domain there must be a UUID
		if 'domainURI' in domain:
			node_uri, domain_uuid = urlparse.urldefrag( domain[ 'domainURI' ] )
			domain_info.uuid = domain_uuid

		profile = None
		if not domain_info.uuid:
			profile_dn = domain.get( 'profile' )
			for dn, pro in self.profiles:
				if dn == profile_dn:
					profile = pro
					break
			else:
				raise UMC_OptionTypeError( _( 'Unknown profile given' ) )
			domain_info.annotations[ 'profile' ] = profile_dn
			domain_info.annotations[ 'os' ] = getattr( profile, 'os' )

		domain_info.name = domain[ 'name' ]
		if 'arch' in domain:
			domain_info.arch = domain[ 'arch' ]
		elif profile:
			domain_info.arch = profile.arch
		else:
			raise UMC_CommandError( 'Could not determine architecture for domain' )

		if domain_info.arch == 'automatic':
			success, node_list = self.uvmm.send( 'NODE_LIST', None, group = 'default', pattern = request.options[ 'nodeURI' ] )
			if not success:
				raise UMC_CommandError( _( 'Failed to retrieve details for the server %(nodeURI)s' ) % request.optiond )
			if not node_list:
				raise UMC_CommandError( _( 'Unknown physical server %(nodeURI)s' ) % request.options )
			archs = set( [ t.arch for t in node_list[ 0 ].capabilities ] )
			if 'x86_64' in archs:
				domain_info.arch = 'x86_64'
			else:
				domain_info.arch = 'i686'

		if 'type' in domain:
			try:
				domain_info.domain_type, domain_info.os_type = domain['type'].split( '-' )
			except ValueError:
				domain_info.domain_type, domain_info.os_type = ( None, None )

		if  domain_info.domain_type is None or domain_info.os_type is None:
			if profile:
				domain_info.domain_type, domain_info.os_type = profile.virttech.split( '-' )
			else:
				raise UMC_CommandError( 'Could not determine virtualisation technology for domain' )

		# check configuration for para-virtualized machines
		if domain_info.os_type == 'xen':
			if profile and getattr( profile, 'advkernelconf', None ) != True: # use pyGrub
				domain_info.bootloader = '/usr/bin/pygrub'
				domain_info.bootloader_args = '-q' # Bug #19249: PyGrub timeout
			else:
				domain_info.kernel = domain['kernel']
				domain_info.cmdline = domain['cmdline']
				domain_info.initrd = domain['initrd']
		# memory
		domain_info.maxMem = MemorySize.str2num( domain['maxMem'], unit = 'MB' )

		# CPUs
		try:
			domain_info.vcpus = int( domain[ 'vcpus' ] )
		except ValueError:
			raise UMC_OptionTypeError( 'vcpus must be a number' )

		# boot devices
		if 'boot' in domain:
			domain_info.boot = domain[ 'boot' ]
		elif profile:
			domain_info.boot = getattr( profile, 'bootdev', None )
		else:
			raise UMC_CommandError( 'Could not determine the list of boot devices for domain' )

		# VNC
		if domain[ 'vnc' ]:
			gfx = Graphic()
			if domain.get( 'vnc_remote', False ):
				gfx.listen = '0.0.0.0'
			else:
				gfx.listen = None
			if 'kblayout' in domain:
				gfx.keymap = domain[ 'kblayout' ]
			elif profile:
				gfx.keymap = profile.kblayout
			else:
				raise UMC_CommandError( 'Could not determine the keyboard layout for the VNC access' )
			gfx.passord = domain.get( 'vnc_password', None )
			domain_info.graphics = [gfx,]

		# annotations
		domain_info.annotations[ 'os' ] = domain.get( 'os', '' )
		domain_info.annotations[ 'description' ] = domain.get( 'description', '' )
		domain_info.annotations[ 'contact' ] = domain.get( 'contact', '' )

		# RTC offset
		domain_info.rtc_offset = domain.get( 'rtc_offset', '' )

		# drives
		domain_info.disks = self._create_disks( request.options[ 'nodeURI' ], domain[ 'disks' ], domain_info )
		verify_device_files( domain_info )
		# on _new_ PV machines we should move the CDROM drive to first position
		if domain_info.uuid is None and domain_info.os_type == 'xen':
			non_disks, disks = [], []
			for dev in domain_info.disks:
				if dev.device == Disk.DEVICE_DISK:
					disks.append( dev )
				else:
					non_disks.append( dev )
			domain_info.disks = non_disks + disks

		# network interface
		domain_info.interfaces = []
		for interface in domain[ 'interfaces' ]:
			iface = Interface()
			iface.source = interface[ 'source' ]
			iface.model = interface[ 'model' ]
			iface.mac_address = interface.get( 'mac_address', None )
			# if  domain_info.os_type == 'hvm':
			# 	if domain_info.domain_type == 'xen':
			# 		iface.model = 'netfront'
			# 	elif domain_info.domain_type in ( 'kvm', 'qemu' ):
			# 		iface.model = 'virtio'
			domain_info.interfaces.append( iface )

		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result

			json = object2dict( data )
			MODULE.info( 'New domain: success: %s, data: %s' % ( success, json ) )
			if success:
				self.finished( request.id, json )
			else:
				self.finished( request.id, None, message = str( data ), status = MODULE_ERR_COMMAND_FAILED )

		self.uvmm.send( 'DOMAIN_DEFINE', Callback( _finished, request ), uri = request.options[ 'nodeURI' ], domain = domain_info )

	def domain_put( self, request ):
		"""Modifies a domain domainUUID on node nodeURI.

		options: { 'domainURI': <domain uri>, 'domain' : {} }

		return: 
		"""
		self.domain_add( request )

	def domain_state( self, request ):
		"""Set the state a domain domainUUID on node nodeURI.

		options: { 'domainURI': <domain uri>, 'domainState': (RUN|SHUTDOWN|PAUSE|RESTART|SUSPEND) }

		return: 
		"""
		self.required_options( request, 'domainURI', 'domainState' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		MODULE.info( 'nodeURI: %s, domainUUID: %s' % ( node_uri, domain_uuid ) )
		if request.options[ 'domainState' ] not in self.DOMAIN_STATES:
			raise UMC_OptionTypeError( _( 'Invalid domain state' ) )
		self.uvmm.send( 'DOMAIN_STATE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, state = request.options[ 'domainState' ] )

	def domain_migrate( self, request ):
		"""Migrates a domain from sourceURI to targetURI.

		options: { 'domainURI': <domain uri>, 'targetNodeURI': <target node uri> }

		return: 
		"""
		self.required_options( request, 'domainURI', 'targetNodeURI' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_MIGRATE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, target_uri = request.options[ 'targetNodeURI' ] )

	def domain_clone( self, request ):
		"""Clones an existing domain.

		options: { 'domainURI': <domain uri>, 'cloneName': <name of clone>, 'macAddress' : (clone|auto) }

		return: 
		"""
		self.required_options( request, 'domainURI', 'cloneName' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_CLONE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, name = request.options[ 'cloneName' ], subst = { 'mac' : request.options.get( 'macAddress', 'clone' ) } )

	def domain_remove( self, request ):
		"""Removes a domain. Optional a list of volumes can bes specified that should be removed

		options: { 'domainURI': <domain uri>, 'volumes' : [ { 'pool' : <pool name>, 'volumeFilename' : <filename> }, ... ] }

		return: 
		"""
		self.required_options( request, 'domainURI', 'volumes' )
		volume_list = []
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )

		for vol in request.options[ 'volumes' ]:
			path = self.get_pool_path( node_uri, vol[ 'pool' ] )
			if not path:
				MODULE.warn( 'Could not find volume %(volumeFilename)s. The pool %(pool)s is not known' % vol )
				continue
			volume_list.append( os.path.join( path, vol[ 'volumeFilename' ] ) )
		self.uvmm.send( 'DOMAIN_UNDEFINE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, volumes = volume_list )

class Bus( object ):
	"""Periphery bus like IDE-, SCSI-, Xen-, VirtIO- und FDC-Bus."""
	def __init__( self, name, prefix, default = False, unsupported = ( Disk.DEVICE_FLOPPY, ) ):
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

def verify_device_files( domain_info ):
	if domain_info.domain_type == 'xen' and domain_info.os_type == 'xen':
		busses = ( Bus( 'ide', 'hd%s' ), Bus( 'xen', 'xvd%s', default = True ), Bus( 'virtio', 'vd%s' ) )
	else:
		busses = ( Bus( 'ide', 'hd%s', default = True ), Bus( 'xen', 'xvd%s' ), Bus( 'virtio', 'vd%s' ), Bus( 'fdc', 'fd%s', default = True, unsupported = ( Disk.DEVICE_DISK, Disk.DEVICE_CDROM ) ) )

	for bus in busses:
		bus.attach( domain_info.disks )

	for dev in domain_info.disks:
		for bus in busses:
			if bus.connect( dev ):
				break

