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

from univention.lib.i18n import Translation

from univention.management.console.log import MODULE

from univention.uvmm.protocol import Data_Domain, Disk, Graphic, Interface
# for urlparse extensions
from univention.uvmm import helpers
import urlparse

from notifier import Callback

from .tools import object2dict, MemorySize

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Domains( object ):
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
											  'mem' : domain[ 'mem' ], 'cpuUsage' : domain[ 'cpu_usage' ] } )
			else:
				domain_list = data
			self.finished( request.id, domain_list, success = success )

		self.uvmm.send( 'DOMAIN_LIST', Callback( _finished, request ), uri = request.options.get( 'nodePattern', '*' ), pattern = request.options.get( 'domainPattern', '*' ) )

	def domain_get( self, request ):
		"""Returns details about a domain domainUUID.

		options: { 'domainURI': <domain uri> }

		return: { 'success' : (True|False), 'data' : <details> }
		"""
		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result

			json = object2dict( data, convert_attrs = ( 'graphics', 'interfaces', 'disks' )  )
			MODULE.info( 'Got domain description: success: %s, data: %s' % ( success, json ) )
			self.finished( request.id, { 'success' : success, 'data' : json } )

		self.required_options( request, 'domainURI' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_INFO', Callback( _finished, request ), uri = node_uri, domain = domain_uuid )

	def domain_add( self, request ):
		"""Creates a new domain on nodeURI.

		options: { 'nodeURI': <node uri>, 'domain' : {} }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'nodeURI', 'domain' )

		domain = request.options.get( 'domain' )

		# profile_dn = domain[ '$profile$' ]
		# profile = None
		# for dn, pro in self.profiles:
		# 	if dn == profile_dn:
		# 		profile = pro
		# 		break
		# if profile is None:
		# 	raise UMC_OptionTypeError( _( 'Unknown profile given' ) )

		# domain_info = Data_Domain()
		# domain_info.name = domain[ 'name' ]
		# domain_info.arch = domain[ 'arch' ]
		# domain_info.domain_type, domain_info.os_type = domain['type'].split( '-' )
		# # check configuration for para-virtualized machines
		# if domain_info.os_type == 'xen':
		# 	if profile.advkernelconf != True: # use pyGrub
		# 		domain_info.bootloader = '/usr/bin/pygrub'
		# 		domain_info.bootloader_args = '-q' # Bug #19249: PyGrub timeout
		# 	else:
		# 		domain_info.kernel = domain['kernel']
		# 		domain_info.cmdline = domain['cmdline']
		# 		domain_info.initrd = domain['initrd']
		# # memory
		# domain_info.maxMem = MemorySize.str2num( domain['memory'], unit = 'MB' )
		# # CPUs
		# domain_info.vcpus = domains[ 'cpus' ]
		# # boot devices
		# if domain[ 'boot' ]:
		# 	domain_info.boot = domain[ 'boot' ]
		# # VNC
		# if domain[ 'vnc' ]:
		# 	gfx = Graphic()
		# 	gfx.listen = '0.0.0.0'
		# 	gfx.keymap = domain[ 'kblayout' ]
		# 	domain_info.graphics = [gfx,]
		# # annotations
		# domain_info.annotations[ 'os' ] = domain[ 'os' ]
		# domain_info.annotations[ 'description' ] = domain[ 'description' ]
		# # RTC offset
		# domain_info.rtc_offset = domain[ 'rtc_offset' ]
		# # drives
		# domain_info.disks = self.drives
		# self.uvmm._verify_device_files(domain_info)
		# # on PV machines we should move the CDROM drive to first position
		# if domain_info.os_type in ( 'linux', 'xen' ):
		# 	non_disks, disks = [], []
		# 	for dev in domain_info.disks:
		# 		if dev.device == uvmmp.Disk.DEVICE_DISK:
		# 			disks.append(dev)
		# 		else:
		# 			non_disks.append(dev)
		# 	domain_info.disks = non_disks + disks
		# # network interface
		# if object.options[ 'interface' ]:
		# 	iface = uvmmp.Interface()
		# 	iface.source = object.options[ 'interface' ]
		# 	if object.options[ 'pvinterface' ] == '1' and domain_info.os_type == 'hvm':
		# 		if domain_info.domain_type == 'xen':
		# 			iface.model = 'netfront'
		# 		elif domain_info.domain_type in ( 'kvm', 'qemu' ):
		# 			iface.model = 'virtio'
		# 	domain_info.interfaces = [iface,]

		# self.finished( request.id )

	def domain_put( self, request ):
		"""Modifies a domain domainUUID on node nodeURI.

		options: { 'nodeURI': <node uri>, 'domainUUID' : <domain UUID>, 'domain' : {} }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.finished( request.id )

	def domain_state( self, request ):
		"""Set the state a domain domainUUID on node nodeURI.

		options: { 'domainURI': <domain uri>, 'domainState': (RUN|SHUTDOWN|PAUSE|RESTART) }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'domainURI', 'domainState' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )

		if request.options[ 'domainState' ] not in Instance.DOMAIN_STATES:
			raise UMC_OptionTypeError( _( 'Invalid domain state' ) )
		self.uvmm.send( 'DOMAIN_STATE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, state = request.options[ 'domainState' ] )

	def domain_migrate( self, request ):
		"""Migrates a domain from sourceURI to targetURI.

		options: { 'domainURI': <domain uri>, 'targetNodeURI': <target node uri> }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'domainURI', 'targetNodeURI' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_MIGRATE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, target_uri = request.options[ 'targetNodeURI' ] )

	def domain_remove( self, request ):
		"""Removes a domain. Optional a list of volumes can bes specified that should be removed

		options: { 'domainURI': <domain uri> }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'domainURI' )
		node_uri, domain_uuid = urlparse.urldefrag( request.options[ 'domainURI' ] )
		self.uvmm.send( 'DOMAIN_UNDEFINE', Callback( self._thread_finish, request ), uri = node_uri, domain = domain_uuid, volumes = request.options[ 'volumes' ] )

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

def verify_device_files( self, domain_info ):
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

