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
from helpers import TranslatableException, ms, N_ as _
from uvmm_ldap import ldap_annotation, LdapError, LdapConnectionError, ldap_modify
import univention.admin.uexceptions
import traceback
from univention.uvmm.eventloop import *
import threading
from storage import create_storage_pool, create_storage_volume, destroy_storage_volumes, get_all_storage_volumes, StorageError, storage_pools, get_storage_pool_info
from protocol import Data_Domain, Data_Node, Data_Snapshot
import os

import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

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
	if id is not None and id in dictionary:
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

	(TYPE_FILE, TYPE_BLOCK) = range(2)
	TYPE_MAP = {TYPE_FILE: 'file', TYPE_BLOCK: 'block'}

	(CACHE_DEFAULT, CACHE_NONE, CACHE_WT, CACHE_WB) = range(4)
	CACHE_MAP = {CACHE_DEFAULT: 'default', CACHE_NONE: 'none', CACHE_WT: 'writethrough', CACHE_WB: 'writeback'}

	def __init__( self ):
		self.type = Disk.TYPE_FILE	# disk/@type
		self.device = Disk.DEVICE_DISK	# disk/@device
		self.driver = None	# disk/driver/@name
		self.driver_type = None	# disk/driver/@type
		self.driver_cache = Disk.CACHE_DEFAULT	# disk/driver/@cache
		self.source = ''	# disk/source/@file | disk/source/@dev
		self.readonly = False	# disk/readonly
		self.target_dev = ''	# disk/target/@dev
		self.target_bus = None	# disk/target/@bus
		self.size = None # not defined

	@staticmethod
	def map_device( id = None, name = None ):
		return _map( Disk.DEVICE_MAP, id, name )

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Disk.TYPE_MAP, id, name )

	@staticmethod
	def map_cache(id=None, name=None):
		return _map(Disk.CACHE_MAP, id, name)

	def __str__( self ):
		return 'Disk(%s,%s): %s, %s' % ( Disk.map_device( id = self.device ), Disk.map_type( id = self.type ), self.source, self.target_dev )

class Interface( object ):
	'''Container for interface objects'''
	( TYPE_BRIDGE, TYPE_NETWORK ) = range( 2 )
	TYPE_MAP = { TYPE_BRIDGE : 'bridge', TYPE_NETWORK : 'network' }
	def __init__( self ):
		self.type = Interface.TYPE_BRIDGE
		self.mac_address = None
		self.source = None
		self.target = None
		self.script = None
		self.model = None

	@staticmethod
	def map_type( id = None, name = None ):
		return _map( Interface.TYPE_MAP, id, name )

	def __str__( self ):
		return 'Interface(%s): %s, %s' % ( Interface.map_type( id = self.type ), self.mac_address, self.source )

class Graphic( object ):
	'''Container for graphic objects'''
	( TYPE_VNC, TYPE_SDL ) = range( 2 )
	TYPE_MAP = { TYPE_VNC: 'vnc', TYPE_SDL: 'sdl' }
	def __init__( self ):
		self.type = Graphic.TYPE_VNC
		self.port = -1
		self.autoport = True
		self.keymap = 'de'
		self.listen = None
		self.passwd = None

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
		>>> t = DomainTemplate.list_from_xml(KVM_CAPABILITIES)
		>>> len(t)
		3
		>>> t[0].os_type
		u'hvm'
		>>> t[0].arch
		u'i686'
		>>> t[0].domain_type
		u'qemu'
		>>> t[0].emulator
		u'/usr/bin/qemu'
		>>> t[0].machines
		[u'pc']
		>>> t[0].features
		['pae', u'acpi', u'apic']
		"""
		doc = parseString(xml)
		capas = doc.firstChild
		result = []
		for guest in filter(lambda f: f.nodeName == 'guest', capas.childNodes):
			os_type = DomainTemplate.__nv(guest, 'os_type')
			f_names = DomainTemplate.__get_features(guest)
			for arch in filter(lambda f: f.nodeName == 'arch', guest.childNodes):
				for dom in filter(lambda f: f.nodeName == 'domain', arch.childNodes):
					dom = DomainTemplate(arch, dom, os_type, f_names)
					result.append(dom)
		return result

	@staticmethod
	def __nv(node, name):
		return node.getElementsByTagName(name)[0].firstChild.nodeValue

	@staticmethod
	def __get_features(node):
		"""Return list of features."""
		f_names = []
		features = filter(lambda f: f.nodeName == 'features', node.childNodes)
		if features:
			for c in features[0].childNodes:
				if c.nodeType == 1:
					if c.nodeName == 'pae':
						if 'nonpae' not in f_names:
							f_names.append('pae')
					elif c.nodeName == 'nonpae':
						if 'pae' not in f_names:
							f_names.append('nonpae')
					elif c.getAttribute('default') == 'on':
						f_names.append(c.nodeName)
		return f_names

	def __init__(self, arch, domain_type, os_type, features):
		self.os_type = os_type
		self.features = features
		self.arch = arch.getAttribute('name')
		self.domain_type = domain_type.getAttribute('type')

		for n in [domain_type, arch]:
			try:
				self.emulator = DomainTemplate.__nv(n, 'emulator')
				break
			except IndexError:
				pass
		else:
			logger.error('No emulator specified in %s/%s' % (self.arch, self.domain_type))
			raise

		for n in [domain_type, arch]:
			self.machines = [m.firstChild.nodeValue for m in n.childNodes if m.nodeName == 'machine']
			if self.machines:
				break
		else:
			logger.error('No machines specified in %s/%s' % (self.arch, self.domain_type))
			raise

		try:
			self.loader = DomainTemplate.__nv(arch, 'loader')
		except:
			self.loader = None # optional

		# Work around for Bug #19120: Xen-Fv-64 needs <pae/>
		if self.domain_type == 'xen' and self.arch == 'x86_64' and not 'pae' in self.features:
			self.features.append('pae')

	def __str__(self):
		return 'DomainTemplate(arch=%s dom_type=%s os_type=%s): %s, %s, %s, %s' % (self.arch, self.domain_type, self.os_type, self.emulator, self.loader, self.machines, self.features)

	def matches(self, domain):
		'''Return True if domain matches os_type, arch and domain_type.'''
		return self.arch == domain.arch and self.domain_type == domain.domain_type and self.os_type == domain.os_type

class Domain(object):
	"""Container for domain statistics."""
	CPUTIMES = (10, 60, 5*60) # 10s 60s 5m
	def __init__(self, domain, node):
		self.node = node
		self.pd = Data_Domain() # public data
		self.pd.uuid = domain.UUIDString()
		self.pd.os_type = domain.OSType()
		self._time_stamp = 0.0
		self._time_used = 0L
		self._cpu_usage = 0
		self.update(domain)
		self.update_ldap()

	def __eq__(self, other):
		return self.pd.uuid == other.pd.uuid;

	def update(self, domain):
		"""Update statistics which may change often."""
		id = domain.ID()
		self.pd.name = domain.name()
		for i in range(5):
			info = domain.info()
			if info[0] != libvirt.VIR_DOMAIN_NOSTATE: # ignore =?= libvirt's transient error
				break
			if not domain.isActive():
				info[0] = libvirt.VIR_DOMAIN_SHUTOFF
				break
			time.sleep(1)
		else:
			logger.warning('No state for %s: %s' % (self.pd.name, info))
			return

		self.pd.state, maxMem, curMem, self.pd.vcpus, runtime = info

		if domain.ID() == 0 and domain.connect().getType() == 'Xen':
			# xen://#Domain-0 always reports (1<<32)-1
			maxMem = domain.connect().getInfo()[1]
			self.pd.maxMem = long(maxMem) << 20 # GiB
		else:
			self.pd.maxMem = long(maxMem) << 10 # KiB

		if self.pd.state in (libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			self.pd.curMem = 0L
			delta_used = 0L
			self._time_used = 0L
		else:
			self.pd.curMem = long(curMem) << 10 # KiB
			delta_used = runtime - self._time_used # running [ns]
			self._time_used = runtime

		# Calculate historical CPU usage
		# http://www.teamquest.com/resources/gunther/display/5/
		now = time.time()
		delta_t = now - self._time_stamp # wall clock [s]
		if delta_t > 0.0 and delta_used >= 0L:
			try:
				self._cpu_usage = delta_used / delta_t / self.pd.vcpus / 1000000 # ms
			except ZeroDivisionError:
				self._cpu_usage = 0
			for i in range(len(Domain.CPUTIMES)):
				if delta_t < Domain.CPUTIMES[i]:
					e = math.exp(-1.0 * delta_t / Domain.CPUTIMES[i])
					self.pd.cputime[i] *= e
					self.pd.cputime[i] += (1.0 - e) * self._cpu_usage
				else:
					self.pd.cputime[i] = self._cpu_usage
		self._time_stamp = now
		self.update_expensive(domain)

	def update_expensive(self, domain):
		"""Update statistics."""
		# Full XML efinition
		self.xml2obj( domain )
		# List of snapshots

		snapshots = None
		if self.node.pd.supports_snapshot:
			has_snapshot_disk = False
			for dev in self.pd.disks:
				if dev.readonly:
					continue
				if dev.driver_type in ('qcow2',):
					has_snapshot_disk = True
					continue
				break
			else:
				if has_snapshot_disk:
					snapshots = {}
					for name in domain.snapshotListNames(0):
						snap = domain.snapshotLookupByName(name, 0)
						xml = snap.getXMLDesc(0)
						doc = parseString(xml)
						ctime = doc.getElementsByTagName('creationTime')[0].firstChild.nodeValue
						s = Data_Snapshot()
						s.name = name
						s.ctime = int(ctime)
						snapshots[name] = s
		self.pd.snapshots = snapshots

	def update_ldap(self):
		"""Update annotations from LDAP."""
		try:
			self.pd.annotations = ldap_annotation(self.pd.uuid)
		except LdapError, e:
			self.pd.annotations = {}

	def xml2obj( self, domain ):
		"""Parse XML into python object."""
		doc = parseString(domain.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
		devices = doc.getElementsByTagName( 'devices' )[ 0 ]
		self.pd.domain_type = doc.documentElement.getAttribute('type')
		os = doc.getElementsByTagName( 'os' )
		if os:
			os = os[ 0 ]
			type = os.getElementsByTagName( 'type' )
			if type and type[ 0 ].firstChild and type[ 0 ].firstChild.nodeValue:
				self.pd.os_type = type[0].firstChild.nodeValue
				# we should use the identifier xen instead of linux
				if self.pd.os_type == 'linux':
					self.pd.os_type = 'xen'
				if type[ 0 ].hasAttribute( 'arch' ):
					self.pd.arch = type[0].getAttribute('arch')
			kernel = os.getElementsByTagName( 'kernel' )
			if kernel and kernel[ 0 ].firstChild and kernel[ 0 ].firstChild.nodeValue:
				self.pd.kernel = kernel[0].firstChild.nodeValue
			cmdline = os.getElementsByTagName( 'cmdline' )
			if cmdline and cmdline[ 0 ].firstChild and cmdline[ 0 ].firstChild.nodeValue:
				self.pd.cmdline = cmdline[0].firstChild.nodeValue
			initrd = os.getElementsByTagName( 'initrd' )
			if initrd and initrd[ 0 ].firstChild and initrd[ 0 ].firstChild.nodeValue:
				self.pd.initrd = initrd[0].firstChild.nodeValue
			boot = os.getElementsByTagName('boot')
			if boot:
				self.pd.boot = [dev.attributes['dev'].value for dev in boot]
		bootloader = doc.getElementsByTagName( 'bootloader' )
		if bootloader:
			if bootloader[ 0 ].firstChild and bootloader[ 0 ].firstChild.nodeValue:
				self.pd.bootloader = bootloader[ 0 ].firstChild.nodeValue
			args = doc.getElementsByTagName( 'bootloader_args' )
			if args and args[ 0 ].firstChild and args[ 0 ].firstChild.nodeValue:
				self.pd.bootloader_args = args[ 0 ].firstChild.nodeValue

		self.pd.disks = []
		disks = devices.getElementsByTagName( 'disk' )
		for disk in disks:
			dev = Disk()
			dev.type = Disk.map_type( name = disk.getAttribute( 'type' ) )
			dev.device = Disk.map_device( name = disk.getAttribute( 'device' ) )
			driver = disk.getElementsByTagName('driver')
			if driver:
				dev.driver = driver[0].getAttribute('name')
				dev.driver_type = driver[0].getAttribute('type')
				dev.driver_cache = driver[0].getAttribute('cache')
			source = disk.getElementsByTagName( 'source' )
			if source:
				if dev.type == Disk.TYPE_FILE:
					dev.source = source[0].getAttribute('file')
				elif dev.type == Disk.TYPE_BLOCK:
					dev.source = source[0].getAttribute('dev')
				else:
					raise NodeError(_('Unknown disk type: %(type)d'), type=dev.type)
			target = disk.getElementsByTagName( 'target' )
			if target:
				dev.target_dev = target[ 0 ].getAttribute( 'dev' )
				dev.target_bus = target[ 0 ].getAttribute( 'bus' )
			if disk.getElementsByTagName( 'readonly' ):
				dev.readonly = True

			self.pd.disks.append(dev)

		self.pd.interfaces = []
		interfaces = devices.getElementsByTagName( 'interface' )
		for iface in interfaces:
			dev = Interface()
			dev.type = Interface.map_type( name = iface.getAttribute( 'type' ) )
			mac = iface.getElementsByTagName( 'mac' )
			if mac:
				dev.mac_address = mac[ 0 ].getAttribute( 'address' )
			source = iface.getElementsByTagName( 'source' )
			if source:
				dev.source = source[ 0 ].getAttribute( dev.map_type( id = dev.type ) )
			script = iface.getElementsByTagName( 'script' )
			if script:
				dev.script = script[ 0 ].getAttribute( 'path' )
			target = iface.getElementsByTagName( 'target' )
			if target:
				dev.target_dev = target[ 0 ].getAttribute( 'dev' )
			model = iface.getElementsByTagName( 'model' )
			if model:
				dev.model = model[ 0 ].getAttribute( 'type' )

			self.pd.interfaces.append(dev)

		self.pd.graphics = []
		graphics = devices.getElementsByTagName( 'graphics' )
		for graphic in graphics:
			dev = Graphic()
			type = graphic.getAttribute('type')
			dev.type = Graphic.map_type(name=type)
			if dev.type == Graphic.TYPE_VNC:
				dev.port = int(graphic.getAttribute('port'))
				dev.autoport = graphic.getAttribute('autoport').lower() == 'yes'
				if graphic.hasAttribute('listen'):
					dev.listen = graphic.getAttribute('listen')
				if graphic.hasAttribute('passwd'):
					dev.passwd = graphic.getAttribute('passwd')
				dev.keymap = graphic.getAttribute('keymap')
			elif dev.type == Graphic.TYPE_SDL:
				pass
			else:
				logger.error('Unsupported graphics type: %s' % type)
			self.pd.graphics.append(dev)

	def key(self):
		"""Return a unique key for this domain and generation."""
		return hash((self.pd.uuid, self._time_stamp))

class Node(object):
	"""Container for node statistics."""
	def __init__(self, uri):
		self.pd = Data_Node() # public data
		self.uri = uri
		self._lock = threading.Lock()
		self.conn = None
		self.domains = {}
		self.config_frequency = Nodes.IDLE_FREQUENCY
		self.current_frequency = Nodes.IDLE_FREQUENCY

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

		self.timerID = virEventAddTimerImpl(self.current_frequency, timer_callback, (None,None))
		self.domainCB = None

	def update_autoreconnect(self):
		"""(Re-)connect after connection broke."""
		try:
			if self.conn == None:
				self.conn = libvirt.open(self.uri)
				logger.info("Connected to '%s'" % (self.uri,))
				self.update_once()
				self._register_default_pool()
				# reset timer after successful re-connect
				self.current_frequency = self.config_frequency
				virEventUpdateTimerImpl(self.timerID, self.config_frequency)
			self.update()
			self.pd.last_try = self.pd.last_update = time.time()
		except libvirt.libvirtError, e:
			self.pd.last_try = time.time()
			# double timer interval until maximum
			hz = min(self.current_frequency * 2, Nodes.BEBO_FREQUENCY)
			logger.warning("'%s' broken? next check in %s. %s" % (self.uri, ms(hz), e))
			if hz > self.current_frequency:
				self.current_frequency = hz
				virEventUpdateTimerImpl(self.timerID, self.current_frequency)
			if self.conn != None:
				try:
					self.conn.domainEventDeregister(self.domainCB)
				except Exception, e:
					logger.error('Exception %s: %s' % (e, traceback.format_exc()))
					pass
				self.domainCB = None
				try:
					self.conn.close()
				except Exception, e:
					logger.error('Exception %s: %s' % (e, traceback.format_exc()))
					pass
				self.conn = None

	def __eq__(self, other):
		return (self.uri, self.pd.name) == (other.uri, other.pd.name)

	def __del__(self):
		"""Free Node and deregister callbacks."""
		self.unregister()
		del self.pd
		del self.domains

	def _register_default_pool( self ):
		'''create a default storage pool if not available'''
		for pool in storage_pools(node=self):
			if pool.name == 'default':
				logger.debug("default pool already registered on %s" % self.pd.name)
				break
		else:
			logger.info("creating default pool on %s" % self.pd.name)
			create_storage_pool( self.conn, configRegistry.get( 'uvmm/pool/default/path', '/var/lib/libvirt/images' ) )

	def update_once(self):
		"""Update once on (re-)connect."""
		self.pd.name = self.conn.getHostname()
		info = self.conn.getInfo()
		self.pd.phyMem = long(info[1]) << 20 # MiB
		self.pd.cpus = info[2]
		self.pd.cores = info[4:8]
		xml = self.conn.getCapabilities()
		self.pd.capabilities = DomainTemplate.list_from_xml(xml)
		type = self.conn.getType()
		self.pd.supports_suspend = False
		self.pd.supports_snapshot = False
		if type == 'QEMU':
			# Qemu/Kvm supports managedSave
			self.pd.supports_suspend = True
			self.pd.supports_snapshot = True
		elif type == 'Xen':
			# As of libvirt-0.8.5 Xen doesn't support managedSave, but test dom0
			d = self.conn.lookupByID(0)
			try:
				d.hasManagedSaveImage(0)
				self.pd.supports_suspend = True
			except libvirt.libvirtError, e:
				if e.get_error_code() != libvirt.VIR_ERR_NO_SUPPORT:
					logger.error('Exception %s: %s' % (e, traceback.format_exc()))
			# As of libvirt-0.8.5 Xen doesn't support snapshot-*, but test dom0
			try:
				d.snapshotListNames(0)
				self.pd.supports_snapshot = True
			except libvirt.libvirtError, e:
				if e.get_error_code() != libvirt.VIR_ERR_NO_SUPPORT:
					logger.error('Exception %s: %s' % (e, traceback.format_exc()))

		def domain_callback(conn, dom, event, detail, node):
			try:
				"""Handle domain addition, update and removal."""
				eventStrings = ("Added", "Removed", "Started", "Suspended", "Resumed", "Stopped", "Saved", "Restored")
				logger.debug("domain_callback %s(%s) %s %d" % (dom.name(), dom.ID(), eventStrings[event], detail))
				uuid = dom.UUIDString()
				if event == libvirt.VIR_DOMAIN_EVENT_DEFINED:
					domStat = Domain(dom, node=self)
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
		self.config_frequency = hz
		self.current_frequency = hz
		virEventUpdateTimerImpl(self.timerID, hz)

	def update(self):
		"""Update node statistics."""
		curMem = 0
		maxMem = 0
		cpu_usage = 0
		cached_domains = self.domains.keys()
		def all_domains():
			for id in self.conn.listDomainsID():
				yield self.conn.lookupByID(id)
			for name in self.conn.listDefinedDomains():
				yield self.conn.lookupByName(name)
		for dom in all_domains():
			uuid = dom.UUIDString()
			if uuid in self.domains:
				# Update existing domains
				domStat = self.domains[uuid]
				domStat.update(dom)
				try:
					cached_domains.remove(uuid)
				except ValueError:
					pass
			else:
				# Add new domains
				domStat = Domain(dom, node=self)
				self.domains[uuid] = domStat
			curMem += domStat.pd.curMem
			maxMem += domStat.pd.maxMem
			cpu_usage += domStat._cpu_usage
		for uuid in cached_domains:
			# Remove obsolete domains
			del self.domains[uuid]
		self.pd.curMem = curMem
		self.pd.maxMem = maxMem
		self.pd.cpu_usage = min(1000, cpu_usage)

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
	IDLE_FREQUENCY = 15*1000 # ms
	USED_FREQUENCY = 10*1000 # ms
	BEBO_FREQUENCY = 5*60*1000 # ms
	def __init__(self):
		super(Nodes,self).__init__()
		self.frequency = -1
	def __delitem__(self, uri):
		"""x.__delitem__(i) <==> del x[i]"""
		self[uri].unregister()
		super(Nodes, self).__delitem__(uri)
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

def _domain_backup(dom, save=True):
	"""Save domain definition to backup file."""
	backup_dir = configRegistry.get('uvmm/backup/directory', '/var/backups/univention-virtual-machine-manager-daemon')
	uuid = dom.UUIDString()
	xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
	if len(xml) < 300: # minimal XML descriptor length
		logger.error("Failed to backup domain %s: %s" % (uuid, xml))
		raise NodeError("Failed to backup domain %(domain)s: %(xml)s", domain=uuid, xml=xml)
	now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
	suffix = 'xml'
	if save:
		suffix += '.save'
	tmp_file = os.path.join(backup_dir, "%s_%s.%s" % (uuid, now, suffix))
	file = os.path.join(backup_dir, "%s.%s" % (uuid, suffix))
	umask = os.umask(0177)
	f = open(tmp_file, "w")
	try:
		f.write(xml)
	finally:
		f.close()
	os.umask(umask)
	os.rename(tmp_file, file)
	logger.info("Domain backuped to %s." % (file,))

def domain_define( uri, domain ):
	"""Convert python object to an XML document."""
	node = node_query(uri)
	conn = node.conn

	# Check for (name,uuid) collision
	try:
		old_dom = conn.lookupByName(domain.name)
		if old_dom.UUIDString() != domain.uuid:
			raise NodeError(_('Domain name "%(domain)s" already used by "%(uuid)s"'), domain=domain.name, uuid=domain.uuid)
	except libvirt.libvirtError, e:
		if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
			logger.error(e)
			raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.name, error=e.get_error_message())

	old_stat = None
	warnings = []

	impl = getDOMImplementation()
	doc = impl.createDocument( None, 'domain', None )
	elem = doc.createElement( 'name' )
	elem.appendChild( doc.createTextNode( domain.name ) )
	doc.documentElement.appendChild( elem )
	doc.documentElement.setAttribute('type', domain.domain_type.lower()) # TODO: verify
	if domain.uuid:
		old_stat = node.domains[domain.uuid].key()
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
	logger.debug('Searching for template: arch=%s domain_type=%s os_type=%s' % (domain.arch, domain.domain_type, domain.os_type))
	for template in node.pd.capabilities:
		logger.debug('template: %s' % template)
		if template.matches(domain):
			if template.loader:
				loader = doc.createElement('loader')
				loader.appendChild(doc.createTextNode(template.loader))

			if template.features:
				features = doc.createElement('features')
				for f_name in template.features:
					feature = doc.createElement(f_name)
					features.appendChild(feature)
				doc.documentElement.appendChild(features)
			break

	type = doc.createElement( 'type' )
	type.appendChild( doc.createTextNode( domain.os_type ) )
	type.setAttribute( 'arch', domain.arch )
	os = doc.createElement( 'os' )
	os.appendChild( type )
	if loader:
		os.appendChild( loader )

	if hasattr(domain, 'bootloader') and domain.bootloader:
		text = doc.createTextNode( domain.bootloader )
		bootloader = doc.createElement( 'bootloader' )
		bootloader.appendChild( text )
		doc.documentElement.appendChild( bootloader )
		if domain.bootloader_args:
			text = doc.createTextNode( domain.bootloader_args )
			bootloader_args = doc.createElement( 'bootloader_args' )
			bootloader_args.appendChild( text )
			doc.documentElement.appendChild( bootloader_args )

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
	if domain.os_type == 'hvm':
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

		if hasattr(disk, 'driver') and disk.driver:
			driver = doc.createElement('driver')
			driver.setAttribute('name', disk.driver)
			if hasattr(disk, 'driver_type') and disk.driver_type:
				driver.setAttribute('type', disk.driver_type)
			if hasattr(disk, 'driver_cache') and disk.driver_cache:
				driver.setAttribute('cache', disk.map_cache(id=disk.driver_cache))
			elem.appendChild(driver)

		source = doc.createElement( 'source' )
		if disk.type == Disk.TYPE_FILE:
			source.setAttribute('file', disk.source)
		elif disk.type == Disk.TYPE_BLOCK:
			source.setAttribute('dev', disk.source)
		else:
			raise NodeError(_('Unknown disk type: %(type)d'), type=disk.type)
		elem.appendChild( source )

		# FIXME: Xen-PV should use xvd[a-z], Kvm-VirtIO uses vd[a-z]
		target = doc.createElement( 'target' )
		target.setAttribute( 'dev', disk.target_dev )
		# TODO: Xen an KVM have their default based on the device names
		if disk.target_bus:
			target.setAttribute('bus', disk.target_bus)
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
		source.setAttribute( iface.map_type( id = iface.type ), iface.source )
		elem.appendChild( source )
		if iface.script:
			script = doc.createElement( 'script' )
			script.setAttribute( 'path', iface.script )
			elem.appendChild( script )
		if iface.target:
			target = doc.createElement( 'target' )
			target.setAttribute( 'dev', iface.target )
			elem.appendChild( target )
		if hasattr(iface, 'model') and iface.model:
			model = doc.createElement( 'model' )
			model.setAttribute( 'type', iface.model )
			elem.appendChild( model )
		devices.appendChild( elem )

	# define a tablet usb device which has absolute cursor movement for a better VNC experience. Bug #19244
	if domain.os_type == 'hvm':
		tablet = doc.createElement( 'input' )
		tablet.setAttribute( 'type', 'tablet' )
		tablet.setAttribute( 'bus', 'usb' )

		devices.appendChild( tablet )

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
		if hasattr(graphic, 'passwd') and graphic.passwd:
			elem.setAttribute( 'passwd', graphic.passwd )
		elem.setAttribute( 'keymap', graphic.keymap )
		devices.appendChild( elem )

	doc.documentElement.appendChild( devices )

	if domain.domain_type in ('kvm'): # 'qemu'
		doc.documentElement.setAttribute("xmlns:qemu", "http://libvirt.org/schemas/domain/qemu/1.0")
		commandline = doc.createElement('qemu:commandline')

		models = set()
		for iface in domain.interfaces:
			if hasattr(iface, 'model') and iface.model:
				models.add(iface.model)
		models &= set(['e1000', 'ne2k_isa', 'ne2k_pci', 'pcnet', 'rtl8139', 'virtio'])
		for model in models:
			arg = doc.createElement('qemu:arg')
			arg.setAttribute('value', '-option-rom')
			commandline.appendChild(arg)
			arg = doc.createElement('qemu:arg')
			arg.setAttribute('value', '/usr/share/kvm/pxe-%s.bin' % model)
			commandline.appendChild(arg)

		doc.documentElement.appendChild(commandline)

	# remove old domain definitions
	if domain.uuid:
		try:
			dom = conn.lookupByUUIDString(domain.uuid)
			_domain_backup(dom)
			if dom.name() != domain.name: # rename needs undefine
				dom.undefine() # all snapshots are destroyed!
				logger.info('Old domain "%s" removed.' % (domain.uuid,))
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(e)
				raise NodeError(_('Error removing domain "%(domain)s": %(error)s'), domain=domain.uuid, error=e.get_error_message())

	try:
		logger.debug('XML DUMP: %s' % doc.toxml())
		d = conn.defineXML(doc.toxml())
		domain.uuid = d.UUIDString()
		_domain_backup(d, save=False)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error defining domain "%(domain)s": %(error)s'), domain=domain.name, error=e.get_error_message())
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
		except LdapConnectionError, e:
			logger.error('Updating LDAP failed, insufficient permissions: %s' % (e,))
			warnings.append( _( 'Failed to update the additionally information in the LDAP directory.' ) )
		except ( univention.admin.uexceptions.ldapError, univention.admin.uexceptions.objectExists ), e:
			logger.error('Updating LDAP failed: %s %s' % (e, record))
			warnings.append( _( 'Failed to update the additionally information in the LDAP directory.' ) )

	node.wait_update(domain.uuid, old_stat)

	return ( domain.uuid, warnings )

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
					(libvirt.VIR_DOMAIN_RUNNING,  'SUSPEND' ): lambda:dom.managedSave(0),
					(libvirt.VIR_DOMAIN_BLOCKED,  'PAUSE'   ): dom.suspend,
					(libvirt.VIR_DOMAIN_BLOCKED,  'RESTART' ): lambda:dom.destroy(None),
					(libvirt.VIR_DOMAIN_BLOCKED,  'RUN'     ): None,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SHUTDOWN'): dom.destroy,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SUSPEND' ): lambda:dom.managedSave(0),
					(libvirt.VIR_DOMAIN_PAUSED,   'PAUSE'   ): None,
					(libvirt.VIR_DOMAIN_PAUSED,   'RUN'     ): dom.resume,
					(libvirt.VIR_DOMAIN_PAUSED,   'SHUTDOWN'): dom.destroy,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_CRASHED,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_CRASHED,  'SHUTDOWN'): None, # TODO destroy?
					}
			transition = TRANSITION[(dom_stat.pd.state, state)]
		except KeyError, e:
			cur_state = STATES[dom_stat.pd.state]
			raise NodeError(_('Unsupported state transition %(cur_state)s to %(next_state)s'), cur_state=cur_state, next_state=state)

		if transition:
			transition()
			ignore_states = [libvirt.VIR_DOMAIN_NOSTATE]
			if state == 'RUN':
				ignore_states.append(libvirt.VIR_DOMAIN_PAUSED)
			for t in range(20):
				cur_state = dom.info()[0]
				if cur_state not in ignore_states:
					# xen does not send event, do update explicitly
					dom_stat.pd.state = cur_state
					break
				time.sleep(1)
	except KeyError, e:
		logger.error("Domain %s not found" % (e,))
		raise NodeError(_('Error managing domain "%(domain)s"'), domain=domain)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=e.get_error_message())

def domain_save(uri, domain, statefile):
	"""Save defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		old_state = node.domains[ domain ].key()
		dom.save(statefile)
		node.domains[ domain ].update( dom )
		node.wait_update( domain, old_state )
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error saving domain "%(domain)s": %(error)s'), domain=domain, error=e.get_error_message())

def domain_restore(uri, domain, statefile):
	"""Restore defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		old_state = node.domains[ domain ].key()
		conn.restore(statefile)
		node.domains[ domain ].update( dom )
		node.wait_update( domain, old_state )
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error restoring domain "%(domain)s": %(error)s'), domain=domain, error=e.get_error_message())

def domain_undefine(uri, domain, volumes=[]):
	"""Undefine a domain and its volumes on a node."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		_domain_backup(dom)
		if volumes is None:
			volumes = get_all_storage_volumes(conn, dom,)
		destroy_storage_volumes(conn, volumes, ignore_error=True)
		try:
			if dom.hasManagedSaveImage(0):
				ret = dom.managedSaveRemove(0)
		except libvirt.libvirtError, e:
			# libvirt returns an 'internal error' when no save image exists
			if e.get_error_code() != libvirt.VIR_ERR_INTERNAL_ERROR:
				logger.debug(e)
		dom.undefine()
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error undefining domain "%(domain)s": %(error)s'), domain=domain, error=e.get_error_message())

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
			xml = source_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
			target_conn.defineXML(xml)
			source_dom.undefine()
		elif True or source_state in (libvirt.VIR_DOMAIN_PAUSED):
			raise NodeError(_('Domain "%(domain)s" in state "%(state)s" can not be migrated'), domain=domain, state=STATES[source_state])

		# Updates are handled via the callback mechanism, but remove domain
		# info as soon as possible to not show stale data
		try:
			del source_node.domains[domain]
		except KeyError, e:
			pass
		#target_node.domains[domain] = Domain(target_dom, node=target_node)
		for t in range(10):
			if domain not in source_node.domains and domain in target_node.domains:
				break
			time.sleep(1)
		else:
			logger.warning('Domain "%(domain)s" still not migrated from "%(source)s" to "%(target)s"' % {'domain':domain, 'source':source_uri, 'target':target_uri})
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=e.get_error_message())

def domain_snapshot_create(uri, domain, snapshot):
	"""Create new snapshot of domain."""
	try:
		node = node_query(uri)
		if not node.pd.supports_snapshot:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		if dom_stat.pd.snapshots is None:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		old_state = dom_stat.key()
		xml = '''<domainsnapshot><name>%s</name></domainsnapshot>''' % snapshot
		s = dom.snapshotCreateXML(xml, 0)

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error creating "%(domain)s" snapshot: %(error)s'), domain=domain, error=e.get_error_message())

def domain_snapshot_revert(uri, domain, snapshot):
	"""Revert to snapshot of domain."""
	try:
		node = node_query(uri)
		if not node.pd.supports_snapshot:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		if dom_stat.pd.snapshots is None:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		old_state = dom_stat.key()
		snap = dom.snapshotLookupByName(snapshot, 0)
		r = dom.revertToSnapshot(snap, 0)
		if r != 0:
			raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=e.get_error_message())

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=e.get_error_message())

def domain_snapshot_delete(uri, domain, snapshot):
	"""Delete snapshot of domain."""
	try:
		node = node_query(uri)
		if not node.pd.supports_snapshot:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		if dom_stat.pd.snapshots is None:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		old_state = dom_stat.key()
		snap = dom.snapshotLookupByName(snapshot, 0)
		r = snap.delete(0)
		if r != 0:
			raise NodeError(_('Error deleting "%(domain)s" snapshot: %(error)s'), domain=domain, error=e.get_error_message())

		try:
			del node.domains[domain].pd.snapshots[snapshot]
		except KeyError, e:
			dom_stat.update(dom)
			node.wait_update(domain, old_state)
	except libvirt.libvirtError, e:
		logger.error(e)
		raise NodeError(_('Error deleting "%(domain)s" snapshot: %(error)s'), domain=domain, error=e.get_error_message())

def domain_update(domain):
	"""Trigger update of domain.
	Unfound domains are ignored."""
	global nodes
	for node in nodes.itervalues():
		conn = node.conn
		try:
			dom_stat = node.domains[domain]
			dom = conn.lookupByUUIDString(domain)
			dom_stat.update(dom)
			dom_stat.update_ldap()
			return
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(e)
				raise NodeError(_('Error updating domain "%(domain)s"'), domain=domain)
			# remove stale data
			del node.domains[domain]
		except KeyError, e:
			# domain not on this node
			pass
	# failed to find existing data, search again all hosts
	for node in nodes.itervalues():
		conn = node.conn
		try:
			dom = conn.lookupByUUIDString(domain)
			dom_stat = Domain(dom, node=node)
			node.domains[uuid] = dom_stat
			return
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(e)
				raise NodeError(_('Error updating domain "%(domain)s"'), domain=domain)
			else:
				continue # skip this node
	else:
		logger.info('Domain %s not found for update' % domain)
		raise NodeError(_('Failto to update domain "%(domain)s"'), domain=domain)

if __name__ == '__main__':
	XEN_CAPABILITIES = '''<capabilities>
		<host>
			<cpu>
				<arch>x86_64</arch>
				<features>
					<pae/>
				</features>
			</cpu>
			<migration_features>
				<live/>
				<uri_transports>
					<uri_transport>xenmigr</uri_transport>
				</uri_transports>
			</migration_features>
			<topology>
				<cells num='1'>
					<cell id='0'>
						<cpus num='1'>
							<cpu id='0'/>
						</cpus>
					</cell>
				</cells>
			</topology>
		</host>
		<guest>
			<os_type>xen</os_type>
			<arch name='x86_64'>
				<wordsize>64</wordsize>
				<emulator>/usr/lib64/xen/bin/qemu-dm</emulator>
				<machine>xenpv</machine>
				<domain type='xen'>
				</domain>
			</arch>
		</guest>
		<guest>
			<os_type>xen</os_type>
			<arch name='i686'>
				<wordsize>32</wordsize>
				<emulator>/usr/lib64/xen/bin/qemu-dm</emulator>
				<machine>xenfv</machine>
				<domain type='xen'>
				</domain>
			</arch>
			<features>
				<pae/>
				<nonpae/>
				<acpi default='on' toggle='yes'/>
				<apic default='on' toggle='yes'/>
			</features>
		</guest>
	</capabilities>'''
	KVM_CAPABILITIES = '''<capabilities>
		<host>
			<uuid>00020003-0004-0005-0006-000700080009</uuid>
			<cpu>
				<arch>x86_64</arch>
				<model>phenom</model>
				<topology sockets='1' cores='2' threads='1'/>
				<feature name='wdt'/>
			</cpu>
			<migration_features>
				<live/>
				<uri_transports>
					<uri_transport>tcp</uri_transport>
				</uri_transports>
			</migration_features>
		</host>
		<guest>
			<os_type>hvm</os_type>
			<arch name='i686'>
				<wordsize>32</wordsize>
				<emulator>/usr/bin/qemu</emulator>
				<machine>pc</machine>
				<domain type='qemu'>
				</domain>
				<domain type='kvm'>
					<emulator>/usr/bin/kvm</emulator>
					<machine>pc-0.12</machine>
					<machine canonical='pc-0.12'>pc</machine>
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
		<guest>
			<os_type>hvm</os_type>
			<arch name='arm'>
				<wordsize>32</wordsize>
				<emulator>/usr/bin/qemu-system-arm</emulator>
				<machine>integratorcp</machine>
				<domain type='qemu'>
				</domain>
			</arch>
		</guest>
	</capabilities>'''

	import doctest
	doctest.testmod()
