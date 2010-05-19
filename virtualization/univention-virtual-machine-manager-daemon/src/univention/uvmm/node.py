#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  node handler
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
"""UVMM node handler.

This module implements functions to handle nodes and domains. This is independent from the on-wire-format.
"""

import libvirt
import time
import socket
import logging
from xml.dom.minidom import getDOMImplementation, parseString
import math

logger = logging.getLogger('uvmmd.node')

# Create global event loop
from univention.uvmm.eventloop import *
virEventLoopPureStart()
virEventLoopPureRegister()

class NodeError(Exception):
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
		_, self.capacity, _, self.available = pool.info()

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
		self.keymap = 'de-de'

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Graphic.TYPE_MAP, id, name )

	def __str__( self ):
		return 'Graphic(%s): %s, %s' % ( Graphic.map_type( id = self.type ), self.port, self.keymap )

class DomainTemplate(object):
	'''Container for node capability.'''
	@staticmethod
	def list_from_xml(xml):
		doc = parseString(xml)
		result = []
		for guest in doc.getElementsByTagName('guest'):
			os_type = guest.getElementsByTagName('os_type')[0].firstChild.nodeValue
			for arch in guest.getElementsByTagName('arch'):
				dom = DomainTemplate(os_type, arch)
				result.append(dom)
		return result

	def __init__(self, os_type, arch):
		self.os_type = os_type
		self.arch = arch.getAttribute('name')
		self.emulator = arch.getElementsByTagName('emulator')[0].firstChild.nodeValue
		try:
			self.loader = arch.getElementsByTagName('loader')[0].firstChild.nodeValue
		except:
			self.loader = None
		self.machines = [m.firstChild.nodeValue for m in arch.getElementsByTagName('machine')]
		self.domains = [d.getAttribute('type') for d in arch.getElementsByTagName('domain')]

	def __str__(self):
		return 'DomainTemplate(type=%s arch=%s): %s, %s, %s, %s' % (self.os_type, self.arch, self.emulator, self.loader, self.machines, self.domains)

class Domain(object):
	"""Container for domain statistics."""
	CPUTIMES = (10, 60, 5*60) # 10s 60s 5m
	def __init__(self, domain):
		self.uuid = domain.UUIDString()
		self.name = domain.name()
		self.os = domain.OSType()
		self.kernel = ''
		self.cmdline = ''
		self.initrd = ''
		self.interfaces = []
		self.disks = []
		self.graphics = []
		self._time_stamp = 0.0
		self._time_used = domain.info()[4]
		self.cputime = [0.0, 0.0, 0.0] # percentage in last 10s 60s 5m
		self.update(domain)

	def __eq__(self, other):
		return self.uuid == other.uuid;

	def update(self, domain):
		"""Update statistics."""
		self.name = domain.name()
		self.state, maxMem, curMem, self.vcpus, runtime = domain.info()

		if domain.ID() == 0 and domain.connect().getURI().startswith("xen"):
			# xen://#Domain-0 always reports (1<<32)-1
			maxMem = domain.connect().getInfo()[1]
			self.maxMem = long(maxMem) << 20 # GiB
		else:
			self.maxMem = long(maxMem) << 10 # KiB

		if self.state in (libvirt.VIR_DOMAIN_NOSTATE, libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			self.curMem = 0L
		else:
			self.curMem = long(curMem) << 10 # KiB

		# Calculate historical CPU usage
		# http://www.teamquest.com/resources/gunther/display/5/
		now = time.time()
		delta_t = now - self._time_stamp # wall clock [s]
		delta_used = runtime - self._time_used # running [ns]
		usage = delta_used / delta_t / self.vcpus / 1000000 # ms
		for i in range(len(Domain.CPUTIMES)):
			if delta_t < Domain.CPUTIMES[i]:
				e = math.exp(-1.0 * delta_t / Domain.CPUTIMES[i])
				self.cputime[i] *= e
				self.cputime[i] += (1.0 - e) * usage
			else:
				self.cputime[i] = usage
		self._time_stamp = now
		self._time_used = runtime
		self.update_expensive(domain)

	def update_expensive(self, domain):
		"""Update statistics."""
		self.xml2obj( domain )

	def xml2obj( self, domain ):
		"""Parse XML into python object."""
		doc = parseString( domain.XMLDesc( 0 ) )
		devices = doc.getElementsByTagName( 'devices' )[ 0 ]

		os = doc.getElementsByTagName( 'os' )
		if os:
			os = os[ 0 ]
			kernel = os.getElementsByTagName( 'kernel' )
			if kernel and kernel[ 0 ].firstChild and kernel[ 0 ].firstChild.nodeValue:
				self.kernel = kernel[ 0 ].firstChild.nodeValue
			cmdline = os.getElementsByTagName( 'cmdline' )
			if cmdline and cmdline[ 0 ].firstChild and cmdline[ 0 ].firstChild.nodeValue:
				self.cmdline = cmdline[ 0 ].firstChild.nodeValue
			initrd = os.getElementsByTagName( 'initrd' )
			if initrd and initrd[ 0 ].firstChild and initrd[ 0 ].firstChild.nodeValue:
				self.initrd = initrd[ 0 ].firstChild.nodeValue

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
			if dev.autoport.lower() == 'yes':
				dev.autoport = True
			else:
				dev.autoport = False
			dev.keymap = graphic.getAttribute( 'keymap' )
			self.graphics.append( dev )


class Node(object):
	"""Container for node statistics."""
	def __init__(self, uri):
		self.uri = uri
		self.conn = None
		self.storages = {}
		self.domains = {}
		self.update_autoreconnect()

		def timer_callback(timer, *opaque):
			"""Handle regular poll. Also checks connection liveness."""
			self.update_autoreconnect()
			logger.debug("timer_callback#%d: %s)" % (timer, self.uri,))
		self.timerID = virEventAddTimerImpl(Nodes.IDLE_FREQUENCY, timer_callback, (None,None))

	def update_autoreconnect(self):
		"""(Re-)connect after connection broke."""
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
				  if False: # libvirt-BUG domainEventDeregister SEGVs!!!
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
		return (self.conn.getURI(), self.name) == (other.conn.getURI(), other.name);

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
			"""Handle domain addition, update and removal."""
			eventStrings = ("Added", "Removed", "Started", "Suspended", "Resumed", "Stopped", "Saved", "Restored")
			logger.debug("domain_callback %s(%s) %s %d" % (dom.name(), dom.ID(), eventStrings[event], detail))
			uuid = dom.UUIDString()
			if event == libvirt.VIR_DOMAIN_EVENT_DEFINED:
				domStat = Domain(dom)
				self.domains[uuid] = domStat
			elif event == libvirt.VIR_DOMAIN_EVENT_UNDEFINED:
				del self.domains[uuid]
			else: # VIR_DOMAIN_EVENT_STARTED _SUSPENDED _RESUMED _STOPPED
				try:
					domStat = self.domains[uuid]
					domStat.update( dom )
				except KeyError, e:
					# during migration events are not ordered causal
					pass
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

class Nodes(dict):
	"""Handle registered nodes."""
	IDLE_FREQUENCY = 60*1000; # ms
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
	>>> node_add("qemu:///session")
	>>> node_add("xen:///")"""
	global nodes
	if uri in nodes:
		raise NodeError("Hypervisor '%s' is already connected." % (uri,))

	node = Node(uri)
	nodes[uri] = node

	logger.debug("Hypervisor '%s' added." % (uri,))

def node_remove(uri):
	"""Add node to watch list."""
	global nodes
	try:
		del nodes[uri]
	except KeyError:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))
	logger.debug("Hypervisor '%s' removed." % (uri,))

def node_query(uri):
	"""Get domain data from node."""
	global nodes
	try:
		return nodes[uri]
	except KeyError:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))

def node_frequency(hz=Nodes.IDLE_FREQUENCY, uri=None):
	"""Set frequency for polling nodes."""
	global nodes
	if uri == None:
		nodes.set_frequency(hz)
	else:
		try:
			nodes[uri].set_frequency(hz)
		except KeyError:
			raise NodeError("Hypervisor '%s' is not connected." % (uri,))

def node_list(group):
	"""Return list of watched nodes."""
	if group == 'default': # FIXME
		return [uri for uri in nodes]
	else:
		return []

def group_list():
	"""Return list of groups for nodes."""
	return ['default'] # FIXME


def domain_define( uri, domain ):
	"""Convert python object to an XML document."""
	impl = getDOMImplementation()
	doc = impl.createDocument( None, 'domain', None )
	elem = doc.createElement( 'name' )
	elem.appendChild( doc.createTextNode( domain.name ) )
	doc.documentElement.appendChild( elem )
	doc.documentElement.setAttribute( 'type', 'xen' )
	if domain.uuid:
		elem = doc.createElement( 'uuid' )
		elem.appendChild( doc.createTextNode( domain.uuid ) )
		doc.documentElement.appendChild( elem )
	elem = doc.createElement( 'memory' )
	elem.appendChild( doc.createTextNode( str( domain.maxMem / 1024 ) ) )
	doc.documentElement.appendChild( elem )
	elem = doc.createElement( 'currentMemory' )
	elem.appendChild( doc.createTextNode( str( domain.maxMem / 1024 ) ) )
	doc.documentElement.appendChild( elem )
	elem = doc.createElement( 'vcpu' )
	elem.appendChild( doc.createTextNode( str( domain.vcpus ) ) )
	doc.documentElement.appendChild( elem )
	type = doc.createElement( 'type' )
	type.appendChild( doc.createTextNode( domain.os ) )
	os = doc.createElement( 'os' )
	os.appendChild( type )
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

	doc.documentElement.appendChild( os )
	devices = doc.createElement( 'devices' )
	logger.warning( 'DISKS: %s' % domain.disks )
	for disk in domain.disks:
		logger.warning( 'DISK: %s' % disk )
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
	for iface in domain.interfaces:
		logger.warning( 'INTERFACE: %s' % iface )
		elem = doc.createElement( 'interface' )
		elem.setAttribute( 'type', iface.map_type( id = iface.type ) )
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
		logger.warning( 'GRAPHIC: %s' % graphic )
		elem = doc.createElement( 'graphics' )
		elem.setAttribute( 'type', Graphic.map_type( id = graphic.type ) )
		elem.setAttribute( 'port', str( graphic.port ) )
		if graphic.autoport:
			elem.setAttribute( 'autoport', 'yes' )
		else:
			elem.setAttribute( 'autoport', 'no' )
		elem.setAttribute( 'keymap', graphic.keymap )
		devices.appendChild( elem )

	doc.documentElement.appendChild( devices )

	try:
		node = nodes[uri]
		conn = node.conn
		logger.error( doc.toxml() )
		conn.defineXML( doc.toxml() )
	except KeyError:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))

def domain_state(uri, domain, state):
	"""Change running state of domain on node."""
	try:
		node = nodes[uri]
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_state = dom.info()[0]
		if "RUN" == state:
			if dom_state == libvirt.VIR_DOMAIN_PAUSED:
				return dom.resume()
			elif dom_state in (libvirt.VIR_DOMAIN_SHUTDOWN, libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
				return dom.create()
		elif "PAUSE" == state:
			if dom_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED):
				return dom.suspend()
		elif "SHUTDOWN" == state:
			if dom_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED):
				return dom.destroy()
		elif "RESTART" == state:
			if dom_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED):
				return dom.reboot(None)

		try:
			STATES = ['NOSTATE', 'RUNNING', 'BLOCKED', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED']
			cur_state = STATES[dom_state]
		except IndexError:
			cur_state = str(dom_state)
		raise NodeError("Unsupported state transition %s to %s" % (cur_state, state))
	except KeyError, key:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError("Error managing domain '%s': %s" % (domain, e))

def domain_save(uri, domain, statefile):
	"""Save defined domain."""
	try:
		node = nodes[uri]
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom.save(statefile)
	except KeyError, key:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError("Error saving domain '%s': %s" % (domain, e))

def domain_restore(uri, statefile):
	"""Restore defined domain."""
	try:
		node = nodes[uri]
		conn = node.conn
		conn.restore(statefile)
	except KeyError:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError("Error restoring domain '%s': %s" % (domain, e))

def domain_undefine(uri, domain):
	"""Undefine a domain on a node."""
	try:
		node = nodes[uri]
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom.undefine()
	except KeyError, key:
		raise NodeError("Hypervisor '%s' is not connected." % (uri,))
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError("Error undefining domain '%s': %s" % (domain, e))

def domain_migrate(source_uri, domain, target_uri):
	"""Migrate a domain from node to the target node."""
	try:
		source_node = nodes[source_uri]
		source_conn = source_node.conn
		source_dom = source_conn.lookupByUUIDString(domain)
		target_node = nodes[target_uri]
		target_conn = target_node.conn

		flags = libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_PERSIST_DEST | libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
		target_dom = source_dom.migrate(target_conn, flags, None, None, 0)

		# Updates are handled via the callback mechanism
		#del source_node.domains[domain]
		#target_node.domains[domain] = Domain(target_dom)
	except KeyError, key:
		raise NodeError("Hypervisor '%s' is not connected." % (key,))
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError("Error migrating domain '%s': %s" % (domain, e))
