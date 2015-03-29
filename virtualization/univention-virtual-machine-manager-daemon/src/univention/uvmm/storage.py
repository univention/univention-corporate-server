# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  storage handler
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
"""UVMM storage handler.

This module implements functions to handle storage on nodes. This is
independent from the on-wire-format.
"""

import libvirt
import logging
from helpers import TranslatableException, N_ as _, TimeoutError, timeout
from protocol import Disk, Data_Pool
import os.path
import univention.config_registry as ucr
import time
from xml.sax.saxutils import escape as xml_escape
try:
	from lxml import etree as ET
except ImportError:
	import xml.etree.ElementTree as ET

POOLS_RW = set(('dir', 'disk', 'fs', 'netfs', 'logical'))
POOLS_TYPE = {
		'dir': Disk.TYPE_FILE,
		'disk': Disk.TYPE_BLOCK,
		'fs': Disk.TYPE_FILE,
		'iscsi': Disk.TYPE_BLOCK,
		'logical': Disk.TYPE_BLOCK,
		'mpath': Disk.TYPE_BLOCK,
		'netfs': Disk.TYPE_FILE,
		'scsi': Disk.TYPE_BLOCK,
		}

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.storage')


class StorageError(TranslatableException):
	"""Error while handling storage."""
	pass


def create_storage_pool(conn, path, pool_name='default'):
	"""Create directory pool."""
	# FIXME: support other types than dir
	xml = '''
	<pool type="dir">
		<name>%(pool)s</name>
		<target>
			<path>%(path)s</path>
		</target>
	</pool>
	''' % {
			'pool': xml_escape(pool_name),
			'path': xml_escape(path),
			}
	try:
		pool = conn.storagePoolDefineXML(xml, 0)
		pool.setAutostart(True)
		pool.create(0)
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise StorageError(
				_('Error creating storage pool "%(pool)s": %(error)s'),
				pool=pool_name,
				error=ex.get_error_message(),
				)


def create_storage_volume(conn, domain, disk):
	"""Create disk for domain."""
	try:
		# BUG #19342: does not find volumes in sub-directories
		vol = conn.storageVolLookupByPath(disk.source)
		logger.warning(
				'Reusing existing volume "%s" for domain "%s"',
				disk.source,
				domain.name,
				)
		return vol
	except libvirt.libvirtError, ex:
		logger.info(
				'create_storage_volume: libvirt error (%d): %s',
				ex.get_error_code(),
				ex,
				)
		if not ex.get_error_code() in (
				libvirt.VIR_ERR_INVALID_STORAGE_VOL,
				libvirt.VIR_ERR_NO_STORAGE_VOL,
				):
			raise StorageError(
					_('Error locating storage volume "%(volume)s" for "%(domain)s": %(error)s'),
					volume=disk.source,
					domain=domain.name,
					error=ex.get_error_message(),
					)

	best = (0, None, '')
	for pool_name in conn.listStoragePools() + conn.listDefinedStoragePools():
		try:
			pool = conn.storagePoolLookupByName(pool_name)
			xml = pool.XMLDesc(0)
			pool_tree = ET.fromstring(xml)
			pool_type = pool_tree.attrib['type']
			path = pool_tree.find('target').findtext('path')
			if '/' != path[-1]:
				path += '/'
			if disk.source.startswith(path):
				length = len(path)
				if length > best[0]:
					best = (length, pool, pool_type)
		except libvirt.libvirtError, ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_POOL:
				logger.error(ex)
				raise StorageError(
						_('Error locating storage pool "%(pool)s" for "%(domain)s": %(error)s'),
						pool=pool_name,
						domain=domain.name,
						error=ex.get_error_message(),
						)
		except IndexError, ex:
			pass
	length, pool, pool_type = best
	if not length:
		logger.warning(
				'Volume "%s" for "%s" in not located in any storage pool.',
				disk.source,
				domain.name,
				)
		return None # FIXME
		#raise StorageError(_('Volume "%(volume)s" for "%(domain)s" in not located in any storage pool.'), volume=disk.source, domain=domain.name)
		#create_storage_pool(conn, path.dirname(disk.source))
	try:
		if pool_type in ('dir', 'fs', 'netfs'):
			pool.refresh(0)
		vol = pool.storageVolLookupByName(disk.source[length:])
		logger.warning(
				'Reusing existing volume "%s" for domain "%s"',
				disk.source,
				domain.name,
				)
		return vol
	except libvirt.libvirtError, ex:
		logger.info(
				'create_storage_volume: libvirt error (%d): %s',
				ex.get_error_code(),
				ex,
				)
		if not ex.get_error_code() in (
				libvirt.VIR_ERR_INVALID_STORAGE_VOL,
				libvirt.VIR_ERR_NO_STORAGE_VOL,
				):
			raise StorageError(
					_('Error locating storage volume "%(volume)s" for "%(domain)s": %(error)s'),
					volume=disk.source,
					domain=domain.name,
					error=ex.get_error_message(),
					)

	if hasattr(disk, 'size') and disk.size:
		size = disk.size
	else:
		size = 8 << 30 # GiB

	values = {
			'name': xml_escape(os.path.basename(disk.source)),
			'size': size,
			}

	if POOLS_TYPE.get(pool_type) == Disk.TYPE_FILE:
		if hasattr(disk, 'driver_type') and disk.driver_type not in (None, 'iso', 'aio'):
			values['type'] = xml_escape(disk.driver_type)
		else:
			values['type'] = 'raw'
		# permissions
		permissions = [(access, configRegistry.get('uvmm/volume/permissions/%s' % access, None))
				for access in ('owner', 'group', 'mode')]
		permissions = ['\t\t\t<%(tag)s>%(value)s</%(tag)s>' % {
			'tag': xml_escape(key),
			'value': xml_escape(value),
			} for (key, value) in permissions if value and value.isdigit()]
		if permissions:
			permissions = '\t\t<permissions>\n%s\n\t\t</permissions>' % (
					'\n'.join(permissions),
					)
		else:
			permissions = ''

		template = '''
		<volume>
			<name>%%(name)s</name>
			<source/>
			<capacity>%%(size)ld</capacity>
			<allocation>0</allocation>
			<target>
				<format type="%%(type)s"/>
				%s
			</target>
		</volume>
		''' % permissions
	elif pool_type == 'logical':
		template = '''
		<volume>
			<name>%(name)s</name>
			<source/>
			<capacity>%(size)ld</capacity>
			<target/>
		</volume>
		'''
	else:
		logger.error(
				"Unsupported storage-pool-type %s for %s:%s",
				pool_type,
				domain.name,
				disk.source,
				)
		raise StorageError(
				_('Unsupported storage-pool-type "%(pool_type)s" for "%(domain)s"'),
				pool_type=pool_type,
				domain=domain.name,
				)

	xml = template % values
	try:
		logger.debug('XML DUMP: %s' % xml)
		vol = pool.createXML(xml, 0)
		logger.info(
				'New disk "%s" for "%s"(%s) defined.',
				vol.path(),
				domain.name,
				domain.uuid,
				)
		return vol
	except libvirt.libvirtError, ex:
		if ex.get_error_code() in (libvirt.VIR_ERR_NO_STORAGE_VOL,):
			logger.warning(
					'Reusing existing volume "%s" for domain "%s"',
					disk.source,
					domain.name,
					)
			return None
		logger.error(ex)
		raise StorageError(
				_('Error creating storage volume "%(name)s" for "%(domain)s": %(error)s'),
				name=disk.source,
				domain=domain.name,
				error=ex.get_error_message(),
				)


def get_storage_volumes(node, pool_name, type=None):
	"""
	Get 'protocol.Disk' instance for all Storage Volumes in named pool of
	given type.
	"""
	if node.conn is None:
		raise StorageError(
				_('Error listing volumes at "%(uri)s": %(error)s'),
				uri=node.uri,
				error='no connection'
				)
	volumes = []
	try:
		pool = timeout(node.conn.storagePoolLookupByName)(pool_name)

		xml = pool.XMLDesc(0)
		pool_tree = ET.fromstring(xml)
		pool_type = pool_tree.attrib['type']
		if pool_type in ('dir', 'fs', 'netfs'):
			pool.refresh(0)
	except TimeoutError, ex:
		logger.warning('libvirt connection "%s" timeout: %s', node.pd.uri, ex)
		node.pd.last_try = time.time()
		return volumes
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise StorageError(
				_('Error listing volumes at "%(uri)s": %(error)s'),
				uri=node.pd.uri,
				error=ex.get_error_message(),
				)

	xml = pool.XMLDesc(0)
	pool_tree = ET.fromstring(xml)
	pool_type = pool_tree.attrib['type']

	for name in pool.listVolumes():
		vol = pool.storageVolLookupByName( name )
		xml = vol.XMLDesc( 0 )
		try:
			volume_tree = ET.fromstring(xml)
		except ET.XMLSyntaxError:
			continue
		disk = Disk()
		disk.pool = pool_name
		disk.size = int(volume_tree.findtext('capacity'))
		target = volume_tree.find('target')
		disk.source = target.findtext('path')

		disk.type = POOLS_TYPE.get(pool_type)
		if disk.type == Disk.TYPE_FILE:
			disk.driver_type = target.find('format').attrib['type']
			if disk.driver_type == 'iso':
				disk.device = Disk.DEVICE_CDROM
			else:
				disk.device = Disk.DEVICE_DISK
		elif disk.type == Disk.TYPE_BLOCK:
			disk.device = Disk.DEVICE_DISK
			disk.driver_type = None # raw
		elif disk.source.startswith('/dev/'):
			disk.type = Disk.TYPE_BLOCK
			disk.device = Disk.DEVICE_DISK
			disk.driver_type = None # raw
		else:
			logger.info('Unsupported storage pool type: %s', pool_type)
			continue

		if not type or disk.device == type:
			volumes.append( disk )

	return volumes


def get_domain_storage_volumes(domain):
	"""Retrieve all referenced storage volumes."""
	volumes = []
	try:
		xml = domain.XMLDesc(0)
		domain_tree = ET.fromstring(xml)
	except ET.XMLSyntaxError:
		return volumes

	for disk in domain_tree.find('devices').findall('disk'):
		source = disk.find('source')
		if source is not None:
			vol = source.attrib.get('file')
			if vol:
				volumes.append(vol)

	return volumes


def destroy_storage_volumes(conn, volumes, ignore_error=False):
	"""Destroy volumes."""
	# 1. translate names into references
	refs = []
	for name in volumes:
		try:
			ref = conn.storageVolLookupByPath(name)
			refs.append(ref)
		except libvirt.libvirtError, ex:
			if ignore_error:
				logger.warning(
						"Error translating '%s' to volume: %s",
						name,
						ex.get_error_message(),
						)
			else:
				logger.error(
						"Error translating '%s' to volume: %s. Ignored.",
						name,
						ex.get_error_message(),
						)
				raise
	# 2. delete them all
	for volume in refs:
		try:
			volume.delete(0)
		except libvirt.libvirtError, ex:
			if ignore_error:
				logger.warning(
						"Error deleting volume: %s",
						ex.get_error_message(),
						)
			else:
				logger.error(
						"Error deleting volume: %s. Ignored.",
						ex.get_error_message(),
						)
				raise


def get_pool_info(node, name):
	"""
	Get 'protocol.Data_Pool' instance for named pool.
	"""
	try:
		pool = node.conn.storagePoolLookupByName( name )
	except libvirt.libvirtError, ex:
		if ex.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_POOL:
			raise KeyError(name)
		logger.error(ex)
		raise StorageError(
				_('Error listing pools at "%(uri)s": %(error)s'),
				uri=node.pd.uri,
				error=ex.get_error_message(),
				)
	xml = pool.XMLDesc(0)
	pool_tree = ET.fromstring(xml)
	res = Data_Pool()
	res.name = name
	res.uuid = pool_tree.findtext('uuid')
	res.capacity = int(pool_tree.findtext('capacity'))
	res.available = int(pool_tree.findtext('available'))
	res.path = pool_tree.find('target').findtext('path')
	res.active = pool.isActive() == 1
	res.type = pool_tree.attrib['type']  # pool/@type
	return res


def storage_pools(node):
	"""
	Get 'protocol.Data_Pool' instance for all (active) pools.
	"""
	if node.conn is None:
		raise StorageError(
				_('Error listing pools at "%(uri)s": %(error)s'),
				uri=node.pd.uri,
				error='no connection'
				)
	try:
		pools = []
		for name in timeout(node.conn.listStoragePools)():
			pool = get_pool_info(node, name)
			pools.append( pool )
		return pools
	except TimeoutError, ex:
		logger.warning(
				'libvirt connection "%s" timeout: %s',
				node.pd.uri,
				ex,
				)
		node.pd.last_try = time.time()
		return pools
	except libvirt.libvirtError, ex:
		logger.error(ex)
		raise StorageError(
				_('Error listing pools at "%(uri)s": %(error)s'),
				uri=node.uri,
				error=ex.get_error_message(),
				)


def storage_volume_usedby( nodes, volume_path, ignore_cdrom = True ):
	"""Returns a list of tuples ( <node URI>, <domain UUID> ) of domains
	that use the given volume"""
	used_by = []
	for uri, node in nodes.items():
		for _uuid, domain in node.domains.items():
			for device in domain.pd.disks:
				if ignore_cdrom and device.device == Disk.DEVICE_CDROM:
					continue
				if device.source == volume_path:
					used_by.append((uri, domain.pd.uuid))
	return used_by
