#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""Test univention.uvmm.storage.*"""
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
from os.path import dirname, join
from textwrap import dedent
from unittest import main, TestCase

from libvirt import libvirtError, VIR_ERR_NO_STORAGE_VOL

import univention
univention.__path__.append(join(dirname(__file__), '../src/univention'))  # type: ignore
from univention.uvmm.storage import create_storage_volume, get_domain_storage_volumes, get_pool_info, get_storage_volumes  # noqa: F402
from univention.uvmm.protocol import Disk  # noqa: F402


class _Storage(TestCase):

	def setUp(self):
		self.xml = dedent(self.__doc__)


class _StoragePool(_Storage):

	"""
	<pool type='dir'>
		<name>default</name>
		<uuid>e6fd2acc-72b7-3796-34e2-dc5d29e58448</uuid>
		<capacity unit='bytes'>274658435072</capacity>
		<allocation unit='bytes'>198527012864</allocation>
		<available unit='bytes'>76131422208</available>
		<source>
		</source>
		<target>
			<path>/var/lib/libvirt/images</path>
			<permissions>
				<mode>0700</mode>
				<owner>-1</owner>
				<group>-1</group>
			</permissions>
		</target>
	</pool>
	"""

	DNAME = '/var/lib/libvirt/images'
	FNAME = 'ucs401-0.qcow2'
	PNAME = join(DNAME, FNAME)
	POOL = 'default'

	def setUp(self):
		self.__doc__ = _StoragePool.__doc__
		super(_StoragePool, self).setUp()

	def XMLDesc(self, flags):  # pool
		assert flags == 0
		return self.xml

	def refresh(self, flags):  # pool
		assert flags == 0

	def listVolumes(self):  # pool
		return [self.FNAME]

	def _null(self):
		pass

	def name(self):  # pool
		return self.POOL


class TestCreateStorageVolume(_StoragePool):

	def storageVolLookupByPath(self, path):  # conn
		assert path == self.PNAME
		ex = libvirtError("")
		ex.err = (VIR_ERR_NO_STORAGE_VOL, None, None, None, None, None, None, None, None)
		raise ex

	def listStoragePools(self):  # conn
		return [self.POOL]

	def listDefinedStoragePools(self):  # conn
		return [self.POOL]

	def storagePoolLookupByName(self, name):  # conn
		assert name == self.POOL
		return self

	def listAllStoragePools(self):  # conn
		return []

	def storageVolLookupByName(self, name):  # pool
		assert name == self.FNAME
		ex = libvirtError("")
		ex.err = (VIR_ERR_NO_STORAGE_VOL, None, None, None, None, None, None, None, None)
		raise ex

	def createXML(self, xml, flags):  # pool
		assert flags == 0
		self.assertTrue(xml)
		return self

	def path(self):  # volume
		return self.PNAME

	def test_create_storage_volume(self):
		create_storage_volume(conn=self, domain=self, disk=self)

	@property
	def name(self):  # domain
		return 'domain'

	@property
	def uuid(self):  # domain
		return 'UUID'

	@property
	def source(self):  # disk
		return self.PNAME

	@property
	def size(self):  # disk
		return 1 << 30  # GiB

	@property
	def driver_type(self):  # disk
		return 'qcow2'


class TestGetDomainStorageVolumes(_Storage):

	"""
	<domain type='kvm'>
		<devices>
			<disk type='file' device='disk'>
				<driver name='qemu' type='qcow2' cache='none'/>
				<source file='/var/lib/libvirt/images/ucs401-0.qcow2'/>
				<target dev='vda' bus='virtio'/>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
			</disk>
			<disk type='file' device='cdrom'>
				<driver name='qemu' type='raw'/>
				<source file='/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso'/>
				<target dev='hda' bus='ide'/>
				<readonly/>
				<address type='drive' controller='0' bus='0' target='0' unit='0'/>
			</disk>
		</devices>
	</domain>
	"""

	def XMLDesc(self, flags):
		assert flags == 0
		return self.xml

	def test_get_domain_storage_volumes(self):
		devices = get_domain_storage_volumes(self)
		self.assertEqual([
			'/var/lib/libvirt/images/ucs401-0.qcow2',
			'/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso',
		], devices)


class TestGetPoolInfo(_StoragePool):

	def isActive(self):  # pool
		return True

	def test_pool_info(self):
		pool = get_pool_info(pool=self)
		self.assertEqual('default', pool.name)
		self.assertEqual('e6fd2acc-72b7-3796-34e2-dc5d29e58448', pool.uuid)
		self.assertEqual(274658435072, pool.capacity)
		self.assertEqual(76131422208, pool.available)
		self.assertEqual(self.DNAME, pool.path)
		self.assertTrue(pool.active)
		self.assertEqual('dir', pool.type)


class TestGetStorageVolumes(_Storage):

	"""
	<volume type='file'>
		<name>ucs401-0.qcow2</name>
		<key>/var/lib/libvirt/images/ucs401-0.qcow2</key>
		<source>
		</source>
		<capacity unit='bytes'>10737418240</capacity>
		<allocation unit='bytes'>6306344960</allocation>
		<target>
			<path>/var/lib/libvirt/images/ucs401-0.qcow2</path>
			<format type='qcow2'/>
			<permissions>
				<mode>0600</mode>
				<owner>0</owner>
				<group>0</group>
			</permissions>
			<timestamps>
				<atime>1427408403.452087425</atime>
				<mtime>1426580675.981340941</mtime>
				<ctime>1426580678.265360980</ctime>
			</timestamps>
		</target>
	</volume>
	"""

	@property
	def conn(self):  # node
		return self

	def storagePoolLookupByName(self, name):  # conn
		assert name == _StoragePool.POOL
		pool = _StoragePool(methodName='_null')
		pool.setUp()
		pool.storageVolLookupByName = self.storageVolLookupByName
		pool.listAllVolumes = self.listAllVolumes
		return pool

	def storageVolLookupByName(self, name):
		assert name == _StoragePool.FNAME
		return self

	def XMLDesc(self, flags):
		assert flags == 0
		return self.xml

	def listAllVolumes(self):  # pool
		return [self]

	def test_get_storage_volumes(self):
		volumes = get_storage_volumes(node=self, pool_name=_StoragePool.POOL)
		self.assertEqual(1, len(volumes))
		v = volumes[0]
		self.assertEqual(_StoragePool.POOL, v.pool)
		self.assertEqual(10737418240, v.size)
		self.assertEqual(_StoragePool.PNAME, v.source)
		self.assertEqual(Disk.TYPE_FILE, v.type)
		self.assertEqual('qcow2', v.driver_type)
		self.assertEqual(Disk.DEVICE_DISK, v.device)


if __name__ == '__main__':
	main()
