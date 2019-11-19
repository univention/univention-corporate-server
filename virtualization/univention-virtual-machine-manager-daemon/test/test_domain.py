#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""Test univention.uvmm.node.Domain"""
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
from unittest import main, TestCase
from textwrap import dedent

import univention
univention.__path__.append(join(dirname(__file__), '../src/univention'))  # type: ignore
from univention.uvmm.node import Domain  # noqa: F402
from univention.uvmm.protocol import Data_Domain  # noqa: F402


class _Domain(TestCase):

	def setUp(self):
		xml = dedent(self.__doc__)
		self.dom = Domain(xml, None)
		self.default = Data_Domain()


class TestDomainKVM(_Domain):

	"""
	<domain type='kvm'>
		<name>ucs401</name>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<metadata>
			<uvmm:migrationtargethosts xmlns:uvmm="https://univention.de/uvmm/1.0">
				<uvmm:hostname>host5.phahn.dev</uvmm:hostname>
				<uvmm:hostname>host6.phahn.dev</uvmm:hostname>
			</uvmm:migrationtargethosts>
		</metadata>
		<description>https://forge.univention.org/bugzilla/show_bug.cgi?id=36640</description>
		<memory unit='KiB'>1048576</memory>
		<currentMemory unit='KiB'>1048576</currentMemory>
		<vcpu placement='static'>1</vcpu>
		<os>
			<type arch='x86_64' machine='pc-1.1'>hvm</type>
			<boot dev='cdrom'/>
			<boot dev='hd'/>
		</os>
		<features>
			<acpi/>
			<apic/>
		</features>
		<clock offset='utc'/>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
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
			<controller type='usb' index='0'>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x2'/>
			</controller>
			<controller type='pci' index='0' model='pci-root'/>
			<controller type='ide' index='0'>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
			</controller>
			<interface type='bridge'>
				<mac address='52:54:00:71:90:4b'/>
				<source bridge='br0'/>
				<model type='virtio'/>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
			</interface>
			<input type='tablet' bus='usb'/>
			<input type='mouse' bus='ps2'/>
			<input type='keyboard' bus='ps2'/>
			<graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0' keymap='en'>
				<listen type='address' address='0.0.0.0'/>
			</graphics>
			<video>
				<model type='cirrus' vram='9216' heads='1'/>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
			</video>
			<memballoon model='virtio'>
				<address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
			</memballoon>
		</devices>
	</domain>
	"""

	def test_domain_type(self):
		self.assertEqual('kvm', self.dom.pd.domain_type)

	def test_name(self):
		self.assertEqual('ucs401', self.dom.pd.name)

	def test_uuid(self):
		self.assertEqual('da33829a-4c56-4626-8d33-beec0580fc10', self.dom.pd.uuid)

	def test_os_type(self):
		self.assertEqual('hvm', self.dom.pd.os_type)

	def test_arch(self):
		self.assertEqual('x86_64', self.dom.pd.arch)

	def test_kernel(self):
		self.failIf(self.dom.pd.kernel)

	def test_cmdline(self):
		self.failIf(self.dom.pd.cmdline)

	def test_initrd(self):
		self.failIf(self.dom.pd.initrd)

	def test_boot(self):
		self.assertEqual(['cdrom', 'hd'], self.dom.pd.boot)

	def test_rtc_offset(self):
		self.assertEqual('utc', self.dom.pd.rtc_offset)

	def test_disk0(self):
		d = self.dom.pd.disks[0]
		self.assertEqual('file', d.type)
		self.assertEqual('disk', d.device)
		self.assertEqual('qemu', d.driver)
		self.assertEqual('qcow2', d.driver_type)
		self.assertEqual('none', d.driver_cache)
		self.assertEqual('/var/lib/libvirt/images/ucs401-0.qcow2', d.source)
		self.assertEqual('vda', d.target_dev)
		self.assertEqual('virtio', d.target_bus)
		self.assertFalse(d.readonly)

	def test_disk1(self):
		d = self.dom.pd.disks[1]
		self.assertEqual('file', d.type)
		self.assertEqual('cdrom', d.device)
		self.assertEqual('qemu', d.driver)
		self.assertEqual('raw', d.driver_type)
		self.assertEqual('', d.driver_cache)  # Disk.CACHE_DEFAULT
		self.assertEqual('/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso', d.source)
		self.assertEqual('hda', d.target_dev)
		self.assertEqual('ide', d.target_bus)
		self.assertTrue(d.readonly)

	def test_interface0(self):
		i = self.dom.pd.interfaces[0]
		self.assertEqual('bridge', i.type)
		self.assertEqual('52:54:00:71:90:4b', i.mac_address)
		self.assertEqual('br0', i.source)
		self.failIf(i.script)
		self.failIf(i.target)
		self.assertEqual('virtio', i.model)

	def test_graphics0(self):
		g = self.dom.pd.graphics[0]
		self.assertEqual('vnc', g.type)
		self.assertEqual(-1, g.port)
		self.assertTrue(g.autoport)
		self.assertEqual('0.0.0.0', g.listen)
		self.failIf(g.passwd)
		self.assertEqual('en', g.keymap)

	def test_metadata(self):
		t = self.dom.pd.targethosts
		self.assertEqual(['host5.phahn.dev', 'host6.phahn.dev'], t)


class TestDomainXenHVM(_Domain):

	"""
	<domain type="xen">
		<name>ucs401</name>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<os>
			<type>hvm</type>
			<loader>/usr/lib/xen/boot/hvmloader</loader>
			<boot dev='hd'/>
		</os>
		<devices>
			<emulator>/usr/lib64/xen/bin/qemu-dm</emulator>
		</devices>
	</domain>
	"""

	def test_domain_type(self):
		self.assertEqual('xen', self.dom.pd.domain_type)

	def test_os_type(self):
		self.assertEqual('hvm', self.dom.pd.os_type)

	def test_arch(self):
		self.assertEqual(self.default.arch, self.dom.pd.arch)

	def test_kernel(self):
		self.failIf(self.dom.pd.kernel)

	def test_cmdline(self):
		self.failIf(self.dom.pd.cmdline)

	def test_initrd(self):
		self.failIf(self.dom.pd.initrd)

	def test_boot(self):
		self.assertEqual(['hd'], self.dom.pd.boot)


class TestDomainXenPVDirect(_Domain):

	"""
	<domain type="xen">
		<name>ucs401</name>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<os>
			<type>linux</type>
			<kernel>kernel</kernel>
			<initrd>initrd</initrd>
			<cmdline>root=UUID=... ro root2fstype=ext3 nosplash verbose console=xvc0</cmdline>
		</os>
		<devices>
			<emulator>/usr/lib64/xen/bin/qemu-dm</emulator>
			<disk type='file' device='disk'>
				<driver type='file'/>
				<target dev='xvda'/>
			</disk>
		</devices>
	</domain>
	"""

	def test_domain_type(self):
		self.assertEqual('xen', self.dom.pd.domain_type)

	def test_os_type(self):
		self.assertEqual('linux', self.dom.pd.os_type)

	def test_arch(self):
		self.assertEqual(self.default.arch, self.dom.pd.arch)

	def test_kernel(self):
		self.assertEqual('kernel', self.dom.pd.kernel)

	def test_initrd(self):
		self.assertEqual('initrd', self.dom.pd.initrd)

	def test_cmdline(self):
		self.assertEqual('root=UUID=... ro root2fstype=ext3 nosplash verbose console=xvc0', self.dom.pd.cmdline)

	def test_boot(self):
		self.failIf(self.dom.pd.boot)


class TestDomainXenPVGrub(_Domain):

	"""
	<domain type="xen">
		<name>ucs401</name>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<bootloader>/usr/bin/pygrub</bootloader>
		<bootloader_args>-q --args="console=hvc0 loglevel=7"</bootloader_args>
		<os>
			<type>linux</type>
		</os>
		<devices>
			<emulator>/usr/lib64/xen/bin/qemu-dm</emulator>
			<disk type='file' device='disk'>
				<driver type='file'/>
				<target dev='xvda'/>
			</disk>
			<interface type='bridge'>
				<mac address='00:16:3e:06:6a:b6'/>
				<source bridge='eth0'/>
				<target dev='internal0'/>
				<script path='vif-bridge'/>
				<model type='netfront'/>
			</interface>
		</devices>
	</domain>
	"""

	def test_domain_type(self):
		self.assertEqual('xen', self.dom.pd.domain_type)

	def test_os_type(self):
		self.assertEqual('linux', self.dom.pd.os_type)

	def test_arch(self):
		self.assertEqual(self.default.arch, self.dom.pd.arch)

	def test_kernel(self):
		self.failIf(self.dom.pd.kernel)

	def test_initrd(self):
		self.failIf(self.dom.pd.initrd)

	def test_cmdline(self):
		self.failIf(self.dom.pd.cmdline)

	def test_boot(self):
		self.failIf(self.dom.pd.boot)

	def test_bootloader(self):
		self.assertEqual('/usr/bin/pygrub', self.dom.pd.bootloader)

	def test_bootloader_args(self):
		self.assertEqual('-q --args="console=hvc0 loglevel=7"', self.dom.pd.bootloader_args)

	def test_interface0(self):
		i = self.dom.pd.interfaces[0]
		self.assertEqual('bridge', i.type)
		self.assertEqual('00:16:3e:06:6a:b6', i.mac_address)
		self.assertEqual('eth0', i.source)
		self.assertEqual('vif-bridge', i.script)
		self.assertEqual('internal0', i.target)
		self.assertEqual('netfront', i.model)


class TestDomainVNC(_Domain):

	"""
	<domain type='kvm'>
		<name>ucs401</name>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<memory unit='KiB'>1048576</memory>
		<currentMemory unit='KiB'>1048576</currentMemory>
		<vcpu placement='static'>1</vcpu>
		<os>
			<type arch='x86_64' machine='pc-1.1'>hvm</type>
		</os>
		<features>
			<acpi/>
			<apic/>
		</features>
		<clock offset='utc'/>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
			<input type='tablet' bus='usb'/>
			<input type='mouse' bus='ps2'/>
			<input type='keyboard' bus='ps2'/>
			<graphics type='vnc' port='7900' autoport='no'/>
			<video>
				<model type='cirrus' vram='9216' heads='1'/>
			</video>
		</devices>
	</domain>
	"""

	def test_graphics0(self):
		g = self.dom.pd.graphics[0]
		self.assertEqual('vnc', g.type)
		self.assertEqual(7900, g.port)
		self.assertFalse(g.autoport)
		self.failIf(g.listen)
		self.failIf(g.passwd)
		self.assertEqual('de', g.keymap)


if __name__ == '__main__':
	main()
