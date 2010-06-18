#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  storage handler
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
"""UVMM storage handler.

This module implements functions to handle storage on nodes. This is independent from the on-wire-format.
"""

import libvirt
import logging
from xml.dom.minidom import getDOMImplementation, parseString
from helpers import TranslatableException, N_ as _
import os.path

logger = logging.getLogger('uvmmd.storage')

class StorageError(TranslatableException):
	"""Error while handling storage."""
	pass

def create_storage_pool(conn, dir, pool_name='default'):
	"""Create directory pool."""
	xml = '''
	<pool type="dir">
		<name>%(pool)s</name>
		<target>
			<path>%(path)s</path>
		</target>
	</pool>
	''' % {
			'pool': pool_name,
			'path': dir,
			}
	try:
		p = conn.storagePoolDefineXML(xml, 0)
		p.setAutostart(True)
	except libvirt.libvirtError, e:
		raise StorageError(_('Error creating storage pool "%(pool)s" for "%(domain)s": %(error)s'), pool=pool_name, domain=domain.name, error=e)

def create_storage_volume(conn, domain, disk):
	"""Create disk for domain."""
	try:
		v = conn.storageVolLookupByPath(disk.source)
		logger.warning('Reusing existing volume "%s" for domain "%s"' % (disk.source, domain.name))
		return v
	except libvirt.libvirtError, e:
		if e.get_error_code() != libvirt.VIR_ERR_INVALID_STORAGE_VOL:
			raise StorageError(_('Error locating storage volume "%(volume)s" for "%(domain)s": %(error)s'), volume=disk.source, domain=domain.name, error=e)

	for pool_name in conn.listStoragePools() + conn.listDefinedStoragePools():
		try:
			p = conn.storagePoolLookupByName(pool_name)
			xml = p.XMLDesc(0)
			doc = parseString(xml)
			path = doc.getElementsByTagName('path')[0].firstChild.nodeValue
			if disk.source.startswith(path):
				break
		except libvirt.libvirtError, e:
			if e.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_POOL:
				raise StorageError(_('Error locating storage pool "%(pool)s" for "%(domain)s": %(error)s'), pool=pool_name, domain=domain.name, error=e)
		except IndexError, e:
			pass
	else:
		logger.warning('Volume "%(volume)s" for "%(domain)s" in not located in any storage pool.' % {'volume': disk.source, 'domain': domain.name})
		return None # FIXME
		#raise StorageError(_('Volume "%(volume)s" for "%(domain)s" in not located in any storage pool.'), volume=disk.source, domain=domain.name)
		#create_storage_pool(conn, path.dirname(disk.source))

	xml = '''
	<volume>
		<name>%(name)s</name>
		<allocation unit="G">0</allocation>
		<capacity unit="G">%(size)d</capacity>
		<target>
			<format type="raw"/>
		</target>
	</volume>
	''' % {
			'name': os.path.basename(disk.source),
			'size': 8, # FIXME
			}
	try:
		v = p.createXML(xml, 0)
		logger.info('New disk "%s" for "%s"(%s) defined.' % (v.path(), domain.name, domain.uuid))
		return v
	except libvirt.libvirtError, e:
		raise StorageError(_('Error creating storage volume "%(name)s" for "%(domain)s": %(error)s'), name=disk.source, domain=domain.name, error=e)

def get_all_storage_volumes(conn, domain):
	"""Retrieve alls referenced storage volumes."""
	volumes = []
	doc = parseString(domain.XMLDesc(0))
	devices = doc.getElementsByTagName('devices')[0]
	disks = devices.getElementsByTagName('disk')
	for disk in disks:
		source = disk.getElementsByTagName('source')[0]
		volumes.append(source.getAttribute('file'))
	return volumes

def destroy_storage_volumes(conn, volumes, ignore_error=False):
	"""Destroy volumes."""
	# 1. translate names into references
	refs = []
	for name in volumes:
		try:
			ref = conn.storageVolLookupByKey(name)
			refs.append(ref)
		except libvirt.libvirtError, e:
			if ignore_error:
				logger.warning("Error translating name to volume: %s" % e)
			else:
				logger.error("Error translating name to volume: %s. Ignored." % e)
				raise
	# 2. delete them all
	for volume in refs:
		try:
			volume.delete(0)
		except libvirt.libvirtError, e:
			if ignore_error:
				logger.warning("Error deleting volume: %s" % e)
			else:
				logger.error("Error deleting volume: %s. Ignored." % e)
				raise

def storage_pools(uri):
	"""List all pools."""
	from protocol import Data_Pool
	try:
		node = node_query(uri)
		conn = node.conn
		pools = []
		for name in conn.listStoragePools() + conn.listDefinedStoragePools():
			p = conn.storagePoolLookupByName(name)
			xml = p.XMLDesc(0)
			doc = parseString(xml)
			pool = Data_Pool()
			pool.name = name
			pool.uuid = doc.getElementsByTagName('uuid')[0].firstChild.nodeValue
			pool.capacity = int(doc.getElementsByTagName('capacity')[0].firstChild.nodeValue)
			pool.available = int(doc.getElementsByTagName('available')[0].firstChild.nodeValue)
			pool.path = doc.getElementsByTagName('path')[0].firstChild.nodeValue
			pools.append(pool)
		return pools
	except libvirt.libvirtError, e:
		logger.error(e)
		raise StorageError(_('Error listing pools at "%(uri)s": %(error)s'), uri=uri, error=e)
