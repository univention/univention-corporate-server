#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  node handler
#
# Copyright 2010 Univention GmbH
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
"""UVMM node handler.

This module implements functions to handle nodes and domains. This is independent from the on-wire-format.
"""

import libvirt
import time
import socket
import logging
from xml.dom.minidom import getDOMImplementation, parseString
import math
from helpers import TranslatableException, N_ as _
from uvmm_ldap import ldap_annotation, LdapError, ldap_modify
import univention.admin.uexceptions
import traceback
from univention.uvmm.eventloop import *
import threading
from storage import create_storage_volume, destroy_storage_volumes, get_all_storage_volumes, StorageError

logger = logging.getLogger('uvmmd.node')

STATES = ['NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED']

class NodeError(TranslatableException):
	"""Error while handling node."""
	pass

class StoragePool(object):
	"""Container for storage pool statistics."""
	def __init__(self, pool):
		self.uuid = pool.UUIDString()
		self.name = pool.name()
		self.update(pool)
	def __eq__(self, other):
		return self.uuid == other.uuid;
	def update(self, pool):
		"""Update statistics."""
		state, self.capacity, allocation, self.available = pool.info()

def _map( dictionary, id = None, name = None ):
	"""Map id to name or reverse using the dictionary."""
	if id != None and id in dictionary:
		return dictionary[ id ]
	if name:
		for key, value in dictionary.items():
			if name == value:
				return key

	return ''

class Disk( object ):
	'''Container for disk objects'''
	( DEVICE_DISK, DEVICE_CDROM, DEVICE_FLOPPY ) = range( 3 )
	DEVICE_MAP = { DEVICE_DISK : 'disk', DEVICE_CDROM : 'cdrom', DEVICE_FLOPPY : 'floppy' }
	( TYPE_FILE, ) = range( 1 )
	TYPE_MAP = { TYPE_FILE : 'file' }
	def __init__( self ):
		self.type = Disk.TYPE_FILE
		self.device = Disk.DEVICE_DISK
		self.driver = 'file'
		self.source = ''
		self.readonly = False
		self.target_dev = ''
		self.target_bus = 'ide'

	@staticmethod
	def map_device( id = None, name = None ):
		return _map( Disk.DEVICE_MAP, id, name )

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Disk.TYPE_MAP, id, name )

	def __str__( self ):
		return 'Disk(%s,%s): %s, %s' % ( Disk.map_device( id = self.device ), Disk.map_type( id = self.type ), self.source, self.target_dev )

class Interface( object ):
	'''Container for interface objects'''
	( TYPE_BRIDGE, ) = range( 1 )
	TYPE_MAP = { TYPE_BRIDGE : 'bridge' }
	def __init__( self ):
		self.type = Interface.TYPE_BRIDGE
		self.mac_address = None
		self.source = None
		self.target = None
		self.script = None

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Interface.TYPE_MAP, id, name )

	def __str__( self ):
		return 'Interface(%s): %s, %s' % ( Interface.map_type( id = self.type ), self.mac_address, self.source )

class Graphic( object ):
	'''Container for graphic objects'''
	( TYPE_VNC, ) = range( 1 )
	TYPE_MAP = { TYPE_VNC : 'vnc' }
	def __init__( self ):
		self.type = Graphic.TYPE_VNC
		self.port = -1
		self.autoport = True
		self.keymap = 'de'
		self.listen = None

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Graphic.TYPE_MAP, id, name )

	def __str__( self ):
		return 'Graphic(%s): %s, %s' % ( Graphic.map_type( id = self.type ), self.port, self.keymap )

class DomainTemplate(object):
	'''Container for node capability.'''

	@staticmethod
	def list_from_xml(xml):
		"""Convert XML to list.
		>>> t = DomainTemplate.list_from_xml(TEST_CAPABILITIES)
		>>> len(t)
		1
		>>> t[0].virt_tech
		u'hvm'
		>>> t[0].arch
		u'i686'
		>>> t[0].emulator
		u'/usr/bin/qemu'
		>>> t[0].machines
		[u'pc']
		>>> t[0].domains
		[u'qemu']
		>>> t[0].features
		['pae', u'acpi', u'apic']
		"""
		doc = parseString(xml)
		result = []
		for guest in doc.getElementsByTagName('guest'):
			virt_tech = guest.getElementsByTagName('os_type')[0].firstChild.nodeValue
			f_names = []
			features = guest.getElementsByTagName('features')
			if features:
				c = features[0].firstChild
				while c:
					if c.nodeType == 1:
						if c.nodeName == 'pae':
							if 'nonpae' not in f_names:
								f_names.append('pae')
						elif c.nodeName == 'nonpae':
							if 'pae' not in f_names:
								f_names.append('nonpae')
						elif c.getAttribute('default') == 'on':
							f_names.append(c.nodeName)
					c = c.nextSibling
			for arch in guest.getElementsByTagName('arch'):
				dom = DomainTemplate(virt_tech, arch, f_names)
				result.append(dom)
		return result

	def __init__(self, virt_tech, arch, features):
		self.virt_tech = virt_tech
		self.arch = arch.getAttribute('name')
		self.emulator = arch.getElementsByTagName('emulator')[0].firstChild.nodeValue
		try:
			self.loader = arch.getElementsByTagName('loader')[0].firstChild.nodeValue
		except:
			self.loader = None
		self.machines = [m.firstChild.nodeValue for m in arch.getElementsByTagName('machine')]
		self.domains = [d.getAttribute('type') for d in arch.getElementsByTagName('domain')]
		self.features = features

	def __str__(self):
		return 'DomainTemplate(type=%s arch=%s): %s, %s, %s, %s, %s' % (self.virt_tech, self.arch, self.emulator, self.loader, self.machines, self.domains, self.features)

class Domain(object):
	"""Container for domain statistics."""
	CPUTIMES = (10, 60, 5*60) # 10s 60s 5m
	def __init__(self, domain):
		self.uuid = domain.UUIDString()
		self.state = 0
		self.maxMem = 0L
		self.curMem = 0L
		self.vcpus = 1
		self.arch = 'i686'
		self.virt_tech = domain.OSType()
		self.kernel = ''
		self.cmdline = ''
		self.initrd = ''
		self.boot = ['hd', 'cdrom']
		self.interfaces = []
		self.disks = []
		self.graphics = []
		self._time_stamp = 0.0
		self._time_used = 0L
		self.cputime = [0.0, 0.0, 0.0] # percentage in last 10s 60s 5m
		self.annotations = {}
		self.update(domain)

	def __eq__(self, other):
		return self.uuid == other.uuid;

	def update(self, domain):
		"""Update statistics."""
		self.name = domain.name()
		for i in range(5):
			info = domain.info()
			if info[0] != libvirt.VIR_DOMAIN_NOSTATE: # ignore =?= libvirt's transient error
				break
			time.sleep(1)
		else:
			logger.warning('No state for %s: %s' % (self.name, info))
			return

		self.state, maxMem, curMem, self.vcpus, runtime = info

		if domain.ID() == 0 and domain.connect().getURI().startswith('xen'):
			# xen://#Domain-0 always reports (1<<32)-1
			maxMem = domain.connect().getInfo()[1]
			self.maxMem = long(maxMem) << 20 # GiB
		else:
			self.maxMem = long(maxMem) << 10 # KiB

		if self.state in (libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			self.curMem = 0L
			delta_used = 0L
			self._time_used = 0L
		else:
			self.curMem = long(curMem) << 10 # KiB
			delta_used = runtime - self._time_used # running [ns]
			self._time_used = runtime

		# Calculate historical CPU usage
		# http://www.teamquest.com/resources/gunther/display/5/
		now = time.time()
		if self._time_stamp > 0.0:
			delta_t = now - self._time_stamp # wall clock [s]
			usage = delta_used / delta_t / self.vcpus / 1000000 # ms
			for i in range(len(Domain.CPUTIMES)):
				if delta_t < Domain.CPUTIMES[i]:
					e = math.exp(-1.0 * delta_t / Domain.CPUTIMES[i])
					self.cputime[i] *= e
					self.cputime[i] += (1.0 - e) * usage
				else:
					self.cputime[i] = usage
		self._time_stamp = now
		self.update_expensive(domain)

	def update_expensive(self, domain):
		"""Update statistics."""
		self.xml2obj( domain )
		try:
			self.annotations = ldap_annotation(self.uuid)
		except LdapError, e:
			self.annotations = {}

	def xml2obj( self, domain ):
		"""Parse XML into python object."""
		doc = parseString( domain.XMLDesc( 0 ) )
		devices = doc.getElementsByTagName( 'devices' )[ 0 ]

		os = doc.getElementsByTagName( 'os' )
		if os:
			os = os[ 0 ]
			type = os.getElementsByTagName( 'type' )
			if type and type[ 0 ].firstChild and type[ 0 ].firstChild.nodeValue:
				self.virt_tech = type[ 0 ].firstChild.nodeValue
				if type[ 0 ].hasAttribute( 'arch' ):
					self.arch = type[ 0 ].getAttribute( 'arch' )
			kernel = os.getElementsByTagName( 'kernel' )
			if kernel and kernel[ 0 ].firstChild and kernel[ 0 ].firstChild.nodeValue:
				self.kernel = kernel[ 0 ].firstChild.nodeValue
			cmdline = os.getElementsByTagName( 'cmdline' )
			if cmdline and cmdline[ 0 ].firstChild and cmdline[ 0 ].firstChild.nodeValue:
				self.cmdline = cmdline[ 0 ].firstChild.nodeValue
			initrd = os.getElementsByTagName( 'initrd' )
			if initrd and initrd[ 0 ].firstChild and initrd[ 0 ].firstChild.nodeValue:
				self.initrd = initrd[ 0 ].firstChild.nodeValue
			boot = os.getElementsByTagName('boot')
			if boot:
				self.boot = [dev.attributes['dev'].value for dev in boot]

		self.disks = []
		disks = devices.getElementsByTagName( 'disk' )
		for disk in disks:
			dev = Disk()
			dev.type = Disk.map_type( name = disk.getAttribute( 'type' ) )
			dev.device = Disk.map_device( name = disk.getAttribute( 'device' ) )
			source = disk.getElementsByTagName( 'source' )
			if source:
				dev.source = source[ 0 ].getAttribute( 'file' )
			target = disk.getElementsByTagName( 'target' )
			if target:
				dev.target_dev = target[ 0 ].getAttribute( 'dev' )
				dev.target_bus = target[ 0 ].getAttribute( 'bus' )
			if disk.getElementsByTagName( 'readonly' ):
				dev.readonly = True

			self.disks.append( dev )

		self.interfaces = []
		interfaces = devices.getElementsByTagName( 'interface' )
		for iface in interfaces:
			dev = Interface()
			dev.type = Interface.map_type( name = iface.getAttribute( 'type' ) )
			mac = iface.getElementsByTagName( 'mac' )
			if mac:
				dev.mac_address = mac[ 0 ].getAttribute( 'address' )
			source = iface.getElementsByTagName( 'source' )
			if source:
				dev.source = source[ 0 ].getAttribute( 'bridge' )
			script = iface.getElementsByTagName( 'script' )
			if script:
				dev.script = script[ 0 ].getAttribute( 'path' )
			target = iface.getElementsByTagName( 'target' )
			if target:
				dev.target_dev = target[ 0 ].getAttribute( 'dev' )

			self.interfaces.append( dev )

		self.graphics = []
		graphics = devices.getElementsByTagName( 'graphics' )
		for graphic in graphics:
			dev = Graphic()
			dev.type = Graphic.map_type( name = graphic.getAttribute( 'type' ) )
			dev.port = int( graphic.getAttribute( 'port' ) )
			dev.autoport = graphic.getAttribute( 'autoport' )
			if graphic.hasAttribute( 'listen' ):
				dev.listen = graphic.getAttribute( 'listen' )
			dev.autoport = graphic.getAttribute( 'autoport' )
			if dev.autoport.lower() == 'yes':
				dev.autoport = True
			else:
				dev.autoport = False
			dev.keymap = graphic.getAttribute( 'keymap' )
			self.graphics.append( dev )

	def key(self):
		"""Return a unique key for this domain and generation."""
		return hash((self.uuid, self._time_stamp))

class Node(object):
	"""Container for node statistics."""
	def __init__(self, uri):
		self.uri = uri
		self._lock = threading.Lock()
		self.conn = None
		self.storages = {}
		self.domains = {}

		def timer_callback(timer, *opaque):
			try:
				"""Handle regular poll. Also checks connection liveness."""
				logger.debug("timer_callback#%d: %s)" % (timer, self.uri,))
				try:
					self._lock.acquire()
					self.update_autoreconnect()
				finally:
					self._lock.release()
			except Exception, e:
				logger.error("Exception %s: %s" % (e, traceback.format_exc()))
				# don't crash the event handler

		self.timerID = virEventAddTimerImpl(Nodes.IDLE_FREQUENCY, timer_callback, (None,None))

	def update_autoreconnect(self):
		"""(Re-)connect after connection broke."""
		self.last_try = time.time()
		try:
			if self.conn == None:
				self.conn = libvirt.open(self.uri)
				logger.info("Connected to '%s'" % (self.uri,))
				self.update_once()
			self.update()
		except libvirt.libvirtError, e:
			logger.warning("'%s' broken? %s" % (self.uri, e))
			if self.conn != None:
				try:
				  if False: # libvirt FIXME domainEventDeregister SEGVs!!!
					self.conn.domainEventDeregister(self.domainCB)
				except:
					pass
				self.domainCB = None
				try:
					self.conn.close()
				except:
					pass
				self.conn = None

	def __eq__(self, other):
		return (self.uri, self.name) == (other.uri, other.name)

	def __del__(self):
		"""Free Node and deregister callbacks."""
		self.unregister()
		del self.storages
		del self.domains

	def update_once(self):
		"""Update once on (re-)connect."""
		self.name = self.conn.getHostname()
		info = self.conn.getInfo()
		self.phyMem = long(info[1]) << 20 # MiB
		self.cpus = info[2]
		self.cores = info[4:8]
		xml = self.conn.getCapabilities()
		self.capabilities = DomainTemplate.list_from_xml(xml)

		def domain_callback(conn, dom, event, detail, node):
			try:
				"""Handle domain addition, update and removal."""
				eventStrings = ("Added", "Removed", "Started", "Suspended", "Resumed", "Stopped", "Saved", "Restored")
				logger.debug("domain_callback %s(%s) %s %d" % (dom.name(), dom.ID(), eventStrings[event], detail))
				uuid = dom.UUIDString()
				if event == libvirt.VIR_DOMAIN_EVENT_DEFINED:
					domStat = Domain(dom)
					self.domains[uuid] = domStat
				elif event == libvirt.VIR_DOMAIN_EVENT_UNDEFINED:
					if uuid in self.domains:
						del self.domains[uuid]
				else: # VIR_DOMAIN_EVENT_STARTED _SUSPENDED _RESUMED _STOPPED
					try:
						domStat = self.domains[uuid]
						domStat.update( dom )
					except KeyError, e:
						# during migration events are not ordered causal
						pass
			except Exception, e:
				logger.error("Exception %s: %s" % (e, traceback.format_exc()))
				# don't crash the event handler

		self.conn.domainEventRegister(domain_callback, self)
		self.domainCB = domain_callback

	def unregister(self):
		"""Unregister callbacks doing updates."""
		if self.timerID != None:
			virEventRemoveTimerImpl(self.timerID)
			self.timerID = None
		if self.domainCB != None:
			self.conn.domainEventDeregister(self.domainCB)
			self.domainCB = None
		if self.conn != None:
			self.conn.close()
			self.conn = None

	def set_frequency(self, hz):
		"""Set polling frequency for update."""
		virEventUpdateTimerImpl(self.timerID, hz)

	def update(self):
		"""Update node statistics."""
		cached_pools = self.storages.keys()
		for pool_name in self.conn.listStoragePools():
			pool = self.conn.storagePoolLookupByName(pool_name)
			uuid = pool.UUIDString()
			if uuid in self.storages:
				# Update existing pools
				poolStat = self.storages[uuid]
				poolStat.update(pool)
				cached_pools.remove(uuid)
			else:
				# Add new pools
				poolStat = StoragePool(pool)
				self.storages[uuid] = poolStat
		for uuid in cached_pools:
			# Remove obsolete pools
			del self.storages[uuid]

		curMem = 0
		maxMem = 0
		cached_domains = self.domains.keys()
		for dom in [self.conn.lookupByID(id) for id in self.conn.listDomainsID()] + \
			[self.conn.lookupByName(name) for name in self.conn.listDefinedDomains()]:
			uuid = dom.UUIDString()
			if uuid in self.domains:
				# Update existing domains
				domStat = self.domains[uuid]
				domStat.update(dom)
				cached_domains.remove(uuid)
			else:
				# Add new domains
				domStat = Domain(dom)
				self.domains[uuid] = domStat
			curMem += domStat.curMem
			maxMem += domStat.maxMem
		for uuid in cached_domains:
			# Remove obsolete domains
			del self.domains[uuid]
		self.curMem = curMem
		self.maxMem = maxMem
		self.last_update = self.last_try

	def wait_update(self, domain, state_key, timeout=10):
		"""Wait until domain gets updated."""
		while timeout > 0:
			try:
				if state_key != self.domains[domain].key():
					break
			except KeyError, e:
				pass
			time.sleep(1)
			timeout -= 1
		else:
			logger.warning('Timeout waiting for update.')

class Nodes(dict):
	"""Handle registered nodes."""
	IDLE_FREQUENCY = 15*1000; # ms
	USED_FREQUENCY = 10*1000; # ms
	def __init__(self):
		super(Nodes,self).__init__()
		self.frequency = -1
	def __delitem__(self, uri):
		"""x.__delitem__(i) <==> del x[i]"""
		self[uri].unregister()
		super(Node,self).__delitem__(uri)
	def set_frequency(self, hz):
		"""Set polling frequency for update."""
		for node in self.values():
			node.set_frequency(hz)

nodes = Nodes()

def node_add(uri):
	"""Add node to watch list.
	>>> #node_add("qemu:///session")
	>>> #node_add("xen:///")"""
	global nodes
	if uri in nodes:
		raise NodeError(_('Hypervisor "%(uri)s" is already connected.'), uri=uri)

	node = Node(uri)
	nodes[uri] = node

	logger.debug("Hypervisor '%s' added." % (uri,))

def node_remove(uri):
	"""Remove node from watch list."""
	global nodes
	try:
		del nodes[uri]
	except KeyError:
		raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)
	logger.debug("Hypervisor '%s' removed." % (uri,))

def node_query(uri):
	"""Get domain data from node."""
	global nodes
	try:
		node = nodes[uri]
		if node.conn is None:
			raise NodeError(_('Hypervisor "%(uri)s" is unavailable.'), uri=uri)
		return node
	except KeyError:
		raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)

def node_frequency(hz=Nodes.IDLE_FREQUENCY, uri=None):
	"""Set frequency for polling nodes."""
	global nodes
	if uri == None:
		nodes.set_frequency(hz)
	else:
		node = node_query(uri)
		node.set_frequency(hz)

def node_list(group):
	"""Return list of watched nodes."""
	global nodes
	if group == 'default': # FIXME
		return [uri for uri in nodes]
	else:
		return []

def group_list():
	"""Return list of groups for nodes."""
	return ['default'] # FIXME

def domain_define( uri, domain ):
	"""Convert python object to an XML document."""
	node = node_query(uri)
	conn = node.conn

	old_dom = None
	old_stat = None

	impl = getDOMImplementation()
	doc = impl.createDocument( None, 'domain', None )
	elem = doc.createElement( 'name' )
	elem.appendChild( doc.createTextNode( domain.name ) )
	doc.documentElement.appendChild( elem )
	doc.documentElement.setAttribute('type', conn.getType().lower()) # TODO: verify
	if not domain.uuid:
		try:
			old_dom = conn.lookupByName(domain.name)
			domain.uuid = old_dom.UUIDString()
			old_stat = node.domains[domain.uuid].key()
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.name, error=e)
	if domain.uuid:
		elem = doc.createElement( 'uuid' )
		elem.appendChild( doc.createTextNode( domain.uuid ) )
		doc.documentElement.appendChild( elem )
	elem = doc.createElement( 'memory' )
	elem.appendChild( doc.createTextNode( str( domain.maxMem / 1024 ) ) )
	doc.documentElement.appendChild( elem )
	if domain.vcpus:
		elem = doc.createElement('vcpu')
		elem.appendChild( doc.createTextNode(str(domain.vcpus)))
		doc.documentElement.appendChild(elem)

	# find loader
	loader = None
	logger.debug('Searching for loader: %s' % node.capabilities)
	for template in node.capabilities:
		logger.debug('template: %s' % str((template.arch, domain.arch, template.virt_tech, domain.virt_tech)))
		if template.arch == domain.arch and template.virt_tech == domain.virt_tech and template.loader:
			loader = doc.createElement( 'loader' )
			loader.appendChild( doc.createTextNode( template.loader ) )

			if template.features:
				features = doc.createElement('features')
				for f_name in template.features:
					feature = doc.createElement(f_name)
					features.appendChild(feature)
				doc.documentElement.appendChild(features)

	type = doc.createElement( 'type' )
	type.appendChild( doc.createTextNode( domain.virt_tech ) )
	type.setAttribute( 'arch', domain.arch )
	os = doc.createElement( 'os' )
	os.appendChild( type )
	if loader:
		os.appendChild( loader )
		
	if domain.kernel:
		text = doc.createTextNode( domain.kernel )
		kernel = doc.createElement( 'kernel' )
		kernel.appendChild( text )
		os.appendChild( kernel )
	if domain.cmdline:
		text = doc.createTextNode( domain.cmdline )
		cmdline = doc.createElement( 'cmdline' )
		cmdline.appendChild( text )
		os.appendChild( cmdline )
	if domain.initrd:
		text = doc.createTextNode( domain.initrd )
		initrd = doc.createElement( 'initrd' )
		initrd.appendChild( text )
		os.appendChild( initrd )
	if domain.virt_tech == 'hvm':
		for dev in domain.boot: # (hd|cdrom|network|fd)+
			boot = doc.createElement('boot')
			boot.setAttribute('dev', dev)
			os.appendChild(boot)
	
	if False: # FIXME optional
		clock = doc.createElement('clock')
		clock.setAttribute('offset', 'localtime') # FIXME: (utc|localtime|timezone|variable)
		#clock.setAttribute('timezone', '') # @offset='timezone' only
		#clock.setAttribute('adjustment', 0) # @offset='variable' only
		os.appendChild(clock)

	if False: # FIXME optional
		text = doc.createTextNode('destroy') # (destroy|restart|preserve|rename-restart)
		poweroff = doc.createElement('on_poweroff')
		poweroff.appendChild(text)
		doc.appendChild(poweroff)
	if False: # FIXME optional
		text = doc.createTextNode('restart') # (destroy|restart|preserve|rename-restart)
		reboot = doc.createElement('on_reboot')
		reboot.appendChild(text)
		doc.appendChild(reboot)
	if False: # FIXME optional
		text = doc.createTextNode('destroy') # (destroy|restart|preserve|rename-restart)
		crash = doc.createElement('on_crash')
		crash.appendChild(text)
		doc.appendChild(crash)

	doc.documentElement.appendChild( os )
	devices = doc.createElement( 'devices' )
	if False: # FIXME
		text = doc.createTextNode('/usr/lib64/xen/bin/qemu-dm') # FIXME
		emulator = doc.createElement('emulator')
		emulator.appendChild(text)
		os.appendChild(emulator)

	logger.debug('DISKS: %s' % domain.disks)
	for disk in domain.disks:
		logger.debug('DISK: %s' % disk)
		elem = doc.createElement( 'disk' )
		elem.setAttribute( 'type', disk.map_type( id = disk.type ) )
		elem.setAttribute( 'device', disk.map_device( id = disk.device ) )
		devices.appendChild( elem )
		driver = doc.createElement( 'driver' )
		driver.setAttribute( 'name', disk.driver )
		elem.appendChild( driver )
		source = doc.createElement( 'source' )
		source.setAttribute( 'file', disk.source )
		elem.appendChild( source )
		target = doc.createElement( 'target' )
		target.setAttribute( 'dev', disk.target_dev )
		target.setAttribute( 'bus', disk.target_bus )
		elem.appendChild( target )
		if disk.readonly:
			readonly = doc.createElement( 'readonly' )
			elem.appendChild( readonly )

		if disk.device == Disk.DEVICE_DISK:
			try:
				# FIXME: If the volume is outside any pool, ignore error
				create_storage_volume(conn, domain, disk)
			except StorageError, e:
				raise NodeError(e)

	for iface in domain.interfaces:
		logger.debug('INTERFACE: %s' % iface)
		elem = doc.createElement( 'interface' )
		elem.setAttribute( 'type', iface.map_type( id = iface.type ) )
		if iface.mac_address:
			mac = doc.createElement( 'mac' )
			mac.setAttribute( 'address', iface.mac_address )
			elem.appendChild( mac )
		source = doc.createElement( 'source' )
		source.setAttribute( 'bridge', iface.source )
		elem.appendChild( source )
		if iface.script:
			script = doc.createElement( 'script' )
			script.setAttribute( 'path', iface.script )
			elem.appendChild( script )
		if iface.target:
			target = doc.createElement( 'target' )
			target.setAttribute( 'dev', iface.target )
			elem.appendChild( target )
		devices.appendChild( elem )

	for graphic in domain.graphics:
		logger.debug('GRAPHIC: %s' % graphic)
		elem = doc.createElement( 'graphics' )
		elem.setAttribute( 'type', Graphic.map_type( id = graphic.type ) )
		elem.setAttribute( 'port', str( graphic.port ) )
		if graphic.autoport:
			elem.setAttribute( 'autoport', 'yes' )
		else:
			elem.setAttribute( 'autoport', 'no' )
		if graphic.listen:
			elem.setAttribute( 'listen', graphic.listen )
		elem.setAttribute( 'keymap', graphic.keymap )
		devices.appendChild( elem )

	doc.documentElement.appendChild( devices )

	# remove old domain definitions
	if old_dom:
		try:
			old_dom.undefine()
			logger.info('Old domain "%s" removed.' % (domain.name,))
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				raise NodeError(_('Error removing domain "%(domain)s": %(error)s'), domain=domain.name, error=e)
	if domain.uuid:
		try:
			conn.lookupByUUIDString(domain.uuid).undefine()
			logger.info('Old domain "%s" removed.' % (domain.uuid,))
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				raise NodeError(_('Error removing domain "%(domain)s": %(error)s'), domain=domain.uuid, error=e)

	try:
		d = conn.defineXML(doc.toxml())
		domain.uuid = d.UUIDString()
	except libvirt.libvirtError, e:
		raise NodeError(_('Error defining domain "%(domain)s: %(error)s'), domain=domain.name, error=e)
	logger.info('New domain "%s"(%s) defined.' % (domain.name, domain.uuid))

	if domain.annotations:
		try:
			record = ldap_modify(domain.uuid)
			modified = False
			for key, cur_value in record.items():
				if key == 'uuid':
					new_value = domain.uuid
				else:
					new_value = domain.annotations.get(key, cur_value)
				if new_value != cur_value:
					record[key] = new_value
					modified = True
			if modified:
				record.commit()
		except univention.admin.uexceptions.objectExists, e:
			logger.error('Updating LDAP failed: %s %s' % (e, record))

	node.wait_update(domain.uuid, old_stat)
	return domain.uuid

def domain_state(uri, domain, state):
	"""Change running state of domain on node and wait for updated state."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		try:
			TRANSITION = {
					(libvirt.VIR_DOMAIN_RUNNING,  'PAUSE'   ): dom.suspend,
					(libvirt.VIR_DOMAIN_RUNNING,  'RESTART' ): lambda:dom.destroy(None),
					(libvirt.VIR_DOMAIN_RUNNING,  'RUN'     ): None,
					(libvirt.VIR_DOMAIN_RUNNING,  'SHUTDOWN'): dom.destroy,
					(libvirt.VIR_DOMAIN_BLOCKED,  'PAUSE'   ): dom.suspend,
					(libvirt.VIR_DOMAIN_BLOCKED,  'RESTART' ): lambda:dom.destroy(None),
					(libvirt.VIR_DOMAIN_BLOCKED,  'RUN'     ): None,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SHUTDOWN'): dom.destroy,
					(libvirt.VIR_DOMAIN_PAUSED,   'PAUSE'   ): None,
					(libvirt.VIR_DOMAIN_PAUSED,   'RUN'     ): dom.resume,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_CRASHED,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_CRASHED,  'SHUTDOWN'): None, # TODO destroy?
					}
			transition = TRANSITION[(dom_stat.state, state)]
		except KeyError, e:

			cur_state = STATES[dom_stat.state]
			raise NodeError(_('Unsupported state transition %(cur_state)s to %(next_state)s'), cur_state=cur_state, next_state=state)

		if transition:
			transition()
			ignore_states = [libvirt.VIR_DOMAIN_NOSTATE]
			if state == 'RUN':
				ignore_states.append(libvirt.VIR_DOMAIN_PAUSED)
			for t in range(10):
				cur_state = dom.info()[0]
				if cur_state not in ignore_states:
					# xen does not send event, do update explicitly
					dom_stat.state = cur_state
					break
				time.sleep(1)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=e)

def domain_save(uri, domain, statefile):
	"""Save defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom.save(statefile)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error saving domain "%(domain)s": %(error)s'), domain=domain, error=e)

def domain_restore(uri, statefile):
	"""Restore defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		conn.restore(statefile)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error restoring domain "%(domain)s": %(error)s'), domain=domain, error=e)

def domain_undefine(uri, domain, volumes=[]):
	"""Undefine a domain and its volumes on a node."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		if volumes is None:
			volumes = get_all_storage_volumes(conn, dom,)
		destroy_storage_volumes(conn, volumes, ignore_error=True)
		dom.undefine()
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error undefining domain "%(domain)s": %(error)s'), domain=domain, error=e)

def domain_migrate(source_uri, domain, target_uri):
	"""Migrate a domain from node to the target node."""
	try:
		source_node = node_query(source_uri)
		source_conn = source_node.conn
		source_dom = source_conn.lookupByUUIDString(domain)
		for t in range(10):
			source_state = source_dom.info()[0]
			if source_state != libvirt.VIR_DOMAIN_NOSTATE:
				break
			time.sleep(1)
		target_node = node_query(target_uri)
		target_conn = target_node.conn

		if source_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED):
			# running domains are live migrated
			flags = libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_PERSIST_DEST | libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
			target_dom = source_dom.migrate(target_conn, flags, None, None, 0)
		elif source_state in (libvirt.VIR_DOMAIN_SHUTDOWN, libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			# for domains not running their definition is migrated
			xml = source_dom.XMLDesc(0)
			target_conn.defineXML(xml)
			source_dom.undefine()
		elif True or source_state in (libvirt.VIR_DOMAIN_PAUSED):
			raise NodeError(_('Domain "%(domain)s" in state "%(state)s" can not be migrated'), domain=domain, state=STATES[source_state])

		# Updates are handled via the callback mechanism
		del source_node.domains[domain]
		#target_node.domains[domain] = Domain(target_dom)
		for t in range(10):
			if domain not in source_node.domains and domain in target_node.domains:
				break
			time.sleep(1)
		else:
			logger.warning('Domain "%(domain)s" still not migrated from "%(source)s" to "%(target)s"' % {'domain':domain, 'source':source_uri, 'target':target_uri})
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=e)

if __name__ == '__main__':
	TEST_CAPABILITIES = '''<capabilities>
		<host>
			<cpu/>
			<migration_features/>
		</host>
		<guest>
			<os_type>hvm</os_type>
			<arch name='i686'>
				<wordsize>32</wordsize>
				<emulator>/usr/bin/qemu</emulator>
				<machine>pc</machine>
				<domain type='qemu'>
				</domain>
			</arch>
			<features>
				<cpuselection/>
				<pae/>
				<nonpae/>
				<acpi default='on' toggle='yes'/>
				<apic default='on' toggle='no'/>
			</features>
		</guest>
	</capabilities>'''

	import doctest
	doctest.testmod()
