# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  node handler
#
# Copyright 2010-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
"""UVMM node handler.

This module implements functions to handle nodes and domains. This is independent from the on-wire-format.
"""

from __future__ import absolute_import
from __future__ import print_function

import libvirt
import time
import logging
import math
from .helpers import TranslatableException, ms, tuple2version, N_ as _, uri_encode, FQDN, prettyCapacity
from .uvmm_ldap import ldap_annotation, LdapError, LdapConnectionError, ldap_modify
import univention.admin.uexceptions
import threading
from .storage import create_storage_pool, create_storage_volume, destroy_storage_volumes, get_domain_storage_volumes, StorageError, assign_disks, calc_index
from .protocol import Data_Domain, Data_Node, Data_Snapshot, Disk, Interface, Graphic
from .network import network_start, network_find_by_bridge, NetworkError
from .xml import XMLNS, ET
import copy
import os
import stat
import errno
import fnmatch
import re
import random
from xml.sax.saxutils import escape as xml_escape
import tempfile
import pickle

import univention.config_registry as ucr
try:
	from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union  # noqa
	from types import TracebackType  # noqa
except ImportError:
	pass

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.node')

CACHE_STATE = '/var/run/uvmmd.cache'
STATES = ('NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED', 'PMSUSPENDED')
VIR_DOM = dict((v, k[9:]) for (k, v) in vars(libvirt).items() if k.startswith('VIR_FROM_'))
VIR_ERR = dict((v, k[8:]) for (k, v) in vars(libvirt).items() if k.startswith('VIR_ERR_') and k not in {'VIR_ERR_NONE', 'VIR_ERR_WARNING', 'VIR_ERR_ERROR'})
VIR_LVL = dict((v, k[8:]) for (k, v) in vars(libvirt).items() if k in {'VIR_ERR_NONE', 'VIR_ERR_WARNING', 'VIR_ERR_ERROR'})


def format_error(ex):
	# type: (libvirt.libvirtError) -> str
	lvl = ex.get_error_level()
	dom = ex.get_error_domain()
	err = ex.get_error_code()
	msg = ex.get_error_message()
	return '{:d}:{:s} {:d}:{:s} {:d}:{:s}: {:s}'.format(
		lvl, VIR_LVL.get(lvl, '?'),
		dom, VIR_DOM.get(dom, '?'),
		err, VIR_ERR.get(err, '?'),
		msg,
	)


class Description(object):
	__slots__ = ('desc', 'args')

	def __init__(self, *args, **kwargs):
		self.desc = kwargs.get('desc')
		self.args = args

	def __str__(self):  # type: () -> str
		return self.desc

	def __getitem__(self, item):  # type: (int) -> Union[str, Description]
		try:
			data = self.args[item]
		except IndexError:
			return self.__class__(desc=str(item))

		if isinstance(data, str):
			return self.__class__(desc=data)
		elif isinstance(data, (list, tuple)):
			desc, args = data
			return self.__class__(*args, desc=desc)

		raise TypeError(args)


DOM_EVENTS = Description(
	("Defined", ("Added", "Updated", "Renamed", "Snapshot")),
	("Undefined", ("Removed", "Renamed")),
	("Started", ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup")),
	("Suspended", ("Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error", "Postcopy", "Postcopy failed")),
	("Resumed", ("Unpaused", "Migrated", "Snapshot", "Postcopy")),
	("Stopped", ("Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot", "Daemon")),
	("Shutdown", ("Finished", "On guest request", "On host request")),
	("PMSuspended", ("Memory", "Disk")),
	("Crashed", ("Panicked",)),
)
ERROR_EVENTS = Description("None", "Pause", "Report")
CONNECTION_EVENTS = Description("Error", "End-of-file", "Keepalive", "Client")
RE_XML_NODE = re.compile(r'^(?:.*/)?(?:(\w+):)?(\w+)(?:\[.*\])?$')


class NodeError(TranslatableException):
	"""Error while handling node."""


class StoragePool(object):

	"""Container for storage pool statistics."""

	def __init__(self, pool):
		# type: (libvirt.virStoragePool) -> None
		self.uuid = pool.UUIDString()
		self.name = pool.name()
		self.capacity = 0
		self.available = 0
		self.update(pool)

	def __eq__(self, other):
		# type: (Any) -> bool
		return self.uuid == other.uuid

	def update(self, pool):
		# type: (libvirt.virStoragePool) -> None
		"""Update statistics."""
		_state, self.capacity, _allocation, self.available = pool.info()


class DomainTemplate(object):

	"""Container for node capability."""

	@staticmethod
	def list_from_xml(xml):
		# type: (str) -> List[DomainTemplate]
		"""Convert XML to list."""
		capabilities_tree = ET.fromstring(xml)
		result = []  # type: List[DomainTemplate]
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
		# type: (ET._Element) -> List[str]
		"""Return list of features."""
		f_names = []  # type: List[str]
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
		# type: (ET._Element, ET._Element, str, List[str]) -> None
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
			logger.error('No emulator specified in %s/%s', self.arch, self.domain_type)

		for node in [domain_type, arch]:
			self.machines = [m.text for m in node.findall('machine')]
			if self.machines:
				break
		else:
			logger.error('No machines specified in %s/%s', self.arch, self.domain_type)

		self.loader = arch.findtext('loader')

	def __str__(self):
		# type: () -> str
		return 'DomainTemplate(arch=%s dom_type=%s os_type=%s): %s, %s, %s, %s' % (self.arch, self.domain_type, self.os_type, self.emulator, self.loader, self.machines, self.features)

	def matches(self, domain):
		# type: (Data_Domain) -> bool
		"""Return True if domain matches os_type, arch and domain_type."""
		return self.arch == domain.arch and self.domain_type == domain.domain_type and self.os_type == domain.os_type


class PersistentCached(object):

	"""Abstract class to implement caching."""

	def cache_file_name(self, suffix='.pic'):
		# type: (str) -> str
		raise NotImplementedError()

	def cache_save(self, data):
		# type: (Any) -> None
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
		# type: () -> None
		"""Purge public data from cache."""
		old_name = self.cache_file_name()
		new_name = self.cache_file_name(suffix='.old')
		os.rename(old_name, new_name)


class _Domain(object):
	__slots__ = ('log', 'domain', '_inactive_xml', '_inactive_tree', '_active_xml', '_active_tree')

	def __init__(self, domain):
		# type: (libvirt.virDomain) -> None
		self.log = logger.getChild('xml')
		self.domain = domain  # type: libvirt.virDomain
		self._inactive_xml = None  # type: Optional[str]
		self._inactive_tree = None  # type: ET._Element
		self._active_xml = None  # type: Optional[str]
		self._active_tree = None  # type: ET._Element

	@property
	def inactive_xml(self):
		# type () -> str
		if not self._inactive_xml:
			self.log.debug('Fetching inactive XML for %s', self.domain.name())
			self._inactive_xml = self.domain.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE | libvirt.VIR_DOMAIN_XML_INACTIVE)
		return self._inactive_xml

	@property
	def inactive_tree(self):
		# type: () -> ET._Element
		if self._inactive_tree is None:
			self.log.debug('Parsing inactive XML for %s', self.domain.name())
			self._inactive_tree = ET.fromstring(self.inactive_xml)
		return self._inactive_tree

	@property
	def active_xml(self):
		# type () -> str
		if not self._active_xml:
			self.log.debug('Fetching active XML for %s', self.domain.name())
			self._active_xml = self.domain.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
		return self._active_xml

	@property
	def active_tree(self):
		# type: () -> ET._Element
		if self._active_tree is None:
			self.log.debug('Parsing active XML for %s', self.domain.name())
			self._active_tree = ET.fromstring(self.active_xml)
		return self._active_tree

	def __enter__(self):
		# type: () -> _Domain
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		self._inactive_xml = None
		self._inactive_tree = None
		self._active_xml = None
		self._active_tree = None


class Domain(PersistentCached):

	"""Container for domain statistics."""
	CPUTIMES = (10, 60, 5 * 60)  # 10s 60s 5m

	def __init__(self, domain, node):
		# type: (Union[libvirt.virDomain, str], Node) -> None
		self.node = node  # type: Node
		self._time_stamp = 0.0
		self._time_used = long(0)
		self._cpu_usage = 0.0
		self._cache_id = None  # type: Optional[int]
		self._restart = 0
		self._redefined = True  # check for <cpu> only once per process as this is quiet expensive
		self.pd = Data_Domain()
		if isinstance(domain, libvirt.virDomain):
			self.pd.uuid = domain.UUIDString()
			self.pd.os_type = domain.OSType()
			self.update(domain)
		elif isinstance(domain, basestring):  # XML
			self.xml2obj(domain)
		self.update_ldap()

	def __eq__(self, other):
		# type: (Any) -> bool
		return self.pd.uuid == other.pd.uuid

	def update(self, domain, redefined=False):
		# type: (libvirt.virDomain, bool) -> None
		"""
		Update statistics which may change often.

		:param libvirt.virDomain domain: libvirt domain instance.
		:param bool defined: True if the domain was (re-)defined.
		"""
		self._redefined |= redefined
		if self.pd.name is None:
			self.pd.name = domain.name()

		self.pd.autostart = bool(domain.autostart())

		info = domain.info()
		self.pd.state, maxMem, curMem, self.pd.vcpus, runtime = info
		self.pd.maxMem = long(maxMem) << 10  # KiB

		self.pd.state, self.pd.reason = domain.state()

		if self.pd.state in (libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			self.pd.curMem = long(0)
			delta_used = long(0)
			self._time_used = long(0)
		else:
			self.pd.curMem = long(curMem) << 10  # KiB
			delta_used = runtime - self._time_used  # running [ns]
			self._time_used = runtime
			try:
				stats = domain.jobStats()
			except libvirt.libvirtError as ex:
				if ex.get_error_code() != libvirt.VIR_ERR_OPERATION_UNSUPPORTED:
					logger.warning('Failed to query job status %s: %s', self.pd.uuid, format_error(ex))
			else:
				self.migration_status(stats)

		# Calculate historical CPU usage
		# http://www.teamquest.com/resources/gunther/display/5/
		now = time.time()
		delta_t = now - self._time_stamp  # wall clock [s]
		if delta_t > 0.0 and delta_used >= long(0):
			try:
				self._cpu_usage = delta_used / delta_t / self.pd.vcpus / 1e9  # scale [ns] to percentage
			except ZeroDivisionError:
				self._cpu_usage = 0
			for i, span in enumerate(Domain.CPUTIMES):
				if delta_t < span:
					exp = math.exp(-delta_t / span)
					self.pd.cputime[i] *= exp
					self.pd.cputime[i] += (1.0 - exp) * self._cpu_usage
				else:
					self.pd.cputime[i] = self._cpu_usage
		self._time_stamp = now
		self.update_expensive(domain)

	def update_expensive(self, domain):
		# type: (libvirt.virDomain) -> None
		"""Update statistics."""
		with _Domain(domain) as dom:
			cache_id = hash(dom.inactive_xml)
			if self._cache_id != cache_id:
				if self.update_cpu(dom):
					return
				try:
					self.cache_save(dom.inactive_xml)
					self._cache_id = cache_id
				except EnvironmentError as ex:
					logger.warning("Failed to cache domain %s: %s", self.pd.name, ex)

			if domain.isActive():
				xml = dom.active_xml
				self.pd.suspended = False
			else:
				xml = dom.inactive_xml
				self.pd.suspended = domain.hasManagedSaveImage(0)

			self.xml2obj(xml)
			self.update_volumes(domain)
			self.update_snapshots(domain)

	def update_cpu(self, dom):
		# type: (_Domain) -> bool
		"""
		Update '/domain/cpu' as set by UCRV 'uvmm/vm/cpu/host-model'.

		:param _Domain domain: domain XML data.
		:returns: True if the node was updated, False otherwise.
		:rtype: bool
		"""
		if not self._redefined:
			return False

		self._redefined = False

		try:
			model = configRegistry['uvmm/vm/cpu/host-model']
		except LookupError:
			return False

		old_cpu = _update_xml(dom.inactive_tree, 'cpu', None)
		if model == 'remove':
			inactive_changed = bool(old_cpu)
		elif model == 'missing' and old_cpu is not None:
			dom.inactive_tree.append(old_cpu)
			inactive_changed = False
		elif model in ('missing', 'always'):
			new_cpu = _update_xml(dom.inactive_tree, 'cpu', None, mode='host-model')
			_update_xml(new_cpu, 'model', None, fallback='allow')
			inactive_changed = old_cpu is None or old_cpu.attrib.get('mode') != 'host-model'
		else:
			return False

		if dom.domain.isActive() and (inactive_changed or (dom.inactive_tree.find('cpu') is None) != (dom.active_tree.find('cpu') is None)):
			logger.info("Pending domain restart: %s", self.pd.name)
			self._restart = dom.domain.ID()

		if not inactive_changed:
			return False

		logger.info("Updating inactive domain %s", self.pd.name)
		new_xml = ET.tostring(dom.inactive_tree)
		conn = dom.domain.connect()
		try:
			conn.defineXML(new_xml)
		except libvirt.libvirtError as ex:
			logger.error("Failed to update domain %s: %s (%s)", self.pd.name, format_error(ex), new_xml)

		return True

	def update_volumes(self, domain):
		# type: (libvirt.virDomain) -> None
		"""Determine size and pool."""
		for dev in self.pd.disks:
			if not dev.source:
				continue
			try:
				conn = domain.connect()
				vol = conn.storageVolLookupByPath(dev.source)
				dev.size = vol.info()[1]  # (type, capacity, allocation)
				pool = vol.storagePoolLookupByVolume()
				dev.pool = pool.name()
			except libvirt.libvirtError as ex:
				if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
					logger.warning('Failed to query disk %s#%s: %s', self.pd.uuid, dev.source, format_error(ex))

	def update_snapshots(self, domain):
		# type: (libvirt.virDomain) -> None
		"""List of snapshots."""
		snapshots = {}
		for name in domain.snapshotListNames(0):
			snap = domain.snapshotLookupByName(name, 0)
			xml = snap.getXMLDesc(0)
			try:
				domainsnap_tree = ET.fromstring(xml)
			except ET.XMLSyntaxError:
				continue
			ctime = domainsnap_tree.findtext('creationTime', namespaces=XMLNS)
			snap_stat = Data_Snapshot()
			snap_stat.name = name
			snap_stat.ctime = int(ctime)
			snapshots[name] = snap_stat
		self.pd.snapshots = snapshots

	def update_ldap(self):
		# type: () -> None
		"""Update annotations from LDAP."""
		try:
			self.pd.annotations = ldap_annotation(self.pd.uuid)
		except LdapError:
			self.pd.annotations = {}

	def migration_status(self, stats):
		# type: (Dict[str, Any]) -> Tuple[str, Dict[str, Any]]
		"""
		Convert libvirt job stats to string and dictionary for string formatting.
		"""
		# final_stats = {
		#  'data_processed': long(1), 'data_remaining': long(0), 'data_total': long(1),
		#  'disk_processed': long(0), 'disk_remaining': long(0), 'disk_total': long(0),
		#  'downtime': long(1), 'downtime_net': long(1),
		#  'memory_constant': long(1), 'memory_dirty_rate': long(0), 'memory_iteration': long(3), 'memory_normal': long(1), 'memory_normal_bytes': long(1), 'memory_processed': long(1), 'memory_remaining': long(0), 'memory_total': long(1),
		#  'setup_time': long(1),
		#  'time_elapsed': long(1), 'time_elapsed_net': long(1),
		# }
		# process_stats = {
		#  'data_processed': long(1), 'data_remaining': long(1), 'data_total': long(1),
		#  'disk_processed': long(0), 'disk_remaining': long(0), 'disk_total': long(0),
		#  'downtime': long(1),
		#  'memory_constant': long(1), 'memory_dirty_rate': long(1), 'memory_iteration': long(1), 'memory_normal': long(1), 'memory_normal_bytes': long(1), 'memory_processed': long(1), 'memory_remaining': long(1), 'memory_total': long(1),
		#  'setup_time': long(1),
		#  'time_elapsed': long(1),
		#  'type': 2,
		# }
		self.pd.migration = stats
		typ = stats.get('type', None)
		if typ == 0:
			self.pd.migration['msg'] = ''
			return ('', {})
		elif typ is None:
			fmt = _('Migration completed after %(time)s in %(iteration)d iterations')
		else:
			fmt = _('Migration in progress since %(time)s, iteration %(iteration)d')
		vals = dict(
			time=ms(stats.get('time_elapsed', 0)),
			iteration=stats.get('memory_iteration', 1),
		)
		self.pd.migration['msg'] = fmt % vals
		return (fmt, vals)

	def xml2obj(self, xml):
		# type: (str) -> None
		"""Parse XML into python object."""
		try:
			domain_tree = ET.fromstring(xml)
		except ET.XMLSyntaxError:
			return

		self.pd.domain_type = domain_tree.attrib['type']
		if not self.pd.domain_type:
			logger.error("Failed /domain/@type from %s" % xml)
		self.pd.uuid = domain_tree.findtext('uuid', namespaces=XMLNS)
		self.pd.name = domain_tree.findtext('name', namespaces=XMLNS)
		self.pd.hyperv = domain_tree.find('features/hyperv/relaxed') is not None
		self.xml2obj_boot(domain_tree)
		self.xml2obj_clock(domain_tree)
		self.pd.cpu_model = domain_tree.findtext('cpu/model', namespaces=XMLNS)

		devices = domain_tree.find('devices', namespaces=XMLNS)
		self.xml2obj_disks(devices)
		self.xml2obj_interfaces(devices)
		self.xml2obj_graphics(devices)

		self.pd.targethosts = [host.text for host in domain_tree.findall('metadata/uvmm:migrationtargethosts/uvmm:hostname', namespaces=XMLNS)]

	def xml2obj_boot(self, domain_tree):
		# type: (ET._Element) -> None
		"""Parse boot information from XML."""
		os_ = domain_tree.find('os', namespaces=XMLNS)
		if os_ is not None:
			typ = os_.find('type', namespaces=XMLNS)
			if typ is not None:
				self.pd.os_type = typ.text
				if 'arch' in typ.attrib:
					self.pd.arch = typ.attrib['arch']
			self.pd.kernel = os_.findtext('kernel', namespaces=XMLNS)
			self.pd.cmdline = os_.findtext('cmdline', namespaces=XMLNS)
			self.pd.initrd = os_.findtext('initrd', namespaces=XMLNS)
			self.pd.boot = [boot.attrib['dev'] for boot in os_.findall('boot', namespaces=XMLNS)]
		bootloader = domain_tree.find('bootloader', namespaces=XMLNS)
		if bootloader is not None:
			self.pd.bootloader = bootloader.text
			self.pd.bootloader_args = domain_tree.findtext('bootloader_args', namespaces=XMLNS)

	def xml2obj_clock(self, domain_tree):
		# type: (ET._Element) -> None
		"""Parse clock information from XML."""
		clock = domain_tree.find('clock', namespaces=XMLNS)
		if clock is not None:
			self.pd.rtc_offset = clock.attrib.get('offset')

	def xml2obj_disks(self, devices):
		# type: (ET._Element) -> None
		"""Parse disks from XML."""
		self.pd.disks = []
		for disk in devices.findall('disk', namespaces=XMLNS):
			dev = Disk()
			dev.type = disk.attrib['type']
			dev.device = disk.attrib['device']
			driver = disk.find('driver', namespaces=XMLNS)
			if driver is not None:
				dev.driver = driver.attrib.get('name')  # optional
				dev.driver_type = driver.attrib.get('type')  # optional
				dev.driver_cache = driver.attrib.get('cache', '')  # optional
			source = disk.find('source', namespaces=XMLNS)
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
			target = disk.find('target', namespaces=XMLNS)
			if target is not None:
				dev.target_dev = target.attrib['dev']
				dev.target_bus = target.attrib.get('bus')  # optional
			if disk.find('readonly', namespaces=XMLNS) is not None:
				dev.readonly = True

			self.pd.disks.append(dev)

	def xml2obj_interfaces(self, devices):
		# type: (ET._Element) -> None
		"""Parse interfaces from XML."""
		self.pd.interfaces = []
		for iface in devices.findall('interface', namespaces=XMLNS):
			dev = Interface()
			dev.type = iface.attrib['type']
			mac = iface.find('mac', namespaces=XMLNS)
			if mac is not None:
				dev.mac_address = mac.attrib['address']
			source = iface.find('source', namespaces=XMLNS)
			if source is not None:
				if dev.type == Interface.TYPE_BRIDGE:
					dev.source = source.attrib['bridge']
				elif dev.type == Interface.TYPE_NETWORK:
					dev.source = source.attrib['network']
				elif dev.type == Interface.TYPE_DIRECT:
					dev.source = source.attrib['dev']
			script = iface.find('script', namespaces=XMLNS)
			if script is not None:
				dev.script = script.attrib['path']
			target = iface.find('target', namespaces=XMLNS)
			if target is not None:
				dev.target = target.attrib['dev']
			model = iface.find('model', namespaces=XMLNS)
			if model is not None:
				dev.model = model.attrib['type']

			self.pd.interfaces.append(dev)

	def xml2obj_graphics(self, devices):
		# type: (ET._Element) -> None
		"""Parse graphics from XML."""
		self.pd.graphics = []
		for graphic in devices.findall('graphics', namespaces=XMLNS):
			dev = Graphic()
			type = graphic.attrib['type']
			dev.type = type
			if dev.type == Graphic.TYPE_VNC:
				dev.port = int(graphic.attrib['port'])  # FIXME
				dev.autoport = graphic.attrib['autoport'].lower() == 'yes'
				try:
					dev.listen = graphic.attrib['listen']  # FIXME
				except LookupError:
					pass
				try:
					dev.passwd = graphic.attrib['passwd']
				except LookupError:
					pass
				try:
					dev.keymap = graphic.attrib['keymap']
				except LookupError:
					pass
			elif dev.type == Graphic.TYPE_SDL:
				pass
			else:
				logger.error('Unsupported graphics type: %s' % type)
			self.pd.graphics.append(dev)

	def key(self):
		# type: () -> int
		"""Return a unique key for this domain and generation."""
		return hash((self.pd.uuid, self._time_stamp))

	def cache_file_name(self, uuid=None, suffix='.xml'):
		# type: (str, str) -> str
		"""Return the path of the domain cache file."""
		if uuid is None:
			uuid = self.pd.uuid
		return os.path.join(self.node.cache_dom_dir(), uuid + suffix)

	def calc_cache_id(self):
		# type: () -> int
		key = hash((self.pd.uuid, self.pd.name, self.pd.maxMem))
		for disk in self.pd.disks:
			key ^= hash((disk.target_dev, disk.source))
		for iface in self.pd.interfaces:
			key ^= hash((iface.mac_address, iface.source, iface.model))
		for gfx in self.pd.graphics:
			key ^= hash(gfx.port)
		return key

	def _vnc(self):
		# type: () -> Optional[Tuple[str, int]]
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
		# type: (str) -> None
		"""x.__delitem__(i) <==> del x[i]"""
		domStat = super(_DomainDict, self).pop(uuid)
		try:
			domStat.cache_purge()
		except EnvironmentError as ex:
			if ex.errno != errno.ENOENT:
				logger.warning("Failed to remove cached domain '%s#%s': %s", domStat.node.pd.uri, uuid, ex)


class Node(PersistentCached):
	"""
	Container for node statistics.
	"""

	try:
		reservedMem = max(0, int(configRegistry['uvmm/overcommit/reserved']))
	except (LookupError, TypeError, ValueError):
		reservedMem = 0

	def __init__(self, uri, cache_dir):
		# type: (str, str) -> None
		self.cache_dir = cache_dir
		self.domains = _DomainDict()
		self.conn = None  # type: Optional[libvirt.virConnect]
		self.libvirt_version = tuple2version((0, 8, 7))
		self.config_frequency = Nodes.IDLE_FREQUENCY
		self.current_frequency = Nodes.IDLE_FREQUENCY
		self.domainCB = []  # type: List[int]
		self.timerEvent = threading.Event()
		try:
			# Calculate base cache dir for node
			cache_dom_dir = self.cache_dom_dir(uri)
			try:
				os.mkdir(cache_dom_dir, 0o700)  # contains VNC password
			except EnvironmentError as ex:
				if ex.errno != errno.EEXIST:
					raise

			# Load cached node info
			cache_file_name = self.cache_file_name(uri)
			logger.debug("Loading cache '%s'", cache_file_name)
			with open(CACHE_STATE, 'w') as cache:
				cache.write(cache_file_name)
			with open(cache_file_name, 'r') as cache_file:
				try:
					data = pickle.Unpickler(cache_file)
					assert data is not None
					self.pd = data.load()  # type: Data_Node
				except:
					os.unlink(cache_file_name)
					raise

			os.unlink(CACHE_STATE)
			assert self.pd.uri == uri
			logger.debug("Loaded from cache '%s'", self.pd.uri)

			# Load cached domains info
			for root, dirs, files in os.walk(cache_dom_dir):
				for fname in files:
					if not fname.endswith('.xml'):
						continue
					cache_file_name = os.path.join(root, fname)
					try:
						with open(cache_file_name, 'r') as cache_file:
							xml = cache_file.read()
						assert xml
						assert isinstance(xml, basestring)
						domStat = Domain(xml, self)
						assert domStat.cache_file_name() == cache_file_name
						self.domains[domStat.pd.uuid] = domStat
						logger.debug("Loaded from cache '%s#%s'", self.pd.uri, domStat.pd.uuid)
					except (EOFError, EnvironmentError, AssertionError, ET.XMLSyntaxError, TypeError) as ex:
						logger.warning("Failed to load cached domain %s: %s", cache_file_name, ex)
				del dirs[:]  # just that directory; no recursion
		except (EOFError, EnvironmentError, AssertionError, pickle.PickleError) as ex:
			logger.warning("Failed to load cached state of %s: %s", uri, ex)
			self.pd = Data_Node()  # public data
			self.pd.uri = uri
			self.pd.name = re.sub('^[^:]+://(?:[^/@]+@)?([^/]+).*', lambda m: m.group(1), uri)
		self._cache_id = self.calc_cache_id()

		# schedule periodic update
		self.timer = threading.Thread(group=None, target=self.run, name=self.pd.uri, args=(), kwargs={})  # type: Optional[threading.Thread]
		self.timer.start()

	def run(self):
		# type: () -> None
		"""Handle regular poll. Also checks connection liveness."""
		logger.info("timer_callback(%s) start", self.pd.uri)
		try:
			while self.timer is not None:
				try:
					logger.debug("timer_callback: %s", self.pd.uri)
					self.update_autoreconnect()
				except Exception:
					logger.error("%s: Exception in timer_callback", self.pd.uri, exc_info=True)
					# don't crash the event handler
				self.timerEvent.clear()
				self.timerEvent.wait(self.current_frequency / 1000.0)
		finally:
			logger.debug("timer_callback(%s) terminated", self.pd.uri)

	def update_autoreconnect(self):
		# type: () -> None
		"""(Re-)connect after connection broke."""
		try:
			if self.conn is None:
				self.conn = libvirt.open(self.pd.uri)
				logger.info("Connected to '%s'", self.pd.uri)
				self.conn.registerCloseCallback(self.close_event, None)

				self.update_once()
				self._register_default_pool()
				# reset timer after successful re-connect
				self.current_frequency = self.config_frequency

			self.update()
			self.pd.last_try = self.pd.last_update = time.time()
		except libvirt.libvirtError as ex:
			self.pd.last_try = time.time()
			# double timer interval until maximum
			hz = min(self.current_frequency * 2, Nodes.BEBO_FREQUENCY)
			logger.warning("'%s' broken? next check in %s. %s", self.pd.uri, ms(hz), format_error(ex), exc_info=self.current_frequency == self.config_frequency)
			if hz > self.current_frequency:
				self.current_frequency = hz

				if ex.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
					return
				elif ex.get_error_domain() != libvirt.VIR_FROM_RPC:
					return

			self._unregister()

	def __eq__(self, other):
		# type: (Any) -> bool
		return (self.pd.uri, self.pd.name) == (other.pd.uri, other.pd.name)

	def __del__(self):
		# type: () -> None
		"""Free Node and deregister callbacks."""
		self.unregister()
		del self.pd
		del self.domains

	def _register_default_pool(self):
		# type: () -> None
		"""Create a default storage pool if not available"""
		try:
			assert self.conn is not None
			self.conn.storagePoolLookupByName('default')
			logger.debug("default pool already registered on %s" % self.pd.name)
		except libvirt.libvirtError:
			logger.info("creating default pool on %s" % self.pd.name)
			create_storage_pool(
				self.conn,
				configRegistry.get('uvmm/pool/default/path', '/var/lib/libvirt/images')
			)

	def update_once(self):
		# type: () -> None
		"""Update once on (re-)connect."""
		assert self.conn is not None
		self.pd.name = self.conn.getHostname()
		info = self.conn.getInfo()
		self.pd.phyMem = (long(info[1]) << 20) - self.reservedMem  # MiB
		self.pd.cpus = info[2]
		self.pd.cores = tuple(info[4:8])
		xml = self.conn.getCapabilities()
		self.pd.capabilities = DomainTemplate.list_from_xml(xml)
		self.libvirt_version = self.conn.getLibVersion()

		self.domainCB = [
			self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, self.livecycle_event, None),
			self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_REBOOT, self.reboot_event, None),
			self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON, self.error_event, None),
			self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_MIGRATION_ITERATION, self.migration_event, None),
			self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_JOB_COMPLETED, self.job_event, None),
		]

	def livecycle_event(self, conn, dom, event, detail, opaque):
		# type: (libvirt.virConnect, libvirt.virDomain, int, int, Any) -> None
		"""Handle domain addition, update and removal."""
		log = logger.getChild('livecycle')
		try:
			log.debug(
				"Node %s Domain %s(%s) Event %s Details %s",
				self.pd.name,
				dom.name(),
				dom.ID(),
				DOM_EVENTS[event],
				DOM_EVENTS[event][detail],
			)
			uuid = dom.UUIDString()
			if event == libvirt.VIR_DOMAIN_EVENT_UNDEFINED:
				if detail == libvirt.VIR_DOMAIN_EVENT_UNDEFINED_REMOVED:
					del self.domains[uuid]
			elif event == libvirt.VIR_DOMAIN_EVENT_STOPPED and detail in (
				libvirt.VIR_DOMAIN_EVENT_STOPPED_MIGRATED,
				libvirt.VIR_DOMAIN_EVENT_STOPPED_FAILED,
			):
				pass
			else:
				try:
					domStat = self.domains[uuid]
				except LookupError:
					domStat = Domain(dom, node=self)
					self.domains[uuid] = domStat

				domStat.update(dom, redefined=event == libvirt.VIR_DOMAIN_EVENT_DEFINED)
				if event != libvirt.VIR_DOMAIN_EVENT_SUSPENDED and detail != libvirt.VIR_DOMAIN_EVENT_SUSPENDED_IOERROR:
					domStat.pd.error = {}
			if event in (libvirt.VIR_DOMAIN_EVENT_STARTED, libvirt.VIR_DOMAIN_EVENT_RESUMED):
				self.write_novnc_tokens()
		except KeyError:
			# during migration events are not ordered causal
			pass
		except Exception:
			log.error('%s: Exception handling callback', self.pd.uri, exc_info=True)
			# don't crash the event handler

	def reboot_event(self, conn, dom, opaque):
		# type: (libvirt.virConnect, libvirt.virDomain, Any) -> None
		"""Handle domain reboot."""
		log = logger.getChild('reboot')
		try:
			log.debug(
				"Node %s Domain %s(%s)",
				self.pd.name,
				dom.name(),
				dom.ID(),
			)
			uuid = dom.UUIDString()
			try:
				domStat = self.domains[uuid]
			except LookupError:
				return
			try:
				if domStat._restart == dom.ID():
					# Race condition: the slower UVMMd will just ignore errors
					try:
						dom.destroy()
						dom.create()
					except libvirt.libvirtError as ex:
						if ex.get_error_code() != libvirt.VIR_ERR_OPERATION_INVALID:
							raise
			finally:
				domStat._restart = 0
		except Exception:
			log.error('%s: Exception handling callback', self.pd.uri, exc_info=True)
			# don't crash the event handler

	def error_event(self, conn, dom, srcpath, devalias, action, reason, opaque):
		# type: (libvirt.virConnect, libvirt.virDomain, str, str, int, str, Any) -> None
		"""
		Handle IO errors.
		"""
		log = logger.getChild('io')
		try:
			log.debug(
				"Node %s Domain %s(%s) dev=%s[%s] action=%s reason=%s",
				self.pd.name,
				dom.name(),
				dom.ID(),
				devalias,
				srcpath,
				ERROR_EVENTS[action],
				reason,
			)
			uuid = dom.UUIDString()
			try:
				domStat = self.domains[uuid]
			except LookupError:
				return
			error = {
				'reason': reason,
				'device': devalias,
				'srcpath': srcpath,
			}
			error['msg'] = _('IO error "%(reason)s" on device "%(device)s[%(srcpath)s]"') % error
			domStat.pd.error = error
		except Exception:
			log.error('%s: Exception handling callback', self.pd.uri, exc_info=True)
			# don't crash the event handler

	def migration_event(self, conn, dom, iteration, opaque):
		# type: (libvirt.virConnect, libvirt.virDomain, int, Any) -> None
		"""
		Handle domain migration events.
		"""
		log = logger.getChild('migration')
		try:
			domain = dom.name()
			log.debug(
				"Node %s Domain %s(%s) iter=%d",
				self.pd.name,
				domain,
				dom.ID(),
				iteration,
			)
			uuid = dom.UUIDString()
			try:
				domStat = self.domains[uuid]
			except LookupError:
				return
			stats = dom.jobStats()
			domStat.migration_status(stats)
			try:
				switch = int(configRegistry['uvmm/migrate/postcopy'])
			except (LookupError, TypeError, ValueError):
				return
			if iteration == switch:
				log.info('Domain "%(domain)s" switching to post-copy: %(stats)r', dict(domain=domain, stats=stats))
				dom.migrateStartPostCopy()
		except Exception:
			log.error('%s: Exception handling callback', self.pd.uri, exc_info=True)
			# don't crash the event handler

	def job_event(self, conn, dom, stats, opaque):
		# type: (libvirt.virConnect, libvirt.virDomain, Dict[str, Any], Any) -> None
		"""
		Handle domain job completed events.
		"""
		log = logger.getChild('job')
		try:
			log.debug(
				"Node %s Domain %s(%s) stats=%r",
				self.pd.name,
				dom.name(),
				dom.ID(),
				stats,
			)
			uuid = dom.UUIDString()
			try:
				domStat = self.domains[uuid]
			except LookupError:
				return
			domStat.migration_status(stats)
		except Exception:
			log.error('%s: Exception handling callback', self.pd.uri, exc_info=True)
			# don't crash the event handler

	def close_event(self, conn, reason, opaque):
		# type: (libvirt.virConnect, int, Any) -> None
		"""
		Handle connection close event.

		:param libvirt.virConnect conn: The (now closed) connection.
		:param int reason: Event details.
		:param opaque: Opaque data.
		"""
		log = logger.getChild('connection')
		log.info(
			"Connection %s closed: %s",
			conn.getURI(),
			CONNECTION_EVENTS[reason],
		)
		self.conn = None

	def unregister(self, wait=False):
		# type: (bool) -> None
		"""Unregister callbacks doing updates."""
		if self.timer is not None:
			timer, self.timer = self.timer, None
			self.timerEvent.set()
			while wait:
				timer.join(1.0)  # wait for up to 1 second until Thread terminates
				if timer.isAlive():
					logger.debug("timer still alive: %s", self.pd.uri)
				else:
					wait = False

		self._unregister()

	def _unregister(self):
		# type: () -> None
		"""Unregister callback and close connection."""
		conn, self.conn = self.conn, None
		if conn is not None:
			while self.domainCB:
				try:
					conn.domainEventDeregisterAny(self.domainCB.pop())
				except Exception as ex:
					logger.warning("%s: Exception in domainEventDeregisterAny: %s", self.pd.uri, ex)

			try:
				conn.close()
			except Exception as ex:
				logger.warning('%s: Exception in conn.close: %s', self.pd.uri, ex)

	def set_frequency(self, hz):
		# type: (int) -> None
		"""Set polling frequency for update."""
		self.config_frequency = hz
		self.current_frequency = hz
		self.timerEvent.set()

	def update(self):
		# type: () -> None
		"""Update node statistics."""
		curMem = 0
		maxMem = 0
		cpu_usage = 0.0
		cached_domains = self.domains.keys()

		assert self.conn is not None
		for dom in self.conn.listAllDomains():
			try:
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
			except libvirt.libvirtError as ex:
				if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
					raise

			curMem += domStat.pd.curMem
			maxMem += domStat.pd.maxMem
			cpu_usage += domStat._cpu_usage * domStat.pd.vcpus

		for uuid in cached_domains:
			# Remove obsolete domains
			try:
				del self.domains[uuid]
			except KeyError:
				continue

		self.pd.curMem = curMem
		self.pd.maxMem = maxMem
		self.pd.cpu_usage = cpu_usage / self.pd.cpus

		cache_id = self.calc_cache_id()
		if self._cache_id != cache_id:
			try:
				data = pickle.dumps(self.pd)
				self.cache_save(data)
				self._cache_id = cache_id
			except EnvironmentError as ex:
				logger.exception("Failed to write cached node %s: %s" % (self.pd.uri, ex))
			self.write_novnc_tokens()

	def write_novnc_tokens(self):
		# type: () -> None
		token_dir = os.path.join(self.cache_dir, 'novnc.tokens')
		path = os.path.join(token_dir, uri_encode(self.pd.uri))
		logger.debug("Writing noVNC tokens to '%s'", path)
		with tempfile.NamedTemporaryFile(delete=False, dir=token_dir) as tmp_file:
			for uuid, domStat in self.domains.items():
				try:
					host, port = domStat._vnc()
					print('%s: %s:%d' % (uuid, host, port), file=tmp_file)
				except TypeError:
					continue
		os.rename(tmp_file.name, path)

	def wait_update(self, domain, state_key, timeout=10):
		# type: (str, int, int) -> None
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
		# type: () -> int
		"""Calculate key for disk cache."""
		key = hash((
			self.pd.phyMem,
			self.pd.cores,
		))
		for dom in self.domains.values():
			key ^= dom.calc_cache_id()
		return key

	def cache_file_name(self, uri=None, suffix='.pic'):
		# type: (str, str) -> str
		"""Return the path of the node cache file."""
		if uri is None:
			uri = self.pd.uri
		return os.path.join(self.cache_dir, uri_encode(uri) + suffix)

	def domain_list(self, pattern='*'):
		# type: (str) -> List[Dict[str, Any]]
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		domains = []
		for dom in self.domains:
			pd = self.domains[dom].pd
			contact = pd.annotations.get('contact', '')
			name = pd.name
			descr = pd.annotations.get('description', '')
			if regex.match(name) or regex.match(contact) or regex.match(descr):
				vnc = self.domains[dom]._vnc()
				domains.append({
					'uuid': pd.uuid,
					'name': pd.name,
					'state': STATES[pd.state],
					'reason': pd.reason,
					'mem': pd.maxMem,
					'cpu_usage': pd.cputime[0],
					'vnc': bool(vnc),
					'vnc_port': vnc[1] if vnc else -1,
					'suspended': pd.suspended,
					'description': descr,
					'node_available': self.pd.last_try == self.pd.last_update,
					'error': pd.error,
					'migration': pd.migration,
				})

		return domains

	def cache_dom_dir(self, uri=None):
		# type: (str) -> str
		"""Return the path of the domain cache directory of the node."""
		return self.cache_file_name(uri, suffix='.d')

	def _check_ram_overcommit(self, domain):
		# type: (Domain) -> None
		"""
		Check if starting/migrating the VM is withing the RAM limit of the node.

		:param domain: The domain to start/migrate.
		:raises NodeError: if the currently available RAM on the node is not enough.
		"""
		if not self.reservedMem:
			return

		ram_vm = domain.pd.maxMem
		ram_host = self.pd.phyMem - self.pd.curMem
		if ram_vm > ram_host:
			raise NodeError(_('RAM overcommitment: VM RAM %(vm)s exceeds available host RAM %(host)s') % {
				'vm': prettyCapacity(ram_vm),
				'host': prettyCapacity(ram_host),
			})


class Nodes(dict):

	"""Handle registered nodes."""
	IDLE_FREQUENCY = 15 * 1000  # ms
	USED_FREQUENCY = 10 * 1000  # ms
	BEBO_FREQUENCY = 5 * 60 * 1000  # ms

	def __init__(self):
		# type: () -> None
		super(Nodes, self).__init__()
		self.cache_dir = ''

	def __delitem__(self, uri):
		# type: (str) -> None
		"""x.__delitem__(i) <==> del x[i]"""
		self[uri].unregister()
		super(Nodes, self).__delitem__(uri)

	def set_frequency(self, hz):
		# type: (int) -> None
		"""Set polling frequency for update."""
		for node in self.values():
			node.set_frequency(hz)

	def set_cache(self, cache):
		# type: (str) -> None
		"""Register a cache."""
		self.cache_dir = cache

	def add(self, uri):
		# type: (str) -> None
		"""Add node to watch list."""
		if uri in self:
			raise NodeError(_('Hypervisor "%(uri)s" is already connected.'), uri=uri)

		node = Node(uri, cache_dir=self.cache_dir)
		self[uri] = node

		logger.debug("Hypervisor '%s' added.", uri)

	def remove(self, uri):
		# type: (str) -> None
		"""Remove node from watch list."""
		try:
			del self[uri]
		except KeyError:
			raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)
		logger.debug("Hypervisor '%s' removed.", uri)

	def query(self, uri):
		# type: (str) -> Node
		"""Get domain data from node."""
		try:
			node = self[uri]
			return node
		except KeyError:
			raise NodeError(_('Hypervisor "%(uri)s" is not connected.'), uri=uri)

	def frequency(self, hz=IDLE_FREQUENCY, uri=None):
		# type: (int, str) -> None
		"""Set frequency for polling nodes."""
		if uri is None:
			self.set_frequency(hz)
		else:
			node = self.query(uri)
			node.set_frequency(hz)

	def list(self, group, pattern):
		# type: (Optional[str], str) -> List[Node]
		"""Return list of watched nodes matching the given pattern."""
		nodes = []
		if group == 'default' or group is None:  # FIXME
			pattern_regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
			for node_uri in self.keys():
				if pattern_regex.match(node_uri):
					nodes.append(self[node_uri].pd)
		return nodes


nodes = Nodes()
node_add = nodes.add
node_remove = nodes.remove
node_query = nodes.query
node_frequency = nodes.frequency
node_list = nodes.list


def group_list():
	# type: () -> List[str]
	"""Return list of groups for nodes."""
	group = []
	if len(node_list('default', '*')) > 0:
		group.append('default')
	from univention.uvmm.cloudnode import cloudconnections
	if len(cloudconnections.list()) > 0:
		group.append('cloudconnections')
	return group


def _backup(content, fname):
	# type: (str, str) -> None
	"""
	Backup content to file.

	:param str content: The file content.
	:param str fname: The (relative) file name.
	"""
	backup_dir = configRegistry.get('uvmm/backup/directory', '/var/backups/univention-virtual-machine-manager-daemon')
	if not backup_dir:
		return

	path = os.path.join(backup_dir, fname)
	head, tail = os.path.split(path)

	try:
		try:
			os.makedirs(head, 0o700)
		except EnvironmentError as ex:
			if ex.errno != errno.EEXIST:
				raise

		with tempfile.NamedTemporaryFile(delete=False, dir=head) as tmp_file:
			tmp_file.write(content)

		os.rename(tmp_file.name, path)
	except EnvironmentError as ex:
		logger.warning("Failed backup to %s: %s", fname, ex, exc_info=True)
	else:
		logger.info("Domain backuped to %s.", fname)


def _domain_backup(dom, save=True):
	# type: (libvirt.virDomain, bool) -> None
	"""
	Save domain definition to backup file.

	:param libvirt.virDomain dom: libvirt domain instance.
	:param bool save: `True` to create a backup of the previous description (e.g. before deleing), `False` to save the current description.
	"""
	suffix = '.xml.save' if save else '.xml'

	dom_uuid = dom.UUIDString()
	dom_xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE | libvirt.VIR_DOMAIN_XML_INACTIVE)
	if len(dom_xml) < 300:  # minimal XML descriptor length
		logger.error("Failed to backup domain %s: %s", dom_uuid, dom_xml)
		raise NodeError(_("Failed to backup domain %(domain)s: %(xml)s"), domain=dom_uuid, xml=dom_xml)
	_backup(dom_xml, "%s.%s" % (dom_uuid, suffix))

	for snapshot in dom.listAllSnapshots():
		snap_name = snapshot.getName()
		snap_xml = snapshot.getXMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
		_backup(snap_xml, "%s/%s.%s" % (dom_uuid, snap_name, suffix))


def _update_xml(_node_parent, _node_name, _node_value, _changes=set(), **attr):
	# type: (ET._Element, str, Optional[str], Set[Optional[str]], **Any) -> ET._Element
	"""Create, update or delete node named '_node_name' of '_node_parent'.
	If _node_value == None and all(attr == None), then node is deleted.
	"""
	node = _node_parent.find(_node_name, namespaces=XMLNS)
	if _node_value is None and not filter(lambda v: v is not None, attr.values()):
		if node is not None:
			_changes.add(None)
			_node_parent.remove(node)
	else:
		if node is None:
			match = RE_XML_NODE.match(_node_name)
			assert match, _node_name
			prefix, local_name = match.groups()
			if prefix:
				node = ET.SubElement(_node_parent, '{%s}%s' % (XMLNS[prefix], local_name), nsmap=XMLNS)
			else:
				node = ET.SubElement(_node_parent, local_name)
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
	# type: (Node, Data_Domain, Optional[str]) -> Tuple[str, List[str]]
	"""
	Apply python object 'dom_stat' to an XML domain description.

	:param Node node: The host system node.
	:param Data_Domain dom_stat: The virtual machine object.
	:param str xml: libvirt domain XML string.

	:returns: A 2-tuple (xml, updates_xml), where `xml` is the updated domain XML string, `updates_xml` a list of device update XML strings.
	"""
	if xml:
		defaults = False
	else:
		xml = '<domain/>'
		defaults = True
	live_updates = []

	# find loader
	logger.debug('Searching for template: arch=%s domain_type=%s os_type=%s', dom_stat.arch, dom_stat.domain_type, dom_stat.os_type)
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
	_update_xml(domain, 'uuid', dom_stat.uuid)
	# /domain/name
	_update_xml(domain, 'name', dom_stat.name)
	# /domain/description
	description = dom_stat.annotations.get('description') or None
	_update_xml(domain, 'description', description)
	# /domain/os
	domain_os = domain.find('os', namespaces=XMLNS)
	if domain_os is None:
		domain_os = ET.SubElement(domain, 'os')
	# /domain/os/type @arch
	_update_xml(domain_os, 'type', dom_stat.os_type, arch=dom_stat.arch)
	# /domain/os/loader
	if defaults and template and template.loader:
		_update_xml(domain_os, 'loader', template.loader)
	if dom_stat.os_type == 'hvm':
		# /domain/os/boot[]
		domain_os_boots = domain_os.findall('boot', namespaces=XMLNS)
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
		_update_xml(domain, 'bootloader', dom_stat.bootloader)
		# /domain/bootloader_args
		_update_xml(domain, 'bootloader_args', dom_stat.bootloader_args)
	# /domain/memory
	old_maxMem = int(domain.findtext('memory', default=0, namespaces=XMLNS)) << 10  # KiB
	_update_xml(domain, 'memory', '%d' % (dom_stat.maxMem >> 10))  # KiB
	# On change, reset currentMemory to new maxMem as well
	if old_maxMem != dom_stat.maxMem:
		# /domain/currentMemory
		_update_xml(domain, 'currentMemory', '%d' % (dom_stat.maxMem >> 10))  # KiB
	# /domain/vcpu
	_update_xml(domain, 'vcpu', '%d' % dom_stat.vcpus)
	# /domain/cpu/model
	if dom_stat.cpu_model:
		cpu = domain.find('cpu', namespaces=XMLNS)
		if cpu is None:
			cpu = ET.SubElement(domain, 'cpu', mode='custom', match='exact')
		_update_xml(cpu, 'model', dom_stat.cpu_model, fallback='allow')
	elif configRegistry.get('uvmm/vm/cpu/host-model') != 'missing':
		_update_xml(domain, 'cpu', None)

	# /domain/features
	domain_features = _update_xml(domain, 'features', '')
	if defaults and template and template.features or dom_stat.hyperv:
		for f_name in template.features:
			_update_xml(domain_features, f_name, '')
		if dom_stat.hyperv:
			hyperv = _update_xml(domain_features, 'hyperv', '')
			_update_xml(hyperv, 'relaxed', '', state='on')
			_update_xml(hyperv, 'vapic', '', state='on')
			_update_xml(hyperv, 'spinlocks', '', state='on', retries='8191')
		else:
			_update_xml(domain_features, 'hyperv', None)
	else:
		_update_xml(domain_features, 'hyperv', None)

	# /domain/clock @offset @timezone @adjustment
	if dom_stat.rtc_offset in ('utc', 'localtime'):
		clock = _update_xml(domain, 'clock', '', offset=dom_stat.rtc_offset, timezone=None, adjustment=None, basis=None)
	elif dom_stat.rtc_offset == 'variable':
		clock = _update_xml(domain, 'clock', '', offset=dom_stat.rtc_offset, timezone=None)
	elif dom_stat.rtc_offset:
		clock = _update_xml(domain, 'clock', '', offset=dom_stat.rtc_offset)  # timezone='', adjustment=0
	else:
		clock = _update_xml(domain, 'clock', '', offset='utc')
	# /domain/clock/timer
	_update_xml(clock, 'timer[@name="rtc"]', '', name='rtc', present='yes', tickpolicy='catchup')
	_update_xml(clock, 'timer[@name="pit"]', '', name='pit', present='yes', tickpolicy='delay')
	_update_xml(clock, 'timer[@name="hpet"]', '', name='hpet', present='no')
	if dom_stat.hyperv:
		_update_xml(clock, 'timer[@name="hypervclock"]', '', name='hypervclock', present='yes')
	else:
		_update_xml(clock, 'timer[@name="hypervclock"]', None, name=None, present=None)

	# /domain/on_poweroff
	if defaults:
		_update_xml(domain, 'on_poweroff', 'destroy')  # (destroy|restart|preserve|rename-restart)
	# /domain/on_reboot
	if defaults:
		_update_xml(domain, 'on_reboot', 'restart')  # (destroy|restart|preserve|rename-restart)
	# /domain/on_crash
	if defaults:
		_update_xml(domain, 'on_crash', 'destroy')  # (destroy|restart|preserve|rename-restart)

	# /domain/devices/*[]
	domain_devices = _update_xml(domain, 'devices', '')

	# /domain/devices/emulator
	if defaults and template and template.emulator:
		_update_xml(domain_devices, 'emulator', template.emulator)

	# /domain/devices/disk[]
	domain_devices_disks = domain_devices.findall('disk', namespaces=XMLNS)
	disks = {}
	used_addr = {}  # type: Dict[str, Set[int]]
	for domain_devices_disk in domain_devices_disks:
		bus, dev, index = calc_index(domain_devices_disk)
		key = (bus, dev)
		disks[key] = domain_devices_disk
		domain_devices.remove(domain_devices_disk)
		if index is not None:
			used_addr.setdefault(bus, set()).add(index)

	assign_disks(dom_stat.disks, used_addr)
	for disk in dom_stat.disks:
		logger.debug('DISK: %s' % disk)
		changes = set()  # type: Set[Optional[str]]
		# /domain/devices/disk @type @device
		try:
			key = (disk.target_bus, disk.target_dev)
			domain_devices_disk = disks[key]
			domain_devices.append(domain_devices_disk)
		except LookupError:
			domain_devices_disk = ET.SubElement(domain_devices, 'disk')
			# /domain/devices/disk/target @bus @dev
			domain_devices_disk_target = ET.SubElement(domain_devices_disk, 'target')
			domain_devices_disk_target.attrib['bus'] = disk.target_bus or ''
			domain_devices_disk_target.attrib['dev'] = disk.target_dev
		domain_devices_disk.attrib['type'] = disk.type
		domain_devices_disk.attrib['device'] = disk.device
		# /domain/devices/disk/driver @name @type @cache
		_update_xml(domain_devices_disk, 'driver', None, name=disk.driver, type=disk.driver_type, cache=disk.driver_cache)
		# /domain/devices/disk/source @file @dev
		if disk.type == Disk.TYPE_FILE:
			_update_xml(domain_devices_disk, 'source', None, _changes=changes, file=disk.source, dev=None, dir=None, protocol=None)
		elif disk.type == Disk.TYPE_BLOCK:
			_update_xml(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=disk.source, dir=None, protocol=None)
		elif disk.type == Disk.TYPE_DIR:
			_update_xml(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=None, dir=disk.source, protocol=None)
		elif disk.type == Disk.TYPE_NETWORK:
			_update_xml(domain_devices_disk, 'source', None, _changes=changes, file=None, dev=None, dir=None, protocol=disk.source)
		else:
			raise NodeError(_("Unknown disk/type='%(type)s'"), type=disk.type)
		# /domain/devices/disk/readonly
		domain_devices_disk_readonly = domain_devices_disk.find('readonly', namespaces=XMLNS)
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
	domain_devices_interfaces = domain_devices.findall('interface', namespaces=XMLNS)
	interfaces = {}
	for domain_devices_interface in domain_devices_interfaces:
		domain_devices_interface_mac = domain_devices_interface.find('mac', namespaces=XMLNS)
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
			domain_devices_interface_mac.attrib['address'] = interface.mac_address or ''
		domain_devices_interface.attrib['type'] = interface.type
		# /domain/devices/interface/source @bridge @network @dev
		if interface.type == Interface.TYPE_BRIDGE:
			_update_xml(domain_devices_interface, 'source', '', _changes=changes, bridge=interface.source, network=None, dev=None)
		elif interface.type == Interface.TYPE_NETWORK:
			_update_xml(domain_devices_interface, 'source', '', _changes=changes, bridge=None, network=interface.source, dev=None)
		elif interface.type == Interface.TYPE_ETHERNET:
			_update_xml(domain_devices_interface, 'source', None, _changes=changes, bridge=None, network=None, dev=interface.source)
		elif interface.type == Interface.TYPE_DIRECT:
			_update_xml(domain_devices_interface, 'source', '', _changes=changes, bridge=None, network=None, dev=interface.source)
		else:
			raise NodeError(_("Unknown interface/type='%(type)s'"), type=interface.type)
		# /domain/devices/interface/script @bridge
		_update_xml(domain_devices_interface, 'script', None, path=interface.script)
		# /domain/devices/interface/target @dev
		_update_xml(domain_devices_interface, 'target', None, dev=interface.target)
		# /domain/devices/interface/model @dev
		_update_xml(domain_devices_interface, 'model', None, type=interface.model)
		# do live update
		if changes:
			live_updates.append(domain_devices_interface)

	# /domain/devices/input @type @bus
	if dom_stat.os_type == 'hvm':
		# define a tablet usb device which has absolute cursor movement for a better VNC experience. Bug #19244
		domain_devices_inputs = domain_devices.findall('input', namespaces=XMLNS)
		for domain_devices_input in domain_devices_inputs:
			if domain_devices_input.attrib['type'] == 'tablet' and domain_devices_input.attrib['bus'] == 'usb':
				break
		else:
			domain_devices_input = ET.SubElement(domain_devices, 'input', type='tablet', bus='usb')

	# /domain/devices/graphics[]
	domain_devices_graphics = domain_devices.findall('graphics', namespaces=XMLNS)
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
		domain_devices_graphic.attrib['listen'] = graphics.listen or ''
		if node.libvirt_version >= tuple2version((0, 9, 4)):
			domain_devices_graphic_listens = domain_devices_graphic.findall('listen', namespaces=XMLNS)
			for listen in domain_devices_graphic_listens:
				if listen.attrib['type'] != 'address':
					continue
				if graphics.listen:
					listen.attrib['address'] = graphics.listen or ''
				else:
					domain_devices_graphic.remove(listen)
		if domain_devices_graphic.attrib.get('passwd') != graphics.passwd:
			domain_devices_graphic.attrib['passwd'] = graphics.passwd or ''
			live_updates.append(domain_devices_graphic)

	# Make ET happy and cleanup None values
	for n in domain.getiterator():
		for k, v in n.attrib.items():
			if v is None or v == '':
				del n.attrib[k]
			elif not isinstance(v, basestring):
				n.attrib[k] = '%s' % v

	xml_new = ET.tostring(domain)
	updates_xml = [ET.tostring(device) for device in live_updates]
	return (xml_new, updates_xml)


def domain_define(uri, domain):
	# type: (str, Data_Domain) -> Tuple[str, List[str]]
	"""Convert python object to an XML document."""
	node = node_query(uri)
	conn = node.conn
	assert conn is not None
	logger.debug('PY DUMP: %r' % domain.__dict__)

	# Check for (name,uuid) collision
	old_dom = None
	old_xml = None
	try:
		old_dom = conn.lookupByName(domain.name)
		old_uuid = old_dom.UUIDString()
		if old_uuid != domain.uuid:
			raise NodeError(_('Domain name "%(domain)s" already used by "%(uuid)s"'), domain=domain.name, uuid=old_uuid)
		old_xml = old_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE | libvirt.VIR_DOMAIN_XML_INACTIVE)
	except libvirt.libvirtError as ex:
		if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
			logger.error(ex)
			raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.name, error=format_error(ex))
		# rename: name changed, uuid unchanged
		try:
			if domain.uuid:
				old_dom = conn.lookupByUUIDString(domain.uuid)
				old_xml = old_dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE | libvirt.VIR_DOMAIN_XML_INACTIVE)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(ex)
				raise NodeError(_('Error retrieving old domain "%(domain)s": %(error)s'), domain=domain.uuid, error=format_error(ex))

	old_stat = 0
	warnings = []
	if domain.uuid:
		try:
			dom = node.domains[domain.uuid]
		except KeyError:
			pass  # New domain with pre-configured UUID
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
			except StorageError as ex:
				raise NodeError(ex)

	# update running domain definition
	if old_dom and live_updates:
		try:
			if old_dom.isActive():
				for xml in live_updates:
					try:
						logger.debug('DEVICE_UPDATE: %s' % xml)
						rv = old_dom.updateDeviceFlags(xml, (
							libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE |
							libvirt.VIR_DOMAIN_DEVICE_MODIFY_CONFIG
						))
						if rv != 0:
							warnings.append(_('Failed to update device.'))
					except libvirt.libvirtError as ex:
						if ex.get_error_code() == libvirt.VIR_ERR_OPERATION_INVALID:
							pass
						elif ex.get_error_code() == libvirt.VIR_ERR_OPERATION_FAILED:
							# could not change media on drive-ide0-0-0: Device 'drive-ide0-0-0' is locked\r\n
							raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=format_error(ex))
						elif ex.get_error_code() == libvirt.VIR_ERR_SYSTEM_ERROR:
							# unable to open disk path /dev/cdrom: No medium found
							raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=format_error(ex))
						else:
							raise
		except libvirt.libvirtError as ex:
			logger.error(ex)
			raise NodeError(_('Error updating domain "%(domain)s": %(error)s'), domain=domain.uuid, error=format_error(ex))

	# remove old domain definitions
	if old_dom:
		try:
			_domain_backup(old_dom)
			if old_dom.name() != domain.name:  # rename needs undefine
				try:  # all snapshots are destroyed!
					old_dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)  # all snapshots are destroyed!
				except libvirt.libvirtError as ex:
					if ex.get_error_code() not in (libvirt.VIR_ERR_NO_SUPPORT, libvirt.VIR_ERR_INVALID_ARG):
						raise
					old_dom.undefine()
				logger.info('Old domain "%s" removed.', domain.uuid)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error(format_error(ex))
				raise NodeError(_('Error removing domain "%(domain)s": %(error)s'), domain=domain.uuid, error=format_error(ex))

	try:
		logger.debug('XML DUMP: %s' % new_xml.replace('\n', ' '))
		dom2 = conn.defineXML(new_xml)
		domain.uuid = dom2.UUIDString()
		if domain.autostart is not None:
			dom2.setAutostart(domain.autostart)
		_domain_backup(dom2, save=False)
	except libvirt.libvirtError as ex:
		logger.error(format_error(ex))
		raise NodeError(_('Error defining domain "%(domain)s": %(error)s'), domain=domain.name, error=format_error(ex))
	logger.info('New domain "%s"(%s) defined.', domain.name, domain.uuid)

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
		except LdapConnectionError as ex:
			logger.error('Updating LDAP failed, insufficient permissions: %s', ex)
			warnings.append(_('Failed to update the additionally information in the LDAP directory.'))
		except (univention.admin.uexceptions.ldapError, univention.admin.uexceptions.objectExists) as ex:
			logger.error('Updating LDAP failed: %s %s', ex, record)
			warnings.append(_('Failed to update the additionally information in the LDAP directory.'))

	node.wait_update(domain.uuid, old_stat)

	return (domain.uuid, warnings)


def domain_list(uri, pattern='*'):
	# type: (str, str) -> Dict[str, List[Dict[str, Any]]]
	"""Returns a dictionary of domains matching the pattern in name, contact or description.

	return: { 'nodeY' : [ ( <uuid>, <domain name> ), ... ], ... }
	"""
	global nodes

	if uri in ('*', ''):
		node_list = nodes.values()
	else:
		node_list = [node_query(uri)]

	domains = {}
	for node in node_list:
		domains[node.pd.uri] = node.domain_list(pattern)

	return domains


def domain_info(uri, domain):
	# type: (str, str) -> Dict[str, Any]
	"""Return detailed information of a domain."""
	node = node_query(uri)
	# transfer state number into string constant
	if domain not in node.domains:
		raise NodeError(_('Unknown domain "%s"') % domain)
	domain_pd = copy.copy(node.domains[domain].pd)
	domain_pd.state = STATES[domain_pd.state]
	domain_pd.available = node.pd.last_try == node.pd.last_update

	return domain_pd


def domain_state(uri, domain, state):
	# type: (str, str, str) -> None
	"""Change running state of domain on node and wait for updated state."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		stat_key = dom_stat.key()
		try:
			TRANSITION = {
				(libvirt.VIR_DOMAIN_RUNNING, 'PAUSE'): dom.suspend,
				(libvirt.VIR_DOMAIN_RUNNING, 'RESTART'): lambda: dom.reboot(0),
				(libvirt.VIR_DOMAIN_RUNNING, 'RUN'): None,
				(libvirt.VIR_DOMAIN_RUNNING, 'SHUTDOWN'): dom.shutdown,
				(libvirt.VIR_DOMAIN_RUNNING, 'SHUTOFF'): dom.destroy,
				(libvirt.VIR_DOMAIN_RUNNING, 'SUSPEND'): lambda: dom.managedSave(0),
				(libvirt.VIR_DOMAIN_BLOCKED, 'PAUSE'): dom.suspend,
				(libvirt.VIR_DOMAIN_BLOCKED, 'RESTART'): lambda: dom.reboot(0),
				(libvirt.VIR_DOMAIN_BLOCKED, 'RUN'): None,
				(libvirt.VIR_DOMAIN_BLOCKED, 'SHUTDOWN'): dom.shutdown,
				(libvirt.VIR_DOMAIN_BLOCKED, 'SHUTOFF'): dom.destroy,
				(libvirt.VIR_DOMAIN_BLOCKED, 'SUSPEND'): lambda: dom.managedSave(0),
				(libvirt.VIR_DOMAIN_PAUSED, 'PAUSE'): None,
				(libvirt.VIR_DOMAIN_PAUSED, 'RUN'): dom.resume,
				(libvirt.VIR_DOMAIN_PAUSED, 'SHUTDOWN'): dom.destroy,
				(libvirt.VIR_DOMAIN_PAUSED, 'SHUTOFF'): dom.destroy,
				(libvirt.VIR_DOMAIN_SHUTDOWN, 'RUN'): dom.create,
				(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTDOWN'): None,
				(libvirt.VIR_DOMAIN_SHUTDOWN, 'SHUTOFF'): None,
				(libvirt.VIR_DOMAIN_SHUTOFF, 'RUN'): dom.create,
				(libvirt.VIR_DOMAIN_SHUTOFF, 'SHUTDOWN'): None,
				(libvirt.VIR_DOMAIN_SHUTOFF, 'SHUTOFF'): None,
				(libvirt.VIR_DOMAIN_CRASHED, 'RUN'): dom.create,
				(libvirt.VIR_DOMAIN_CRASHED, 'SHUTDOWN'): None,  # TODO destroy?
				(libvirt.VIR_DOMAIN_CRASHED, 'SHUTOFF'): None,  # TODO destroy?
				(libvirt.VIR_DOMAIN_PMSUSPENDED, 'RUN'): lambda: dom.pMWakeup(0),
				(libvirt.VIR_DOMAIN_PMSUSPENDED, 'SHUTDOWN'): None,  # TODO destroy?
				(libvirt.VIR_DOMAIN_PMSUSPENDED, 'SHUTOFF'): None,  # TODO destroy?
			}
			transition = TRANSITION[(dom_stat.pd.state, state)]
		except KeyError:
			cur_state_ = STATES[dom_stat.pd.state]
			raise NodeError(_('Unsupported state transition %(cur_state)s to %(next_state)s'), cur_state=cur_state_, next_state=state)

		if transition:
			if state == 'RUN':
				node._check_ram_overcommit(dom_stat)
				# if interfaces of type NETWORK exist, verify that the network is active
				for nic in dom_stat.pd.interfaces:
					if nic.type == Interface.TYPE_NETWORK:
						network_start(conn, nic.source)
					elif nic.type == Interface.TYPE_BRIDGE:
						network = network_find_by_bridge(conn, nic.source)
						if network:
							network_start(conn, network.name)
			# Detect if VNC is wanted
			wait_for_vnc = state in ('RUN', 'PAUSE') and any(True for dev in dom_stat.pd.graphics if dev.type == Graphic.TYPE_VNC)
			transition()
			for t in range(20):
				if state != 'RUN':
					break
				cur_state = dom.state()[0]
				if cur_state != libvirt.VIR_DOMAIN_PAUSED:
					# do update explicitly
					dom_stat.pd.state = cur_state
					break
				time.sleep(1)
			# wait for update
			node.wait_update(domain, stat_key)
			if wait_for_vnc:
				# wait <=3*10s until port is known
				for t in range(3):
					if any(True for dev in dom_stat.pd.graphics if dev.type == Graphic.TYPE_VNC and 0 <= dev.port < (1 << 16)):
						break
					logger.info('Still waiting for VNC of %s...' % domain)
					stat_key = dom_stat.key()
					node.wait_update(domain, stat_key)

			dom_stat.pd.migration.clear()
	except KeyError as ex:
		logger.error("Domain %s not found", ex)
		raise NodeError(_('Error managing domain "%(domain)s"'), domain=domain)
	except NetworkError as ex:
		logger.error('state: %s', ex)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=str(ex))
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('state: %s', error)
		raise NodeError(_('Error managing domain "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_save(uri, domain, statefile):
	# type: (str, str, str) -> None
	"""Save defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		old_state = node.domains[domain].key()
		dom.save(statefile)
		node.domains[domain].update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('save: %s', error)
		raise NodeError(_('Error saving domain "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_restore(uri, domain, statefile):
	# type: (str, str, str) -> None
	"""Restore defined domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		old_state = node.domains[domain].key()
		conn.restore(statefile)
		node.domains[domain].update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('restore: %s', error)
		raise NodeError(_('Error restoring domain "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_undefine(uri, domain, volumes=[]):
	# type: (str, str, List[str]) -> None
	"""Undefine a domain and its volumes on a node."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		_domain_backup(dom)
		if volumes is None:
			volumes = get_domain_storage_volumes(dom)
		destroy_storage_volumes(conn, volumes, ignore_error=True)
		try:
			if dom.hasManagedSaveImage(0):
				dom.managedSaveRemove(0)
		except libvirt.libvirtError as ex:
			# libvirt returns an 'internal error' when no save image exists
			if ex.get_error_code() != libvirt.VIR_ERR_INTERNAL_ERROR:
				logger.debug('undefine: %s', format_error(ex))
		del node.domains[domain]
		try:
			dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() not in (libvirt.VIR_ERR_NO_SUPPORT, libvirt.VIR_ERR_INVALID_ARG):
				raise
			dom.undefine()
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('undefine: %s', error)
		raise NodeError(_('Error undefining domain "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_migrate(source_uri, domain, target_uri, mode=0):
	# type: (str, str, str, int) -> None
	"""
	Start migration a domain from node to the target node.

	The functions does *not* wait for the migration to finish!

	:param str source_uri: libvirt URI of source node.
	:param str domain: UUID of domain to migrate.
	:param str target_uri: libvirt URI of target node.
	:param int mode: Migration mode: 0 to start normal migration, -1 to abort any running migration, 1..99 to set auto-convergence increment, 100 to force post-copy now.
	:raises NodeError: if migration failes.
	"""
	snapshots = []
	try:
		source_node = node_query(source_uri)
		source_conn = source_node.conn
		if source_conn is not None:
			source_dom = source_conn.lookupByUUIDString(domain)
			source_state, reason = source_dom.state()
		domStat = source_node.domains[domain]

		if source_conn is None:  # offline node
			target_node = node_query(target_uri)
			target_conn = target_node.conn
			assert target_conn is not None

			try:
				cache_file_name = domStat.cache_file_name()
				with open(cache_file_name, 'r') as cache_file:
					xml = cache_file.read()
				target_conn.defineXML(xml)
			except EnvironmentError as ex:
				raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=ex)
			return

		params = {}  # type: Dict[str, Any]
		flags = libvirt.VIR_MIGRATE_PERSIST_DEST | libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
		if source_state in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_BLOCKED, libvirt.VIR_DOMAIN_PAUSED):
			# running domains are live migrated
			stats = source_dom.jobStats()
			if stats['type'] in (libvirt.VIR_DOMAIN_JOB_BOUNDED, libvirt.VIR_DOMAIN_JOB_UNBOUNDED):
				if mode < 0:
					logger.info('Domain "%(domain)s" aborting migration: %(stats)r', dict(domain=domain, stats=stats))
					domStat.pd.migration['msg'] = _('Migration aborted')
					source_dom.abortJob()
				elif mode > 100:
					logger.info('Domain "%(domain)s" switching to post-copy: %(stats)r', dict(domain=domain, stats=stats))
					domStat.pd.migration['msg'] = _('Post-Copy migration forced')
					source_dom.migrateStartPostCopy()
				else:
					fmt, vals = domStat.migration_status(stats)
					raise NodeError(fmt, **vals)
				return

			flags |= libvirt.VIR_MIGRATE_LIVE
			if source_state == libvirt.VIR_DOMAIN_PAUSED:
				if reason in (libvirt.VIR_DOMAIN_PAUSED_MIGRATION, libvirt.VIR_DOMAIN_PAUSED_POSTCOPY, libvirt.VIR_DOMAIN_PAUSED_POSTCOPY_FAILED):
					raise NodeError(_('Domain "%(domain)s" in state "%(state)s" can not be migrated'), domain=domain, state=STATES[source_state])
			elif 1 <= mode <= 99:
				flags |= libvirt.VIR_MIGRATE_AUTO_CONVERGE
				params = {
					libvirt.VIR_MIGRATE_PARAM_AUTO_CONVERGE_INITIAL: min(mode, 10),
					libvirt.VIR_MIGRATE_PARAM_AUTO_CONVERGE_INCREMENT: min(mode, 100 - mode),
				}
			else:
				flags |= libvirt.VIR_MIGRATE_POSTCOPY
		elif source_state in (libvirt.VIR_DOMAIN_SHUTDOWN, libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED):
			# for domains not running their definition is migrated
			flags |= libvirt.VIR_MIGRATE_OFFLINE | libvirt.VIR_MIGRATE_UNSAFE
		else:
			raise NodeError(_('Domain "%(domain)s" in state "%(state)s" can not be migrated'), domain=domain, state=STATES[source_state])

		target_node = node_query(target_uri)
		target_conn = target_node.conn
		assert target_conn is not None

		target_node._check_ram_overcommit(domStat)
		autostart = source_dom.autostart()
		_domain_backup(source_dom)

		def _migrate(errors):
			try:
				while source_dom.snapshotNum() > 0:
					for snapshot in source_dom.listAllSnapshots(libvirt.VIR_DOMAIN_SNAPSHOT_LIST_LEAVES):
						snap_xml = snapshot.getXMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
						snapshots.append(snap_xml)
						logger.info('Deleting snapshot "%s" of domain "%s"', snapshot.getName(), domain)
						snapshot.delete(libvirt.VIR_DOMAIN_SNAPSHOT_DELETE_METADATA_ONLY)
				snapshots.reverse()

				dest_dom = source_dom.migrate3(target_conn, params, flags)
				# domStat.pd.migration is updated by migration_status()
				logger.info('Finished migration of domain "%s" to host "%s" with flags %x', domain, target_uri, flags)
				source_node.domains.pop(domain, None)

				for snap_xml in snapshots:
					snapshot = dest_dom.snapshotCreateXML(snap_xml, libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_REDEFINE)
					logger.info('Added snapshot "%s" of domain "%s"', snapshot.getName(), domain)

				dest_dom.setAutostart(autostart)
			except libvirt.libvirtError as ex:
				logger.error('_migrate: %s', format_error(ex), exc_info=True)

				for snap_xml in snapshots:
					try:
						snapshot = source_dom.snapshotCreateXML(snap_xml, libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_REDEFINE)
						logger.info('Restored snapshot "%s" of domain "%s"', snapshot.getName(), domain)
					except libvirt.libvirtError as ex2:
						logger.error(_('Failed to restore snapshot after failed migration of domain "%(domain)s": %(error)s'), dict(domain=domain, error=format_error(ex2)))

				if ex.get_error_code() == libvirt.VIR_ERR_CPU_INCOMPATIBLE:
					msg = _('The target host has an incompatible CPU; select a different host or try an offline migration. (%(details)s)') % dict(details=ex.get_str2())
				else:
					msg = _('Error migrating domain "%(domain)s": %(error)s') % dict(domain=domain, error=format_error(ex))
				domStat.pd.migration['msg'] = msg
				errors.append(msg)

		logger.info('Starting migration of domain "%s" to host "%s" with flags %x', domain, target_uri, flags)
		domStat.pd.migration['msg'] = _('Migration started')

		errors = []  # type: List[str]
		if flags & libvirt.VIR_MIGRATE_OFFLINE:
			_migrate(errors)
		else:
			thread = threading.Thread(group=None, target=_migrate, name=domain, args=(errors,), kwargs={})
			thread.start()
			thread.join(3.0)

		if errors:
			raise NodeError(errors[0])
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('migrate: %s', error, exc_info=True)
		raise NodeError(_('Error migrating domain "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_snapshot_create(uri, domain, snapshot):
	# type: (str, str, str) -> None
	"""Create new snapshot of domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		if dom_stat.pd.snapshots is None:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		old_state = dom_stat.key()
		xml = '''<domainsnapshot><name>%s</name></domainsnapshot>''' % (xml_escape(snapshot),)
		dom.snapshotCreateXML(xml, 0)

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('snapshot_create: %s', error)
		raise NodeError(_('Error creating "%(domain)s" snapshot: %(error)s'), domain=domain, error=error)


def domain_snapshot_revert(uri, domain, snapshot):
	# type: (str, str, str) -> None
	"""Revert to snapshot of domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
		dom = conn.lookupByUUIDString(domain)
		dom_stat = node.domains[domain]
		if dom_stat.pd.snapshots is None:
			raise NodeError(_('Snapshot not supported "%(node)s"'), node=uri)
		if dom.hasManagedSaveImage(0):
			logger.warning('Domain "%(domain)s" saved state will be removed.' % {'domain': domain})
			dom.managedSaveRemove(0)
		old_state = dom_stat.key()
		snap = dom.snapshotLookupByName(snapshot, 0)
		try:
			# Try unforced revert for backward-compatibility with previous versions first
			res = dom.revertToSnapshot(snap, 0)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_SNAPSHOT_REVERT_RISKY:
				raise
			res = dom.revertToSnapshot(snap, libvirt.VIR_DOMAIN_SNAPSHOT_REVERT_FORCE)
		if res != 0:
			raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=res)

		dom_stat.update(dom)
		node.wait_update(domain, old_state)
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('snapshot_revert: %s', error)
		raise NodeError(_('Error reverting "%(domain)s" to snapshot: %(error)s'), domain=domain, error=error)


def domain_snapshot_delete(uri, domain, snapshot):
	# type: (str, str, str) -> None
	"""Delete snapshot of domain."""
	try:
		node = node_query(uri)
		conn = node.conn
		assert conn is not None
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
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('snapshot_delete: %s', error)
		raise NodeError(_('Error deleting "%(domain)s" snapshot: %(error)s'), domain=domain, error=error)


def domain_update(domain):
	# type: (str) -> None
	"""Trigger update of domain.
	Unfound domains are ignored."""
	global nodes
	# 1st: find domain on the previous host using only (stale) internal data
	for node in nodes.itervalues():
		conn = node.conn
		assert conn is not None
		try:
			dom_stat = node.domains[domain]
			dom = conn.lookupByUUIDString(domain)
			dom_stat.update(dom)
			dom_stat.update_ldap()
			return
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error('update: %s', format_error(ex))
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
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				logger.error('update: %s', format_error(ex))
				raise NodeError(_('Error updating domain "%(domain)s"'), domain=domain)
			else:
				continue  # skip this node
	else:
		logger.info('Domain %s not found for update' % domain)
		raise NodeError(_('Failed to update domain "%(domain)s"'), domain=domain)


def domain_clone(uri, domain, name, subst):
	# type: (str, str, str, Any) -> Tuple[str, List[str]]
	"""Clone a domain."""
	warnings = []
	undo_vol = []
	try:
		try:
			node = node_query(uri)
			conn = node.conn
			assert conn is not None
			try:
				dom = conn.lookupByName(name)
				uuid = dom.UUIDString()
				raise NodeError(_('Domain "%(domain)s" already exists: %(uuid)s'), domain=name, uuid=uuid)
			except libvirt.libvirtError as ex:
				if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
					raise

			dom = conn.lookupByUUIDString(domain)
			dom_stat = node.domains[domain]
			if dom_stat.pd.state != libvirt.VIR_DOMAIN_SHUTOFF:
				raise NodeError(_('Domain "%(domain)s" is not shut off: %(state)d'), domain=domain, state=dom_stat.pd.state)
			try:
				annotations = ldap_annotation(domain)
			except LdapConnectionError as ex:
				warning = 'Failed to get annotations from LDAP for "%(domain)s": %(error)s' % {'domain': domain, 'error': ex}
				logger.warning(warning)
				warnings.append(warning)
				annotations = {}

			xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE | libvirt.VIR_DOMAIN_XML_INACTIVE)
			# /domain
			domain = ET.fromstring(xml)
			# /domain/uuid
			_update_xml(domain, 'uuid', None)  # remove
			# /domain/name
			_update_xml(domain, 'name', name)  # replace
			# /domain/devices/*[]
			domain_devices = _update_xml(domain, 'devices', '')

			# /domain/devices/interface[]
			domain_devices_interfaces = domain_devices.findall('interface', namespaces=XMLNS)
			default_mac = subst.get('mac', 'clone')  # clone or auto
			for domain_devices_interface in domain_devices_interfaces:
				# /domain/devices/interface/mac @address
				domain_devices_interface_mac = domain_devices_interface.find('mac', namespaces=XMLNS)
				mac_address = domain_devices_interface_mac.attrib['address']
				key = 'mac#%s' % (mac_address,)
				try:
					new_mac = subst[key]
				except KeyError:
					if default_mac == 'auto':
						logger.debug('Auto-generating MAC address for %s (default)', mac_address)
						del domain_devices_interface_mac.attrib['address']
					else:
						logger.debug('Keeping MAC address %s (default)', mac_address)
						# nothing to do for mode 'auto'
				else:
					if new_mac:
						logger.debug('Changing MAC from %s to %s', mac_address, new_mac)
						domain_devices_interface_mac.attrib['address'] = new_mac
					else:
						logger.debug('Auto-generating MAC for %s', mac_address)
						del domain_devices_interface_mac.attrib['address']

			# /domain/devices/disk[]
			domain_devices_disks = domain_devices.findall('disk', namespaces=XMLNS)
			for domain_devices_disk in domain_devices_disks:
				# /domain/devices/disk @type @device
				disk_type = domain_devices_disk.attrib['type']
				disk_device = domain_devices_disk.attrib['device']
				# /domain/devices/disk/driver @name @type @cache
				domain_devices_disk_driver = domain_devices_disk.find('driver', namespaces=XMLNS)
				driver_type = domain_devices_disk_driver.attrib.get('type', 'raw')
				# /domain/devices/disk/readonly
				readonly = domain_devices_disk.find('readony', namespaces=XMLNS) is not None
				# /domain/devices/disk/target @bus @dev
				domain_devices_disk_target = domain_devices_disk.find('target', namespaces=XMLNS)
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
					continue  # nothing to clone for shared disks

				# /domain/devices/disk/source @file @dev
				domain_devices_disk_source = domain_devices_disk.find('source', namespaces=XMLNS)
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
				except libvirt.libvirtError as ex:
					if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
						raise
					raise NodeError(_('Volume "%(volume)s" not found: %(error)s'), volume=source, error=format_error(ex))

				# create new name
				old_name = vol.name()

				def new_names():
					key = 'name#%s' % (target_dev,)
					if key in subst:
						yield subst[key]
						return  # Only try the explicit name
					if dom_stat.pd.name in old_name:
						yield old_name.replace(dom_stat.pd.name, name, 1)
					yield '%s_%s%s' % (name, target_dev, suffix)
					yield '%s_%d%s' % (name, domain_devices_disks.index(domain_devices_disk), suffix)
					for i in range(10):
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
				_update_xml(volume, 'name', new_name)  # replace
				# /volume/key
				_update_xml(volume, 'key', None)  # remove
				# /volume/source
				_update_xml(volume, 'source', None)  # remove
				# /volume/target
				volume_target = volume.find('target', namespaces=XMLNS)
				if volume_target:
					# /volume/target/path
					_update_xml(volume_target, 'path', None)  # remove

				if method == 'cow':
					# /volume/backingStore
					volume_backingStore = _update_xml(volume, 'backingStore', '')
					# /volume/backingStore/path
					_update_xml(volume_backingStore, 'path', vol.path())
				xml = ET.tostring(volume)
				logger.debug('Cloning disk: %s', xml)

				try:
					if method == 'copy':
						logger.info('Copying "%(old_volume)s" to "%(new_volume)s" begins' % {'old_volume': old_name, 'new_volume': new_name})
						new_vol = pool.createXMLFrom(xml, vol, 0)
						logger.info('Copying "%(old_volume)s" to "%(new_volume)s" done' % {'old_volume': old_name, 'new_volume': new_name})
					elif method == 'cow':
						logger.info('Backing "%(new_volume)s" by "%(old_volume)s"' % {'old_volume': old_name, 'new_volume': new_name})
						new_vol = pool.createXML(xml, 0)
					undo_vol.append(new_vol)
				except libvirt.libvirtError as ex:
					raise NodeError(_('Failed to clone volume "%(volume)s": %(error)s'), volume=source, error=format_error(ex))

				if disk_type == 'file':
					domain_devices_disk_source.attrib['file'] = new_vol.path()
				elif disk_type == 'block':
					domain_devices_disk_source.attrib['dev'] = new_vol.path()

			xml = ET.tostring(domain)
			logger.debug('Cloning domain: %s', xml)
			dom2 = conn.defineXML(xml)
			uuid = dom2.UUIDString()
			logger.info('Clone domain "%s"(%s) defined.', name, uuid)
			del undo_vol[:]

			annotations['uuid'] = uuid
			try:
				record = ldap_modify(uuid)
				for key, value in annotations.items():
					record[key] = value
			except (LdapConnectionError, univention.admin.uexceptions.ldapError, univention.admin.uexceptions.objectExists) as ex:
				warning = 'Failed to write annotations in LDAP for "%(domain)s": %(error)s' % {'domain': domain, 'error': ex}
				logger.warning(warning)
				warnings.append(warning)

			return (uuid, warnings)
		except libvirt.libvirtError as ex:
			error = format_error(ex)
			logger.error('clone: %s', error)
			raise NodeError(_('Error cloning "%(domain)s": %(error)s'), domain=domain, error=error)
	finally:
		for vol in undo_vol:
			try:
				logger.info('Deleting "%(volume)s"' % {'volume': vol.name()})
				vol.delete(0)
			except Exception as ex:
				logger.warning('Failed undo: %(error)s' % {'error': ex})


def __domain_targethost(uri, domain):
	# type (str, str) -> None
	"""Modify migration target host"""
	try:
		node = node_query(uri)
		conn = node.conn
		domconn = conn.lookupByUUIDString(domain)
		dom = node.domains[domain]
		try:
			xml = domconn.metadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, XMLNS['uvmm'], libvirt.VIR_DOMAIN_AFFECT_CONFIG)
			tree = ET.fromstring(xml)
			domain_targethosts = set(elem.text for elem in tree.findall('hostname'))
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN_METADATA:
				raise
			domain_targethosts = set()

		logger.debug('Migration-target-host of "%s" before modification: %r', domain, domain_targethosts)
		yield domain_targethosts
		logger.debug('Migration-target-host of "%s" after modification: %r', domain, domain_targethosts)

		xml = '<migrationtargethosts>%s</migrationtargethosts>' % (''.join(
			'<hostname>%s</hostname>' % (xml_escape(hostname),) for hostname in domain_targethosts
		),)
		if domconn.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, xml, 'uvmm', XMLNS['uvmm'], libvirt.VIR_DOMAIN_AFFECT_CONFIG):
			logger.error('Failed to update config metadata XML of "%s"', domain)
		if domconn.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, xml, 'uvmm', XMLNS['uvmm'], 0):
			logger.warning('Failed to update current metadata XML of "%s"', domain)

		dom.pd.targethosts = domain_targethosts
	except libvirt.libvirtError as ex:
		error = format_error(ex)
		logger.error('targethost: %s', error)
		raise NodeError(_('Error modifying migrationtargethost "%(domain)s": %(error)s'), domain=domain, error=error)


def domain_targethost_add(uri, domain, targethost):
	# type (str, str, str) -> None
	"""Add a migration target host"""
	for hosts in __domain_targethost(uri, domain):
		hosts.add(targethost)


def domain_targethost_remove(uri, domain, targethost):
	# type (str, str, str) -> None
	"""Remove a migration target host"""
	for hosts in __domain_targethost(uri, domain):
		hosts.discard(targethost)
