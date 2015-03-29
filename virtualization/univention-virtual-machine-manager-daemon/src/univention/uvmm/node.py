# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  node handler
#
# Copyright 2010-2015 Univention GmbH
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
import logging
import math
from helpers import TranslatableException, ms, tuple2version, N_ as _, uri_encode, FQDN
from uvmm_ldap import ldap_annotation, LdapError, LdapConnectionError, ldap_modify
import univention.admin.uexceptions
import threading
from storage import create_storage_pool, create_storage_volume, destroy_storage_volumes, get_domain_storage_volumes, StorageError, get_pool_info
from protocol import Data_Domain, Data_Node, Data_Snapshot, Disk, Interface, Graphic
from network import network_start, network_find_by_bridge, NetworkError
import copy
import os
import stat
import errno
import fnmatch
import re
import random
from xml.sax.saxutils import escape as xml_escape
import tempfile
try:
	from lxml import etree as ET
except ImportError:
	import xml.etree.ElementTree as ET
try:
	import cPickle as pickle
except ImportError:
	import pickle
QEMU_URI = 'http://libvirt.org/schemas/domain/qemu/1.0'
QEMU_PXE_PREFIX = '/usr/share/kvm/pxe'

import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.node')

STATES = ('NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED')

class NodeError(TranslatableException):
	"""Error while handling node."""
	pass

class StoragePool(object):
	"""Container for storage pool statistics."""
	def __init__(self, pool):
		self.uuid = pool.UUIDString()
		self.name = pool.name()
		self.capacity = 0
		self.available = 0
		self.update(pool)
	def __eq__(self, other):
		return self.uuid == other.uuid
	def update(self, pool):
		"""Update statistics."""
		_state, self.capacity, _allocation, self.available = pool.info()


class DomainTemplate(object):
	'''Container for node capability.'''

	@staticmethod
	def list_from_xml(xml):
		"""Convert XML to list."""
		capabilities_tree = ET.fromstring(xml)
		result = []
		for guest in capabilities_tree.findall('guest'):
			os_type = guest.findtext('os_type')
			f_names = DomainTemplate.__get_features(guest)
			for arch in guest.findall('arch'):
				for dom in arch.findall('domain'):
					dom = DomainTemplate(arch, dom, os_type, f_names)
					result.append(dom)
		return result

	@staticmethod
	def __get_features(node):
		"""Return list of features."""
		f_names = []
		features = node.find('features')
		if features is not None:
			for child in features:
				if child.tag == 'pae':
					if 'nonpae' not in f_names:
						f_names.append('pae')
				elif child.tag == 'nonpae':
					if 'pae' not in f_names:
						f_names.append('nonpae')
				elif child.attrib.get('default') == 'on' and child.tag in ('acpi', 'apic'):
					f_names.append(child.tag)
		return f_names

	def __init__(self, arch, domain_type, os_type, features):
		self.os_type = os_type
		self.features = features
		self.arch = arch.attrib['name']
		self.domain_type = domain_type.attrib['type']

		self.emulator = domain_type.findtext('emulator') or arch.findtext('emulator')
		for node in [domain_type, arch]:
			self.emulator = node.findtext('emulator')
			if self.emulator:
				break
		else:
			logger.error('No emulator specified in %s/%s' % (self.arch, self.domain_type))

		for node in [domain_type, arch]:
			self.machines = [m.text for m in node.findall('machine')]
			if self.machines:
				break
		else:
			logger.error('No machines specified in %s/%s' % (self.arch, self.domain_type))

		self.loader = arch.findtext('loader')

	def __str__(self):
		return 'DomainTemplate(arch=%s dom_type=%s os_type=%s): %s, %s, %s, %s' % (self.arch, self.domain_type, self.os_type, self.emulator, self.loader, self.machines, self.features)

	def matches(self, domain):
		'''Return True if domain matches os_type, arch and domain_type.'''
		return self.arch == domain.arch and self.domain_type == domain.domain_type and self.os_type == domain.os_type

class PersistentCached(object):
	"""Abstract class to implement caching."""
	def cache_file_name(self, suffix='.pic'):
		raise NotImplementedError()

	def cache_save(self, data):
		"""Save public data to cache."""
		new_name = self.cache_file_name(suffix='.new')
		old_name = self.cache_file_name()
		fd = os.open(new_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IREAD | stat.S_IWRITE)
		try:
			os.write(fd, data)
		finally:
			os.close(fd)
		os.rename(new_name, old_name)

	def cache_purge(self):
		"""Purge public data from cache."""
		old_name = self.cache_file_name()
		new_name = self.cache_file_name(suffix='.old')
		os.rename(old_name, new_name)

class Domain(PersistentCached):
	"""Container for domain statistics."""
	CPUTIMES = (10, 60, 5*60) # 10s 60s 5m
	def __init__(self, domain, node):
		self.node = node
		self._time_stamp = 0.0
		self._time_used = 0L
		self._cpu_usage = 0
		self._cache_id = None
		self.pd = Data_Domain()
		if isinstance(domain, libvirt.virDomain):
			self.pd.uuid = domain.UUIDString()
			self.pd.os_type = domain.OSType()
			self.update(domain)
		elif isinstance(domain, basestring): # XML
			self.xml2obj(domain)
		self.update_ldap()

	def __eq__(self, other):
		return self.pd.uuid == other.pd.uuid

	def update(self, domain):
		"""Update statistics which may change often."""
		if self.pd.name is None:
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
					exp = math.exp(-1.0 * delta_t / Domain.CPUTIMES[i])
					self.pd.cputime[i] *= exp
					self.pd.cputime[i] += (1.0 - exp) * self._cpu_usage
				else:
					self.pd.cputime[i] = self._cpu_usage
		self._time_stamp = now
		self.update_expensive(domain)

	def update_expensive(self, domain):
		"""Update statistics."""
		# Full XML definition
		xml = domain.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
		cache_id = hash(xml)
		if self._cache_id != cache_id:
			try:
				self.cache_save(xml)
				self._cache_id = cache_id
			except IOError, ex:
				logger.warning("Failed to cache domain %s: %s" % (self.pd.uuid, ex))
			self.xml2obj(xml)

		# Determine size and pool
		for dev in self.pd.disks:
			if not dev.source:
				continue
			try:
				conn = domain.connect()
				vol = conn.storageVolLookupByPath(dev.source)
				dev.size = vol.info()[1] # (type, capacity, allocation)
				pool = vol.storagePoolLookupByVolume()
				dev.pool = pool.name()
			except libvirt.libvirtError, ex:
				if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
					logger.warning('Failed to query disk %s#%s: %s', self.pd.uuid, dev.source, ex.get_error_message())

		# List of snapshots
		snapshots = None
		if self.node.pd.supports_snapshot:
					snapshots = {}
					for name in domain.snapshotListNames(0):
						snap = domain.snapshotLookupByName(name, 0)
						xml = snap.getXMLDesc(0)
						try:
							domainsnap_tree = ET.fromstring(xml)
						except ET.XMLSyntaxError:
							continue
						ctime = domainsnap_tree.findtext('creationTime')
						snap_stat = Data_Snapshot()
						snap_stat.name = name
						snap_stat.ctime = int(ctime)
						snapshots[name] = snap_stat
		self.pd.snapshots = snapshots

		# Suspend image
		if self.node.pd.supports_suspend:
			self.pd.suspended = domain.hasManagedSaveImage(0)
		else:
			self.pd.suspended = None

	def update_ldap(self):
		"""Update annotations from LDAP."""
		try:
			self.pd.annotations = ldap_annotation(self.pd.uuid)
		except LdapError:
			self.pd.annotations = {}

	def xml2obj(self, xml):
		"""Parse XML into python object."""
		try:
			domain_tree = ET.fromstring(xml)
		except ET.XMLSyntaxError:
			return
		devices = domain_tree.find('devices')
		self.pd.domain_type = domain_tree.attrib['type']
		if not self.pd.domain_type:
			logger.error("Failed /domain/@type from %s" % xml)
		self.pd.uuid = domain_tree.findtext('uuid')
		self.pd.name = domain_tree.findtext('name')
		os_ = domain_tree.find('os')
		if os_ is not None:
			typ = os_.find('type')
			if typ is not None:
				self.pd.os_type = typ.text
				if 'arch' in typ.attrib:
					self.pd.arch = typ.attrib['arch']
			self.pd.kernel = os_.findtext('kernel')
			self.pd.cmdline = os_.findtext('cmdline')
			self.pd.initrd = os_.findtext('initrd')
			self.pd.boot = [boot.attrib['dev'] for boot in os_.findall('boot')]
		bootloader = domain_tree.find('bootloader')
		if bootloader is not None:
			self.pd.bootloader = bootloader.text
			self.pd.bootloader_args = domain_tree.findtext('bootloader_args')
		clock = domain_tree.find('clock')
		if clock is not None:
			self.pd.rtc_offset = clock.attrib.get('offset')

		self.pd.disks = []
		for disk in devices.findall('disk'):
			dev = Disk()
			dev.type = disk.attrib['type']
			dev.device = disk.attrib['device']
			driver = disk.find('driver')
			if driver is not None:
				dev.driver = driver.attrib.get('name')  # optional
				dev.driver_type = driver.attrib['type']
				dev.driver_cache = driver.attrib.get('cache', '')  # optional
			source = disk.find('source')
			if source is not None:
				if dev.type == Disk.TYPE_FILE:
					dev.source = source.attrib['file']
				elif dev.type == Disk.TYPE_BLOCK:
					dev.source = source.attrib['dev']
				elif dev.type == Disk.TYPE_DIR:
					dev.source = source.attrib['dir']
				elif dev.type == Disk.TYPE_NETWORK:
					dev.source = source.attrib['protocol']
				else:
					raise NodeError(_('Unknown disk type: %(type)d'), type=dev.type)
			target = disk.find('target')
			if target is not None:
				dev.target_dev = target.attrib['dev']
				dev.target_bus = target.attrib.get('bus')  # optional
			if disk.find('readonly') is not None:
				dev.readonly = True

			self.pd.disks.append(dev)

		self.pd.interfaces = []
		for iface in devices.findall('interface'):
			dev = Interface()
			dev.type = iface.attrib['type']
			mac = iface.find('mac')
			if mac is not None:
				dev.mac_address = mac.attrib['address']
			source = iface.find('source')
			if source is not None:
				if dev.type == Interface.TYPE_BRIDGE:
					dev.source = source.attrib['bridge']
				elif dev.type == Interface.TYPE_NETWORK:
					dev.source = source.attrib['network']
				elif dev.type == Interface.TYPE_DIRECT:
					dev.source = source.attrib['dev']
			script = iface.find('script')
			if script is not None:
				dev.script = script.attrib['path']
			target = iface.find('target')
			if target is not None:
				dev.target = target.attrib['dev']
			model = iface.find('model')
			if model is not None:
				dev.model = model.attrib['type']

			self.pd.interfaces.append(dev)

		self.pd.graphics = []
		for graphic in devices.findall('graphics'):
			dev = Graphic()
			type = graphic.attrib['type']
			dev.type = type
			if dev.type == Graphic.TYPE_VNC:
				dev.port = int(graphic.attrib['port'])
				dev.autoport = graphic.attrib['autoport'].lower() == 'yes'
				try:
					dev.listen = graphic.attrib['listen']
				except LookupError:
					pass
				try:
					dev.passwd = graphic.attrib['passwd']
				except LookupError:
					pass
				dev.keymap = graphic.attrib['keymap']
			elif dev.type == Graphic.TYPE_SDL:
				pass
			else:
				logger.error('Unsupported graphics type: %s' % type)
			self.pd.graphics.append(dev)

	def key(self):
		"""Return a unique key for this domain and generation."""
		return hash((self.pd.uuid, self._time_stamp))

	def cache_file_name(self, uuid=None, suffix='.xml'):
		"""Return the path of the domain cache file."""
		if uuid is None:
			uuid = self.pd.uuid
		return os.path.join(self.node.cache_dom_dir(), uuid + suffix)

	def calc_cache_id(self):
		key = hash((self.pd.uuid, self.pd.name, self.pd.maxMem))
		for disk in self.pd.disks:
			key ^= hash((disk.target_dev, disk.source))
		for iface in self.pd.interfaces:
			key ^= hash((iface.mac_address, iface.source, iface.model))
		for gfx in self.pd.graphics:
			key ^= hash(gfx.port)
		return key

	def _vnc(self):
		"""
		Return (host, port) tuple for VNC connection, or None.
		"""
		try:
			gfx = self.pd.graphics[0]
		except (AttributeError, IndexError):
			return None
		if gfx.type != Graphic.TYPE_VNC:
			return None
		if gfx.port <= 0:
			return None
		if gfx.listen == '0.0.0.0':
			vnc_addr = self.node.pd.name
		elif (gfx.listen is None or gfx.listen == '127.0.0.1') and self.node.pd.name == FQDN:
			vnc_addr = '127.0.0.1'
		else:
			return None
		return (vnc_addr, gfx.port)


class _DomainDict(dict):
	"""Dictionary for handling domains of a node and their persistent cache."""
	def __delitem__(self, uuid):
		"""x.__delitem__(i) <==> del x[i]"""
		domStat = super(_DomainDict, self).pop(uuid)
		try:
			domStat.cache_purge()
		except OSError, ex:
			if ex.errno != errno.ENOENT:
				logger.warning("Failed to remove cached domain '%s#%s': %s", domStat.node.pd.uri, uuid, ex)

class Node(PersistentCached):
	"""Container for node statistics."""
	def __init__(self, uri, cache_dir=None):
		self.cache_dir = cache_dir
		self.domains = _DomainDict()
		self.conn = None
		self.libvirt_version = tuple2version((0, 8, 7))
		self.config_frequency = Nodes.IDLE_FREQUENCY
		self.current_frequency = Nodes.IDLE_FREQUENCY
		self.domainCB = None
		self.timerEvent = threading.Event()
		try:
			# Calculate base cache dir for node
			cache_dom_dir = self.cache_dom_dir(uri)
			try:
				os.mkdir(cache_dom_dir, 0700) # contains VNC password
			except OSError, ex:
				if ex.errno != errno.EEXIST:
					raise

			# Load cached node info
			cache_file_name = self.cache_file_name(uri)
			cache_file = open(cache_file_name, 'r')
			try:
				data = pickle.Unpickler(cache_file)
				assert data is not None
				self.pd = data.load()
			finally:
				cache_file.close()
			assert self.pd.uri == uri
			logger.debug("Loaded from cache '%s'", self.pd.uri)

			# Load cached domains info
			for root, dirs, files in os.walk(cache_dom_dir):
				for fname in files:
					if not fname.endswith('.xml'):
						continue
					cache_file_name = os.path.join(root, fname)
					try:
						cache_file = open(cache_file_name, 'r')
						try:
							xml = cache_file.read()
						finally:
							cache_file.close()
						assert xml
						assert isinstance(xml, basestring)
						domStat = Domain(xml, self)
						assert domStat.cache_file_name() == cache_file_name
						self.domains[domStat.pd.uuid] = domStat
						logger.debug("Loaded from cache '%s#%s'", self.pd.uri, domStat.pd.uuid)
					except (EOFError, IOError, AssertionError, ET.XMLSyntaxError) as ex:
						logger.warning("Failed to load cached domain %s: %s" % (cache_file_name, ex))
				del dirs[:] # just that direcory; no recursion
		except (EOFError, IOError, AssertionError, pickle.PickleError), ex:
			logger.warning("Failed to load cached state of %s: %s" % (uri, ex))
			self.pd = Data_Node() # public data
			self.pd.uri = uri
			self.pd.name = re.sub('^[^:]+://(?:[^/@]+@)?([^/]+).*', lambda m: m.group(1), uri)
		self._cache_id = self.calc_cache_id()

		# schedule periodic update
		self.timer = threading.Thread(group=None, target=self.run, name=self.pd.uri, args=(), kwargs={})
		self.timer.start()

	def run(self):
		"""Handle regular poll. Also checks connection liveness."""
		logger.info("timer_callback(%s) start" % (self.pd.uri,))
		try:
			while self.timer is not None:
				try:
					logger.debug("timer_callback: %s" % (self.pd.uri,))
					self.update_autoreconnect()
				except Exception:
					logger.error("%s: Exception in timer_callbck", (self.pd.uri,), exc_info=True)
					# don't crash the event handler
				self.timerEvent.clear()
				self.timerEvent.wait(self.current_frequency / 1000.0)
		finally:
			logger.debug("timer_callback(%s) terminated" % (self.pd.uri,))

	def update_autoreconnect(self):
		"""(Re-)connect after connection broke."""
		try:
			if self.conn is None:
				self.conn = libvirt.open(self.pd.uri)
				logger.info("Connected to '%s'" % (self.pd.uri,))
				self.update_once()
				self._register_default_pool()
				# reset timer after successful re-connect
				self.current_frequency = self.config_frequency
			self.update()
			self.pd.last_try = self.pd.last_update = time.time()
		except libvirt.libvirtError, ex:
			self.pd.last_try = time.time()
			# double timer interval until maximum
			hz = min(self.current_frequency * 2, Nodes.BEBO_FREQUENCY)
			logger.warning("'%s' broken? next check in %s. %s" % (self.pd.uri, ms(hz), ex))
			if hz > self.current_frequency:
				self.current_frequency = hz
			if self.conn is not None:
				try:
					self.conn.domainEventDeregister(self.domainCB)
				except Exception:
					logger.error("%s: Exception in domainEventDeregister" % (self.pd.uri,), exc_info=True)
				self.domainCB = None
				try:
					self.conn.close()
				except Exception:
					logger.error('%s: Exception in conn.close' % (self.pd.uri,), exc_info=True)
				self.conn = None

	def __eq__(self, other):
		return (self.pd.uri, self.pd.name) == (other.pd.uri, other.pd.name)

	def __del__(self):
		"""Free Node and deregister callbacks."""
		self.unregister()
		del self.pd
		del self.domains

	def _register_default_pool( self ):
		'''create a default storage pool if not available'''
		try:
			get_pool_info(self, 'default')
			logger.debug("default pool already registered on %s" % self.pd.name)
		except KeyError:
			logger.info("creating default pool on %s" % self.pd.name)
			create_storage_pool(
					self.conn,
					configRegistry.get('uvmm/pool/default/path', '/var/lib/libvirt/images')
					)

	def update_once(self):
		"""Update once on (re-)connect."""
		self.pd.name = self.conn.getHostname()
		info = self.conn.getInfo()
		self.pd.phyMem = long(info[1]) << 20 # MiB
		self.pd.cpus = info[2]
		self.pd.cores = tuple(info[4:8])
		xml = self.conn.getCapabilities()
		self.pd.capabilities = DomainTemplate.list_from_xml(xml)
		self.pd.supports_suspend = True
		self.pd.supports_snapshot = True
		self.libvirt_version = self.conn.getLibVersion()

		def domain_callback(conn, dom, event, detail, node):
			"""Handle domain addition, update and removal."""
			try:
				eventStrings = ("Added", "Removed", "Started", "Suspended", "Resumed", "Stopped", "Saved", "Restored")
				logger.debug("domain_callback %s(%s) %s %d" % (dom.name(), dom.ID(), eventStrings[event], detail))
				uuid = dom.UUIDString()
				if event == libvirt.VIR_DOMAIN_EVENT_DEFINED:
					domStat = Domain(dom, node=self)
					self.domains[uuid] = domStat
				elif event == libvirt.VIR_DOMAIN_EVENT_UNDEFINED:
					try:
						del self.domains[uuid]
					except KeyError:
						pass
				else: # VIR_DOMAIN_EVENT_STARTED _SUSPENDED _RESUMED _STOPPED
					try:
						domStat = self.domains[uuid]
						domStat.update( dom )
						self.write_novnc_tokens()
					except KeyError:
						# during migration events are not ordered causal
						pass
			except Exception:
				logger.error('%s: Exception handling callback' % (self.pd.uri,), exc_info=True)
				# don't crash the event handler

		self.conn.domainEventRegister(domain_callback, self)
		self.domainCB = domain_callback

	def unregister(self, wait=False):
		"""Unregister callbacks doing updates."""
		if self.timer is not None:
			timer = self.timer
			self.timer = None
			self.timerEvent.set()
			while wait:
				timer.join(1.0) # wait for up to 1 second until Thread terminates
				if timer.isAlive():
					logger.debug("timer still alive: %s" % (self.pd.uri,))
				else:
					wait = False
		if self.domainCB is not None:
			self.conn.domainEventDeregister(self.domainCB)
			self.domainCB = None
		if self.conn is not None:
			self.conn.close()
			self.conn = None

	def set_frequency(self, hz):
		"""Set polling frequency for update."""
		self.config_frequency = hz
		self.current_frequency = hz
		self.timerEvent.set()

	def update(self):
		"""Update node statistics."""
		curMem = 0
		maxMem = 0
		cpu_usage = 0
		cached_domains = self.domains.keys()
		def all_domains():
			for dom_id in self.conn.listDomainsID():
				yield self.conn.lookupByID(dom_id)
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

		cache_id = self.calc_cache_id()
		if self._cache_id != cache_id:
			try:
				data = pickle.dumps(self.pd)
				self.cache_save(data)
				self._cache_id = cache_id
			except IOError, ex:
				logger.exception("Failed to write cached node %s: %s" % (self.pd.uri, ex))
			self.write_novnc_tokens()

	def write_novnc_tokens(self):
		token_dir = os.path.join(self.cache_dir, 'novnc.tokens')
		path = os.path.join(token_dir, uri_encode(self.pd.uri))
		logger.debug("Writing noVNC tokens to '%s'", path)
		with tempfile.NamedTemporaryFile(delete=False, dir=token_dir) as tmp_file:
			for uuid, domStat in self.domains.iteritems():
				try:
					host, port = domStat._vnc()
					print >> tmp_file, '%s: %s:%d' % (uuid, host, port)
				except TypeError:
					continue
		os.rename(tmp_file.name, path)

	def wait_update(self, domain, state_key, timeout=10):
		"""Wait until domain gets updated."""
		while timeout > 0:
			try:
				if state_key != self.domains[domain].key():
					break
			except KeyError:
				pass
			time.sleep(1)
			timeout -= 1
		else:
			logger.warning('Timeout waiting for update.')

	def calc_cache_id(self):
		"""Calculate key for disk cache."""
		key = hash((
			self.pd.phyMem,
			self.pd.cores,
			self.pd.supports_suspend,
			self.pd.supports_snapshot,
		))
		for dom in self.domains.values():
			key ^= dom.calc_cache_id()
		return key

	def cache_file_name(self, uri=None, suffix='.pic'):
		"""Return the path of the node cache file."""
		if uri is None:
			uri = self.pd.uri
		return os.path.join(self.cache_dir, uri_encode(uri) + suffix)

	def domain_list( self, pattern = '*' ):
		regex = re.compile( fnmatch.translate( pattern ), re.IGNORECASE )
		domains = []
		for dom in self.domains:
			pd = self.domains[ dom ].pd
			contact = pd.annotations.get( 'contact', '' )
			name = pd.name
			descr = pd.annotations.get( 'description', '' )
			if regex.match( name ) is not None or regex.match( contact )  is not None or regex.match( descr ) is not None:
				vnc = self.domains[dom]._vnc()
				domains.append({
					'uuid': pd.uuid,
					'name': pd.name,
					'state': STATES[pd.state],
					'mem': pd.maxMem,
					'cpu_usage': pd.cputime[0],
					'vnc': bool(vnc),
					'vnc_port': vnc[1] if vnc else -1,
					'suspended': pd.suspended,
					'description': descr,
					'node_available': self.pd.last_try == self.pd.last_update
					})

		return domains

	def cache_dom_dir(self, uri=None):
		"""Return the path of the domain cache directory of the node."""
		return self.cache_file_name(uri, suffix='.d')

class Nodes(dict):
	"""Handle registered nodes."""
	IDLE_FREQUENCY = 15*1000 # ms
	USED_FREQUENCY = 10*1000 # ms
	BEBO_FREQUENCY = 5*60*1000 # ms

	def __init__(self):
		super(Nodes, self).__init__()
		self.cache_dir = None

	def __delitem__(self, uri):
		"""x.__delitem__(i) <==> del x[i]"""
		self[uri].unregister()
		super(Nodes, self).__delitem__(uri)

	def set_frequency(self, hz):
		"""Set polling frequency for update."""
		for node in self.values():
			node.set_frequency(hz)

	def set_cache(self, cache):
		"""Register a cache."""
		self.cache_dir = cache

	def add(self, uri):
		"""Add node to watch list."""
		if uri in self:
			raise NodeError(_('Hypervisor "%(uri)s" is already connected.'), uri=uri)

		node = Node(uri, cache_dir=self.cache_dir)
		self[uri] = node

		logger.debug("Hypervisor '%s' added." % (uri,))

	def remove(self, uri):
		"""Remove node from watch list."""
		try:
			del self[uri]
		except KeyError:
			raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)
		logger.debug("Hypervisor '%s' removed." % (uri,))

	def query(self, uri):
		"""Get domain data from node."""
		try:
			node = self[uri]
			return node
		except KeyError:
			raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)

	def frequency(self, hz=IDLE_FREQUENCY, uri=None):
		"""Set frequency for polling nodes."""
		if uri is None:
			self.set_frequency(hz)
		else:
			node = self.query(uri)
			node.set_frequency(hz)

	def list( self, group, pattern ):
		"""Return list of watched nodes matching the given pattern."""
		nodes = []
		if group == 'default' or group is None: # FIXME
			pattern_regex = re.compile( fnmatch.translate( pattern ), re.IGNORECASE )
			for node_uri in self.keys():
				if pattern_regex.match( node_uri ) is not None:
					nodes.append( self[ node_uri ].pd )
		return nodes

nodes = Nodes()
node_add = nodes.add
node_remove = nodes.remove
node_query = nodes.query
node_frequency = nodes.frequency
node_list = nodes.list

def group_list():
	"""Return list of groups for nodes."""
	group = []
	if (len(node_list('default','*')) > 0):
		group.append('default')
	from univention.uvmm.cloudnode import cloudconnections
	if (len(cloudconnections.list()) > 0):
		group.append('cloudconnections')
	return group

def _domain_backup(dom, save=True):
	"""Save domain definition to backup file."""
	backup_dir = configRegistry.get('uvmm/backup/directory', '/var/backups/univention-virtual-machine-manager-daemon')
	uuid = dom.UUIDString()
	xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
	if len(xml) < 300: # minimal XML descriptor length
		logger.error("Failed to backup domain %s: %s" % (uuid, xml))
		raise NodeError(_("Failed to backup domain %(domain)s: %(xml)s"), domain=uuid, xml=xml)
	now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
	suffix = 'xml'
	if save:
		suffix += '.save'
	tmp_file_name = os.path.join(backup_dir, "%s_%s.%s" % (uuid, now, suffix))
	file = os.path.join(backup_dir, "%s.%s" % (uuid, suffix))
	umask = os.umask(0177)
	tmp_file = open(tmp_file_name, "w")
	try:
		tmp_file.write(xml)
	finally:
		tmp_file.close()
	os.umask(umask)
	os.rename(tmp_file_name, file)
	logger.info("Domain backuped to %s." % (file,))

def __update_xml(_node_parent, _node_name, _node_value, _changes=set(), **attr):
	'''Create, update or delete node named '_node_name' of '_node_parent'.
	If _node_value == None and all(attr == None), then node is deleted.
	'''
	node = _node_parent.find(_node_name)
	if _node_value is None and not filter(lambda v: v is not None, attr.values()):
		if node is not None:
			_changes.add(None)
			_node_parent.remove(node)
	else:
		if node is None:
			node = ET.SubElement(_node_parent, _node_name)
		new_text = _node_value or None
		if node.text != new_text:
			_changes.add(None)
			node.text = new_text
		for k, v in attr.items():
			if v is None or v == '':
				if k in node.attrib:
					_changes.add(k)
					del node.attrib[k]
			elif node.attrib.get(k) != v:
				_changes.add(k)
				node.attrib[k] = v
	return node

def _domain_edit(node, dom_stat, xml):
	"""Apply python object 'dom_stat' to an XML domain description."""
	if xml:
		defaults = False
	else:
		xml = '<domain/>'
		defaults = True
	live_updates = []
	update = __update_xml

	# find loader
	logger.debug('Searching for template: arch=%s domain_type=%s os_type=%s' % (dom_stat.arch, dom_stat.domain_type, dom_stat.os_type))
	for template in node.pd.capabilities:
		logger.debug('template: %s' % template)
		if template.matches(dom_stat):
			break
	else:
		template = None

	# /domain @type
	domain = ET.fromstring(xml)
	domain.attrib['type'] = dom_stat.domain_type
	# /domain/uuid
	domain_uuid = update(domain, 'uuid', dom_stat.uuid)
	# /domain/name
	domain_name = update(domain, 'name', dom_stat.name)
	# /domain/description
	description = dom_stat.annotations.get('description') or None
	domain_description = update(domain, 'description', description)
	# /domain/os
	domain_os = domain.find('os')
	if domain_os is None:
		domain_os = ET.SubElement(domain, 'os')
	# /domain/os/type @arch
	domain_os_type = update(domain_os, 'type', dom_stat.os_type, arch=dom_stat.arch)
	# /domain/os/loader
	if defaults and template and template.loader:
		domain_os_loader = update(domain_os, 'loader', template.loader)
	if dom_stat.os_type == 'hvm':
		# /domain/os/boot[]
		domain_os_boots = domain_os.findall('boot')
		boot = {}
		for domain_os_boot in domain_os_boots:
			dev = domain_os_boot.attrib['dev']
			boot[dev] = domain_os_boot
			domain_os.remove(domain_os_boot)
		for dev in dom_stat.boot:
			try:
				domain_os_boot = boot[dev]
				domain_os.append(domain_os_boot)
			except LookupError:
				domain_os_boot = ET.SubElement(domain_os, 'boot', dev=dev)
	else:
		raise NodeError(_("Unknown os/type='%(type)s'"), type=dom_stat.os_type)
	if dom_stat.bootloader:
		# /domain/bootloader
		domain_bootloader = update(domain, 'bootloader', dom_stat.bootloader)
		# /domain/bootloader_args
		domain_bootloader_args = update(domain, 'bootloader_args', dom_stat.bootloader_args)
	# /domain/memory
	try:
		old_maxMem = int(domain.find('memory').text) << 10 # KiB
	except:
		old_maxMem = -1
	domain_memory = update(domain, 'memory', '%d' % (dom_stat.maxMem >> 10)) # KiB
	# On change, reset currentMemory to new maxMem as well
	if old_maxMem != dom_stat.maxMem:
		# /domain/currentMemory
		domain_currentMemory = update(domain, 'currentMemory', '%d' % (dom_stat.maxMem >> 10)) # KiB
	# /domain/vcpu
	domain_vcpu = update(domain, 'vcpu', '%d' % dom_stat.vcpus)

	# /domain/features
	if defaults and template and template.features:
		domain_features = update(domain, 'features', '')
		for f_name in template.features:
			domain_features_x = update(domain_features, f_name, '')

	# /domain/clock @offset @timezone @adjustment
	if dom_stat.rtc_offset in ('utc', 'localtime'):
		domain_clock = update(domain, 'clock', '', offset=dom_stat.rtc_offset, timezone=None, adjustment=None, basis=None)
	elif dom_stat.rtc_offset == 'variable':
		domain_clock = update(domain, 'clock', '', offset=dom_stat.rtc_offset, timezone=None)
	elif dom_stat.rtc_offset:
		domain_clock = update(domain, 'clock', '', offset=dom_stat.rtc_offset) # timezone='', adjustment=0
	# /domain/on_poweroff
	if defaults:
		domain_on_poweroff = update(domain, 'on_poweroff', 'destroy') # (destroy|restart|preserve|rename-restart)
	# /domain/on_reboot
	if defaults:
		domain_on_reboot = update(domain, 'on_reboot', 'restart') # (destroy|restart|preserve|rename-restart)
	# /domain/on_crash
	if defaults:
		domain_on_crash = update(domain, 'on_crash', 'destroy') # (destroy|restart|preserve|rename-restart)

	# /domain/devices/*[]
	domain_devices = update(domain, 'devices', '')

	# /domain/devices/emulator
	if defaults and template and template.emulator:
		domain_devices_emulator = update(domain_devices, 'emulator', template.emulator)

	# /domain/devices/disk[]
	domain_devices_disks = domain_devices.findall('disk')
	disks = {}
	for domain_devices_disk in domain_devices_disks:
		domain_devices_disk_target = domain_devices_disk.find('target')
		bus = domain_devices_disk_target.attrib['bus']
		dev = domain_devices_disk_target.attrib['dev']
		key = (bus, dev)
		disks[key] = domain_devices_disk
		domain_devices.remove(domain_devices_disk)
	for disk in dom_stat.disks:
		logger.debug('DISK: %s' % disk)
		changes = set()
		# /domain/devices/disk @type @device
		try:
			key = (disk.target_bus, disk.target_dev)
			domain_devices_disk = disks[key]
			domain_devices.append(domain_devices_disk)
		except LookupError:
			domain_devices_disk = ET.SubElement(domain_devices, 'disk')
			# /domain/devices/disk/target @bus @dev
			domain_devices_disk_target = ET.SubElement(domain_devices_disk, 'target')
			domain_devices_disk_target.attrib['bus'] = disk.target_bus
			domain_devices_disk_target.attrib['dev'] = disk.target_dev
		domain_devices_disk.attrib['type'] = disk.type
		domain_devices_disk.attrib['device'] = disk.device
		# /domain/devices/disk/driver @name @type @cache
		domain_devices_disk_driver = update(domain_devices_disk, 'driver', None, name=disk.driver, type=disk.driver_type, cache=disk.driver_cache)
		# /domain/devices/disk/source @file @dev
		if disk.type == Disk.TYPE_FILE:
			domain_devices_disk_source = update(domain_devices_disk, 'source', None, _changes=changes, file=disk.source, dev=None, dir=None, protocol=None)
		elif disk.type == Disk.TYPE_BLOCK:
			domain_devices_disk_source = update(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=disk.source, dir=None, protocol=None)
		elif disk.type == Disk.TYPE_DIR:
			domain_devices_disk_source = update(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=None, dir=disk.source, protocol=None)
		elif disk.type == Disk.TYPE_NETWORK:
			domain_devices_disk_source = update(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=None, dir=None, protocol=disk.source)
		else:
			raise NodeError(_("Unknown disk/type='%(type)s'"), type=disk.type)
		# /domain/devices/disk/readonly
		domain_devices_disk_readonly = domain_devices_disk.find('readonly')
		if disk.readonly:
			if domain_devices_disk_readonly is None:
				ET.SubElement(domain_devices_disk, 'readonly')
		else:
			if domain_devices_disk_readonly is not None:
				domain_devices_disk.remove(domain_devices_disk_readonly)
		# do live update
		if changes:
			live_updates.append(domain_devices_disk)

	# /domain/devices/interface[]
	domain_devices_interfaces = domain_devices.findall('interface')
	interfaces = {}
	for domain_devices_interface in domain_devices_interfaces:
		domain_devices_interface_mac = domain_devices_interface.find('mac')
		key = domain_devices_interface_mac.attrib['address']
		interfaces[key] = domain_devices_interface
		domain_devices.remove(domain_devices_interface)
	for interface in dom_stat.interfaces:
		logger.debug('INTERFACE: %s' % interface)
		changes = set()
		# /domain/devices/interface @type @device
		try:
			key = interface.mac_address
			domain_devices_interface = interfaces[key]
			domain_devices.append(domain_devices_interface)
		except LookupError:
			domain_devices_interface = ET.SubElement(domain_devices, 'interface')
			# /domain/devices/interface/mac @address
			domain_devices_interface_mac = ET.SubElement(domain_devices_interface, 'mac')
			domain_devices_interface_mac.attrib['address'] = interface.mac_address
		domain_devices_interface.attrib['type'] = interface.type
		# /domain/devices/interface/source @bridge @network @dev
		if interface.type == Interface.TYPE_BRIDGE:
			domain_devices_interface_source = update(domain_devices_interface, 'source', '', _changes=changes, bridge=interface.source, network=None, dev=None)
		elif interface.type == Interface.TYPE_NETWORK:
			domain_devices_interface_source = update(domain_devices_interface, 'source', '', _changes=changes, bridge=None, network=interface.source, dev=None)
		elif interface.type == Interface.TYPE_ETHERNET:
			domain_devices_interface_source = update(domain_devices_interface, 'source', None, _changes=changes, bridge=None, network=None, dev=interface.source)
		elif interface.type == Interface.TYPE_DIRECT:
			domain_devices_interface_source = update(domain_devices_interface, 'source', '', _changes=changes, bridge=None, network=None, dev=interface.source)
		else:
			raise NodeError(_("Unknown interface/type='%(type)s'"), type=interface.type)
		# /domain/devices/interface/script @bridge
		domain_devices_interface_script = update(domain_devices_interface, 'script', None, path=interface.script)
		# /domain/devices/interface/target @dev
		domain_devices_interface_target = update(domain_devices_interface, 'target', None, dev=interface.target)
		# /domain/devices/interface/model @dev
		domain_devices_interface_model = update(domain_devices_interface, 'model', None, type=interface.model)
		# do live update
		if changes:
			live_updates.append(domain_devices_interface)

	# /domain/devices/input @type @bus
	if dom_stat.os_type == 'hvm':
		# define a tablet usb device which has absolute cursor movement for a better VNC experience. Bug #19244
		domain_devices_inputs = domain_devices.findall('input')
		for domain_devices_input in domain_devices_inputs:
			if domain_devices_input.attrib['type'] == 'tablet' and domain_devices_input.attrib['bus'] == 'usb':
				break
		else:
			domain_devices_input = ET.SubElement(domain_devices, 'input', type='tablet', bus='usb')

	# /domain/devices/graphics[]
	domain_devices_graphics = domain_devices.findall('graphics')
	for domain_devices_graphic in domain_devices_graphics:
		domain_devices.remove(domain_devices_graphic)
	for graphics in dom_stat.graphics:
		logger.debug('GRAPHIC: %s' % graphics)
		# /domain/devices/graphics @type
		key = graphics.type
		for domain_devices_graphic in domain_devices_graphics:
			if key == domain_devices_graphic.attrib['type']:
				domain_devices.append(domain_devices_graphic)
				break
		else:
			domain_devices_graphic = ET.SubElement(domain_devices, 'graphics', type=key)
		# /domain/devices/graphics @autoport
		if graphics.autoport:
			domain_devices_graphic.attrib['autoport'] = 'yes'
		else:
			domain_devices_graphic.attrib['autoport'] = 'no'
		# /domain/devices/graphics @port @keymap @listen @passwd
		domain_devices_graphic.attrib['port'] = '%d' % graphics.port
		domain_devices_graphic.attrib['keymap'] = graphics.keymap
		domain_devices_graphic.attrib['listen'] = graphics.listen
		if node.libvirt_version >= tuple2version((0, 9, 4)):
			domain_devices_graphic_listens = domain_devices_graphic.findall('listen')
			for listen in domain_devices_graphic_listens:
				if listen.attrib['type'] != 'address':
					continue
				if graphics.listen:
					listen.attrib['address'] = graphics.listen
				else:
					domain_devices_graphic.remove(listen)
		domain_devices_graphic.attrib['listen'] = graphics.listen
		if domain_devices_graphic.attrib.get('passwd') != graphics.passwd:
			domain_devices_graphic.attrib['passwd'] = graphics.passwd
			live_updates.append(domain_devices_graphic)

	if dom_stat.domain_type in ('kvm', 'qemu'):
		models = set()
		for iface in dom_stat.interfaces:
			model = getattr(iface, 'model', None) or 'rtl8139'
			models.add(model)
		if 'network' not in dom_stat.boot: # qemu-kvm_0.12.4 ignores boot-order and always prefers Network
			models = set()
		models &= set(['e1000', 'ne2k_isa', 'ne2k_pci', 'pcnet', 'rtl8139', 'virtio'])
		roms = set(['%s-%s.bin' % (QEMU_PXE_PREFIX, model) for model in models])

	# Make ET happy and cleanup None values
	for n in domain.getiterator():
		for k, v in n.attrib.items():
			if v is None or v == '':
				del n.attrib[k]
			elif not isinstance(v, basestring):
				n.attrib[k] = '%s' % v

	xml = ET.tostring(domain)
	updates_xml = [ET.tostring(device) for device in live_updates]
	return (xml, updates_xml)

def domain_define( uri, domain ):
	"""Convert python object to an XML document."""
	node = node_query(uri)
	conn = node.conn
	logger.debug('PY DUMP: %r' % domain.__dict__)

	# Check for (name,uuid) collision
	old_dom = None
	old_xml = None
	try:
		old_dom = conn.lookupByName(domain.name)
		old_uuid = old_dom.UUIDString()
		if old_uuid != domain.uuid:
			raise NodeError(_('Domain name "%(domain)s" already used by "%(uuid)s"'), domain=domain.name, uuid=old_uuid)
		old_xml = old_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
	except libvirt.libvirtError, ex:
		if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
			logger.error(ex)
			raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.name, error=ex.get_error_message())
		# rename: name changed, uuid unchanged
		try:
			if domain.uuid:
				old_dom = conn.lookupByUUIDString(domain.uuid)
				old_xml = old_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(ex)
				raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.uuid, error=ex.get_error_message())

	old_stat = None
	warnings = []
	if domain.uuid:
		try:
			dom = node.domains[domain.uuid]
		except KeyError:
			pass # New domain with pre-configured UUID
		else:
			old_stat = dom.key()

	new_xml, live_updates = _domain_edit(node, domain, old_xml)

	# create new disks
	logger.debug('DISKS: %s' % domain.disks)
	for disk in domain.disks:
		if disk.device == Disk.DEVICE_DISK:
			try:
				# FIXME: If the volume is outside any pool, ignore error
				create_storage_volume(conn, domain, disk)
			except StorageError, ex:
				raise NodeError(ex)

	# update running domain definition
	if old_dom and live_updates:
		try:
			if old_dom.isActive():
				for xml in live_updates:
					try:
						logger.debug('DEVICE_UPDATE: %s' % xml)
						rv = old_dom.updateDeviceFlags(
								xml, (
									libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE |
									libvirt.VIR_DOMAIN_DEVICE_MODIFY_CONFIG
									)
								)
						if rv != 0:
							warnings.append(_('Failed to update device.'))
					except libvirt.libvirtError, ex:
						if ex.get_error_code() == libvirt.VIR_ERR_OPERATION_INVALID:
							pass
						elif ex.get_error_code() == libvirt.VIR_ERR_OPERATION_FAILED:
							# could not change media on drive-ide0-0-0: Device 'drive-ide0-0-0' is locked\r\n
							raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=ex.get_error_message())
						elif ex.get_error_code() == libvirt.VIR_ERR_SYSTEM_ERROR:
							# unable to open disk path /dev/cdrom: No medium found
							raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=ex.get_error_message())
						else:
							raise
		except libvirt.libvirtError, ex:
			logger.error(ex)
			raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=ex.get_error_message())

	# remove old domain definitions
	if old_dom:
		try:
			_domain_backup(old_dom)
			if old_dom.name() != domain.name: # rename needs undefine
				try: # all snapshots are destroyed!
					old_dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA) # all snapshots are destroyed!
				except libvirt.libvirtError, ex:
					if ex.get_error_code() not in (libvirt.VIR_ERR_NO_SUPPORT, libvirt.VIR_ERR_INVALID_ARG):
						raise
					old_dom.undefine()
				logger.info('Old domain "%s" removed.' % (domain.uuid,))
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(ex)
				raise NodeError(_('Error removing domain "%(domain)s": %(error)s'), domain=domain.uuid, error=ex.get_error_message())

	try:
		logger.debug('XML DUMP: %s' % new_xml.replace('\n', ' '))
		dom2 = conn.defineXML(new_xml)
		domain.uuid = dom2.UUIDString()
		_domain_backup(dom2, save=False)
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error defining domain "%(domain)s": %(error)s'), domain=domain.name, error=ex.get_error_message())
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
		except LdapConnectionError, ex:
			logger.error('Updating LDAP failed, insufficient permissions: %s' % (ex,))
			warnings.append( _( 'Failed to update the additionally information in the LDAP directory.' ) )
		except ( univention.admin.uexceptions.ldapError, univention.admin.uexceptions.objectExists ), ex:
			logger.error('Updating LDAP failed: %s %s' % (ex, record))
			warnings.append( _( 'Failed to update the additionally information in the LDAP directory.' ) )

	node.wait_update(domain.uuid, old_stat)

	return ( domain.uuid, warnings )

def domain_list( uri, pattern = '*' ):
	"""Returns a dictionary of domains matching the pattern in name, contact or description.

	return: { 'nodeY' : [ ( <uuid>, <domain name> ), ... ], ... }
	"""
	global nodes

	if uri in ('*', ''):
		node_list = nodes.values()
	else:
		node_list = [ node_query(uri) ]

	domains = {}
	for node in node_list:
		domains[ node.pd.uri ] = node.domain_list( pattern )

	return domains

def domain_info( uri, domain ):
	"""Return detailed information of a domain."""
	node = node_query( uri )
	# transfer state number into string constant
	if not domain in node.domains:
		raise NodeError( _( 'Unknown domain "%s"' ) % domain )
	domain_pd = copy.copy( node.domains[ domain ].pd )
	domain_pd.state = STATES[ domain_pd.state ]
	domain_pd.available = node.pd.last_try == node.pd.last_update

	return domain_pd

def domain_state(uri, domain, state):
	"""Change running state of domain on node and wait for updated state."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		stat_key = dom_stat.key()
		try:
			TRANSITION = {
					(libvirt.VIR_DOMAIN_RUNNING,  'PAUSE'   ): dom.suspend,
					(libvirt.VIR_DOMAIN_RUNNING,  'RESTART' ): lambda:dom.reboot(0),
					(libvirt.VIR_DOMAIN_RUNNING,  'RUN'     ): None,
					(libvirt.VIR_DOMAIN_RUNNING,  'SHUTDOWN'): dom.shutdown,
					(libvirt.VIR_DOMAIN_RUNNING,  'SHUTOFF' ): dom.destroy,
					(libvirt.VIR_DOMAIN_RUNNING,  'SUSPEND' ): lambda:dom.managedSave(0),
					(libvirt.VIR_DOMAIN_BLOCKED,  'PAUSE'   ): dom.suspend,
					(libvirt.VIR_DOMAIN_BLOCKED,  'RESTART' ): lambda:dom.reboot(0),
					(libvirt.VIR_DOMAIN_BLOCKED,  'RUN'     ): None,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SHUTDOWN'): dom.shutdown,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SHUTOFF' ): dom.destroy,
					(libvirt.VIR_DOMAIN_BLOCKED,  'SUSPEND' ): lambda:dom.managedSave(0),
					(libvirt.VIR_DOMAIN_PAUSED,   'PAUSE'   ): None,
					(libvirt.VIR_DOMAIN_PAUSED,   'RUN'     ): dom.resume,
					(libvirt.VIR_DOMAIN_PAUSED,   'SHUTDOWN'): dom.destroy,
					(libvirt.VIR_DOMAIN_PAUSED,   'SHUTOFF' ): dom.destroy,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTOFF' ): None,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'SHUTDOWN'): None,
					(libvirt.VIR_DOMAIN_SHUTOFF,  'SHUTOFF' ): None,
					(libvirt.VIR_DOMAIN_CRASHED,  'RUN'     ): dom.create,
					(libvirt.VIR_DOMAIN_CRASHED,  'SHUTDOWN'): None, # TODO destroy?
					(libvirt.VIR_DOMAIN_CRASHED,  'SHUTOFF' ): None, # TODO destroy?
					}
			transition = TRANSITION[(dom_stat.pd.state, state)]
		except KeyError:
			cur_state = STATES[dom_stat.pd.state]
			raise NodeError(_('Unsupported state transition %(cur_state)s to %(next_state)s'), cur_state=cur_state, next_state=state)

		if transition:
			if state == 'RUN':
				# if interfaces of type NETWORK exist, verify that the network is active
				for nic in dom_stat.pd.interfaces:
					if nic.type == Interface.TYPE_NETWORK:
						network_start( conn, nic.source )
					elif nic.type == Interface.TYPE_BRIDGE:
						network = network_find_by_bridge( conn, nic.source )
						if network:
							network_start( conn, network.name )
			# Detect if VNC is wanted
			wait_for_vnc = state in ('RUN', 'PAUSE') and any(True for dev in dom_stat.pd.graphics if dev.type == Graphic.TYPE_VNC)
			transition()
			ignore_states = [libvirt.VIR_DOMAIN_NOSTATE]
			if state == 'RUN':
				ignore_states.append(libvirt.VIR_DOMAIN_PAUSED)
			for t in range(20):
				cur_state = dom.info()[0]
				if cur_state not in ignore_states:
					# do update explicitly
					dom_stat.pd.state = cur_state
					break
				time.sleep(1)
			# wait for update
			node.wait_update(domain, stat_key)
			if wait_for_vnc:
				# wait <=3*10s until port is known
				for t in range(3):
					if any(True for dev in dom_stat.pd.graphics if dev.type == Graphic.TYPE_VNC and 0 <= dev.port < (1<<16)):
						break
					logger.info('Still waiting for VNC of %s...' % domain)
					stat_key = dom_stat.key()
					node.wait_update(domain, stat_key)
	except KeyError, ex:
		logger.error("Domain %s not found" % (ex,))
		raise NodeError(_('Error managing domain "%(domain)s"'), domain=domain)
	except NetworkError, ex:
		logger.error(ex)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=str(ex))
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())

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
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error saving domain "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())

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
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error restoring domain "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())

def domain_undefine(uri, domain, volumes=[]):
	"""Undefine a domain and its volumes on a node."""
	try:
		node = node_query(uri)
		conn = node.conn
		dom = conn.lookupByUUIDString(domain)
		_domain_backup(dom)
		if volumes is None:
			volumes = get_domain_storage_volumes(dom)
		destroy_storage_volumes(conn, volumes, ignore_error=True)
		try:
			if dom.hasManagedSaveImage(0):
				dom.managedSaveRemove(0)
		except libvirt.libvirtError, ex:
			# libvirt returns an 'internal error' when no save image exists
			if ex.get_error_code() != libvirt.VIR_ERR_INTERNAL_ERROR:
				logger.debug(ex)
		del node.domains[domain]
		try:
			dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)
		except libvirt.libvirtError, ex:
			if ex.get_error_code() not in (libvirt.VIR_ERR_NO_SUPPORT, libvirt.VIR_ERR_INVALID_ARG):
				raise
			dom.undefine()
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error undefining domain "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())

def domain_migrate(source_uri, domain, target_uri):
	"""Migrate a domain from node to the target node."""
	try:
		source_node = node_query(source_uri)
		source_conn = source_node.conn
		if source_conn is not None:
			source_dom = source_conn.lookupByUUIDString(domain)
			for t in range(10):
				source_state = source_dom.info()[0]
				if source_state != libvirt.VIR_DOMAIN_NOSTATE:
					break
				time.sleep(1)
		target_node = node_query(target_uri)
		target_conn = target_node.conn

		if source_conn is None: # offline node
			domStat = source_node.domains[domain]
			try:
				cache_file_name = domStat.cache_file_name()
				cache_file = open(cache_file_name, 'r')
				try:
					xml = cache_file.read()
				finally:
					cache_file.close()
				target_conn.defineXML(xml)
			except IOError, ex:
				raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=ex)
		elif source_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED):
			# running domains are live migrated
			flags = libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_PERSIST_DEST | libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
			target_dom = source_dom.migrate(target_conn, flags, None, None, 0)
		elif source_state in (libvirt.VIR_DOMAIN_SHUTDOWN, libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			# for domains not running their definition is migrated
			xml = source_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
			target_dom = target_conn.defineXML(xml)
			source_dom.undefine()
		else:
			raise NodeError(_('Domain "%(domain)s" in state "%(state)s" can not be migrated'), domain=domain, state=STATES[source_state])

		# Updates are handled via the callback mechanism, but remove domain
		# info as soon as possible to not show stale data
		try:
			del source_node.domains[domain]
		except KeyError:
			pass
		#target_node.domains[domain] = Domain(target_dom, node=target_node)
		for t in range(20):
			if (domain not in source_node.domains and
					domain in target_node.domains and
					target_node.domains[domain].pd.state != libvirt.VIR_DOMAIN_PAUSED):
				break
			time.sleep(1)
		else:
			logger.warning('Domain "%(domain)s" still not migrated from "%(source)s" to "%(target)s"' % {'domain':domain, 'source':source_uri, 'target':target_uri})
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())

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
		xml = '''<domainsnapshot><name>%s</name></domainsnapshot>''' % (xml_escape(snapshot),)
		s = dom.snapshotCreateXML(xml, 0)

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error creating "%(domain)s" snapshot: %(error)s'), domain=domain, error=ex.get_error_message())

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
		if dom.hasManagedSaveImage(0):
			logger.warning('Domain "%(domain)s" saved state will be removed.' % {'domain':domain})
			dom.managedSaveRemove(0)
		old_state = dom_stat.key()
		snap = dom.snapshotLookupByName(snapshot, 0)
		try:
			# Try unforced revert for backward-compatibility with previous versions first
			res = dom.revertToSnapshot(snap, 0)
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_SNAPSHOT_REVERT_RISKY:
				raise
			res = dom.revertToSnapshot(snap, libvirt.VIR_DOMAIN_SNAPSHOT_REVERT_FORCE)
		if res != 0:
			raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=res)

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=ex.get_error_message())

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
		res = snap.delete(0)
		if res != 0:
			raise NodeError(_('Error deleting "%(domain)s" snapshot: %(error)s'), domain=domain, error=res)

		try:
			del node.domains[domain].pd.snapshots[snapshot]
		except KeyError:
			dom_stat.update(dom)
			node.wait_update(domain, old_state)
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise NodeError(_('Error deleting "%(domain)s" snapshot: %(error)s'), domain=domain, error=ex.get_error_message())

def domain_update(domain):
	"""Trigger update of domain.
	Unfound domains are ignored."""
	global nodes
	# 1st: find domain on the previous host using only (stale) internal data
	for node in nodes.itervalues():
		conn = node.conn
		try:
			dom_stat = node.domains[domain]
			dom = conn.lookupByUUIDString(domain)
			dom_stat.update(dom)
			dom_stat.update_ldap()
			return
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(ex)
				raise NodeError(_('Error updating domain "%(domain)s"'), domain=domain)
			# remove stale data
			del node.domains[domain]
		except KeyError:
			# domain not on this node
			pass
	# 2nd: failed to find existing data, search again all hosts
	for node in nodes.itervalues():
		conn = node.conn
		try:
			dom = conn.lookupByUUIDString(domain)
			dom_stat = Domain(dom, node=node)
			node.domains[domain] = dom_stat
			return
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(ex)
				raise NodeError(_('Error updating domain "%(domain)s"'), domain=domain)
			else:
				continue # skip this node
	else:
		logger.info('Domain %s not found for update' % domain)
		raise NodeError(_('Failto to update domain "%(domain)s"'), domain=domain)

def domain_clone(uri, domain, name, subst):
	"""Clone a domain."""
	warnings = []
	undo_vol = []
	try:
		try:
			node = node_query(uri)
			conn = node.conn
			try:
				dom = conn.lookupByName(name)
				uuid = dom.UUIDString()
				raise NodeError(_('Domain "%(domain)s" already exists: %(uuid)s'), domain=name, uuid=uuid)
			except libvirt.libvirtError, ex:
				if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
					raise

			dom = conn.lookupByUUIDString(domain)
			dom_stat = node.domains[domain]
			if dom_stat.pd.state != libvirt.VIR_DOMAIN_SHUTOFF:
				raise NodeError(_('Domain "%(domain)s" is not shut off: %(state)d'), domain=domain, state=dom_stat.pd.state)
			try:
				annotations = ldap_annotation(domain)
			except LdapConnectionError, ex:
				warning = 'Failed to get annotations from LDAP for "%(domain)s": %(error)s' % {'domain': domain, 'error': ex}
				logger.warning(warning)
				warnings.append(warning)
				annotations = {}

			xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
			# /domain
			domain = ET.fromstring(xml)
			# /domain/uuid
			domain_uuid = __update_xml(domain, 'uuid', None) # remove
			# /domain/name
			domain_name = __update_xml(domain, 'name', name) # replace
			# /domain/devices/*[]
			domain_devices = __update_xml(domain, 'devices', '')

			# /domain/devices/interface[]
			domain_devices_interfaces = domain_devices.findall('interface')
			default_mac = subst.get( 'mac', 'clone' ) # clone or auto
			for domain_devices_interface in domain_devices_interfaces:
				# /domain/devices/interface/mac @address
				domain_devices_interface_mac = domain_devices_interface.find('mac')
				mac_address = domain_devices_interface_mac.attrib['address']
				key = 'mac#%s' % (mac_address,)
				try:
					new_mac = subst[key]
				except KeyError:
					if default_mac == 'auto':
						logger.debug('Auto-generating MAC address for %s (default)' % (mac_address,))
						del domain_devices_interface_mac.attrib['address']
					else:
						logger.debug('Keeping MAC address %s (default)' % (mac_address,))
						# nothing to do for mode 'auto'
				else:
					if new_mac:
						logger.debug('Changing MAC from %s to %s' % (mac_address, new_mac))
						domain_devices_interface_mac.attrib['address'] = new_mac
					else:
						logger.debug('Auto-generating MAC for %s' % (mac_address,))
						del domain_devices_interface_mac.attrib['address']

			# /domain/devices/disk[]
			domain_devices_disks = domain_devices.findall('disk')
			for domain_devices_disk in domain_devices_disks:
				# /domain/devices/disk @type @device
				disk_type = domain_devices_disk.attrib['type']
				disk_device = domain_devices_disk.attrib['device']
				# /domain/devices/disk/driver @name @type @cache
				domain_devices_disk_driver = domain_devices_disk.find('driver')
				driver_type = domain_devices_disk_driver.attrib.get('type', 'raw')
				# /domain/devices/disk/readonly
				readonly = domain_devices_disk.find('readony') is not None
				# /domain/devices/disk/target @bus @dev
				domain_devices_disk_target = domain_devices_disk.find('target')
				target_bus = domain_devices_disk_target.attrib['bus']
				target_dev = domain_devices_disk_target.attrib['dev']

				key = 'copy#%s' % (target_dev,)
				try:
					method = subst[key]
				except KeyError:
					if disk_device in ('cdrom', 'floppy'):
						method = 'share'
					elif readonly:
						method = 'share'
					else:
						method = 'copy'
				if method == 'share':
					continue # nothing to clone for shared disks

				# /domain/devices/disk/source @file @dev
				domain_devices_disk_source = domain_devices_disk.find('source')
				if disk_type == 'file':
					source = domain_devices_disk_source.attrib['file']
					suffix = '.%s' % (driver_type,)
				elif disk_type == 'block':
					source = domain_devices_disk_source.attrib['dev']
					suffix = ''
				else:
					raise NodeError(_("Unknown disk/type='%(type)s'"), type=disk_type)

				# lookup old disk
				try:
					vol = conn.storageVolLookupByPath(source)
					pool = vol.storagePoolLookupByVolume()
				except libvirt.libvirtError, ex:
					if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
						raise
					raise NodeError(_('Volume "%(volume)s" not found: %(error)s'), volume=source, error=ex.get_error_message())

				# create new name
				old_name = vol.name()
				def new_names():
					key = 'name#%s' % (target_dev,)
					if key in subst:
						yield subst[key]
						return # Only try the explicit name
					if dom_stat.pd.name in old_name:
						yield old_name.replace(dom_stat.pd.name, name, 1)
					yield '%s_%s%s' % (name, target_dev, suffix)
					yield '%s_%d%s' % (name, domain_devices_disks.index(domain_devices_disk), suffix)
					for _ in range(10):
						yield '%s_%08x%s' % (name, random.getrandbits(32), suffix)
				volumes = pool.listVolumes()
				for new_name in new_names():
					if new_name not in volumes:
						break
				else:
					raise NodeError(_('Failed to generate new name for disk "%(disk)s"'), disk=old_name)

				xml = vol.XMLDesc(0)
				# /volume
				volume = ET.fromstring(xml)
				# /volume/name
				volume_name = __update_xml(volume, 'name', new_name) # replace
				# /volume/key
				volume_key = __update_xml(volume, 'key', None) # remove
				# /volume/source
				volume_source = __update_xml(volume, 'source', None) # remove
				# /volume/target
				volume_target = volume.find('target')
				if volume_target:
					# /volume/target/path
					volume_target_path = __update_xml(volume_target, 'path', None) # remove

				if method == 'cow':
					# /volume/backingStore
					volume_backingStore = __update_xml(volume, 'backingStore', '')
					# /volume/backingStore/path
					volume_backingStore_path = __update_xml(volume_backingStore, 'path', vol.path())
				xml = ET.tostring(volume)
				logger.debug('Cloning disk: %s' % (xml,))

				try:
					if method == 'copy':
						logger.info('Copying "%(old_volume)s" to "%(new_volume)s" begins' % {'old_volume': old_name, 'new_volume': new_name})
						new_vol = pool.createXMLFrom(xml, vol, 0)
						logger.info('Copying "%(old_volume)s" to "%(new_volume)s" done' % {'old_volume': old_name, 'new_volume': new_name})
					elif method == 'cow':
						logger.info('Backing "%(new_volume)s" by "%(old_volume)s"' % {'old_volume': old_name, 'new_volume': new_name})
						new_vol = pool.createXML(xml, 0)
					undo_vol.append(new_vol)
				except libvirt.libvirtError, ex:
					raise NodeError(_('Failed to clone volume "%(volume)s": %(error)s'), volume=source, error=ex.get_error_message())

				if disk_type == 'file':
					domain_devices_disk_source.attrib['file'] = new_vol.path()
				elif disk_type == 'block':
					domain_devices_disk_source.attrib['dev'] = new_vol.path()

			xml = ET.tostring(domain)
			logger.debug('Cloning domain: %s' % (xml,))
			dom2 = conn.defineXML(xml)
			uuid = dom2.UUIDString()
			logger.info('Clone domain "%s"(%s) defined.' % (name, uuid))
			del undo_vol[:]

			annotations['uuid'] = uuid
			try:
				record = ldap_modify(uuid)
				for key, value in annotations.items():
					record[key] = value
			except (LdapConnectionError, univention.admin.uexceptions.ldapError, univention.admin.uexceptions.objectExists), ex:
				warning = 'Failed to write annotations in LDAP for "%(domain)s": %(error)s' % {'domain': domain, 'error': ex}
				logger.warning(warning)
				warnings.append(warning)

			return (uuid, warnings)
		except libvirt.libvirtError, ex:
			logger.error(ex)
			raise NodeError(_('Error cloning "%(domain)s": %(error)s'), domain=domain, error=ex.get_error_message())
	finally:
		for vol in undo_vol:
			try:
				logger.info('Deleting "%(volume)s"' % {'volume': vol.name()})
				vol.delete(0)
			except Exception, ex:
				logger.warning('Failed undo: %(error)s' % {'error': ex})
