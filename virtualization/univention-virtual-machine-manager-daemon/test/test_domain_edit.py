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
import univention
from unittest import main, TestCase
from textwrap import dedent
from lxml.doctestcompare import LXMLOutputChecker
from doctest import Example

univention.__path__.append(join(dirname(__file__), '../src/univention'))  # type: ignore
from univention.uvmm.node import _domain_edit  # noqa: E402
from univention.uvmm.protocol import Data_Domain, Disk, Interface, Graphic  # noqa: E402


class _Template(object):

	def matches(self, stat):
		return True

	loader = None
	features = ('acpi', 'apic')
	emulator = '/usr/bin/kvm'


class _Domain(TestCase):

	def assertXmlEqual(self, want, got):
		checker = LXMLOutputChecker()
		if not checker.check_output(want, got, 0):
			message = checker.output_difference(Example("", want), got, 0)
			raise AssertionError(message)

	def setUp(self):
		self.xml = dedent(self.__doc__)
		self.domain = Data_Domain()

	@property
	def pd(self):  # Domain
		return self

	@property
	def capabilities(self):  # Domain_Data
		return (_Template(),)

	@property
	def libvirt_version(self):  # Node
		return (0, 9, 4)


class TestDomainDefault(_Domain):

	"""
	<domain type="kvm">
		<os>
			<type arch="i686">hvm</type>
		</os>
		<memory>0</memory>
		<vcpu>1</vcpu>
		<features>
			<acpi/>
			<apic/>
			<hyperv>
				<relaxed state="on"></relaxed>
				<vapic state="on"></vapic>
				<spinlocks retries="8191" state="on"></spinlocks>
			</hyperv>
		</features>
		<clock offset="utc">
			<timer name="rtc" present="yes" tickpolicy="catchup"></timer>
			<timer name="pit" present="yes" tickpolicy="delay"></timer>
			<timer name="hpet" present="no"></timer>
			<timer name="hypervclock" present="yes"></timer>
		</clock>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
			<input bus="usb" type="tablet"/>
		</devices>
	</domain>
	"""

	def test_default(self):
		self.domain = d = Data_Domain()
		xml, update_xml = _domain_edit(self, d, xml=None)
		self.assertXmlEqual(self.xml, xml)


class TestDomainBootloader(_Domain):

	"""
	<domain type="kvm">
		<os>
			<type arch="i686">hvm</type>
		</os>
		<bootloader>/usr/bin/pygrub</bootloader>
		<bootloader_args>-v</bootloader_args>
		<memory>0</memory>
		<vcpu>1</vcpu>
		<features>
			<acpi/>
			<apic/>
			<hyperv>
				<relaxed state="on"></relaxed>
				<vapic state="on"></vapic>
				<spinlocks retries="8191" state="on"></spinlocks>
			</hyperv>
		</features>
		<clock offset="utc">
			<timer name="rtc" present="yes" tickpolicy="catchup"></timer>
			<timer name="pit" present="yes" tickpolicy="delay"></timer>
			<timer name="hpet" present="no"></timer>
			<timer name="hypervclock" present="yes"></timer>
		</clock>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
			<input bus="usb" type="tablet"/>
		</devices>
	</domain>
	"""

	def test_edit_boot(self):
		self.domain = d = Data_Domain()
		d.bootloader = '/usr/bin/pygrub'
		d.bootloader_args = '-v'
		xml, update_xml = _domain_edit(self, d, xml=None)
		self.assertXmlEqual(self.xml, xml)


class TestDomainKVM(_Domain):

	"""
	<domain type='kvm'>
		<uuid>da33829a-4c56-4626-8d33-beec0580fc10</uuid>
		<name>ucs401</name>
		<description>https://forge.univention.org/bugzilla/show_bug.cgi?id=36640</description>
		<os>
			<type arch='x86_64'>hvm</type>
			<boot dev='cdrom'/>
			<boot dev='hd'/>
		</os>
		<memory>1048576</memory>
		<currentMemory>1048576</currentMemory>
		<vcpu>1</vcpu>
		<features>
			<acpi/>
			<apic/>
			<hyperv>
				<relaxed state="on"></relaxed>
				<vapic state="on"></vapic>
				<spinlocks retries="8191" state="on"></spinlocks>
			</hyperv>
		</features>
		<clock offset="utc">
			<timer name="rtc" present="yes" tickpolicy="catchup"></timer>
			<timer name="pit" present="yes" tickpolicy="delay"></timer>
			<timer name="hpet" present="no"></timer>
			<timer name="hypervclock" present="yes"></timer>
		</clock>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
			<disk type='file' device='disk'>
				<target dev='vda' bus='virtio'/>
				<driver name='qemu' type='qcow2' cache='none'/>
				<source file='/var/lib/libvirt/images/ucs401-0.qcow2'/>
			</disk>
			<disk type='file' device='cdrom'>
				<target dev='hda' bus='ide'/>
				<driver name='qemu' type='raw' cache='default'/>
				<source file='/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso'/>
				<readonly/>
			</disk>
			<interface type='bridge'>
				<mac address='52:54:00:71:90:4b'/>
				<source bridge='br0'/>
				<model type='virtio'/>
			</interface>
			<input type='tablet' bus='usb'/>
			<graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0' keymap='de'/>
		</devices>
	</domain>
	"""

	def test_edit(self):
		self.domain = d = Data_Domain()
		d.domain_type = 'kvm'
		d.uuid = 'da33829a-4c56-4626-8d33-beec0580fc10'
		d.name = 'ucs401'
		d.annotations = {'description': 'https://forge.univention.org/bugzilla/show_bug.cgi?id=36640'}
		d.os_type = 'hvm'
		d.arch = 'x86_64'
		d.boot = ['cdrom', 'hd']
		d.maxMem = 1048576 << 10  # KiB
		d.vcpus = 1
		d.rtc_offset = 'utc'

		disk = Disk()
		disk.type = Disk.TYPE_FILE
		disk.device = Disk.DEVICE_DISK
		disk.driver = 'qemu'
		disk.driver_type = 'qcow2'
		disk.driver_cache = 'none'
		disk.source = "/var/lib/libvirt/images/ucs401-0.qcow2"
		disk.target_dev = 'vda'
		disk.target_bus = 'virtio'
		d.disks.append(disk)

		disk = Disk()
		disk.type = Disk.TYPE_FILE
		disk.device = Disk.DEVICE_CDROM
		disk.driver = 'qemu'
		disk.driver_type = 'raw'
		disk.source = "/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso"
		disk.readonly = True
		disk.target_dev = 'hda'
		disk.target_bus = 'ide'
		d.disks.append(disk)

		interface = Interface()
		interface.type = Interface.TYPE_BRIDGE
		interface.mac_address = "52:54:00:71:90:4b"
		interface.source = 'br0'
		interface.model = 'virtio'
		d.interfaces.append(interface)

		graphic = Graphic()
		graphic.type = Graphic.TYPE_VNC
		graphic.listen = '0.0.0.0'
		d.graphics.append(graphic)

		xml, update_xml = _domain_edit(self, d, xml=None)
		self.assertXmlEqual(self.xml, xml)


class TestDomainNew(_Domain):

	"""
	<domain type='kvm'>
		<name>ucs401</name>
		<os>
			<type arch='i686'>hvm</type>
		</os>
		<memory>0</memory>
		<vcpu>1</vcpu>
		<features>
			<acpi/>
			<apic/>
			<hyperv>
				<relaxed state="on"></relaxed>
				<vapic state="on"></vapic>
				<spinlocks retries="8191" state="on"></spinlocks>
			</hyperv>
		</features>
		<clock offset="utc">
			<timer name="rtc" present="yes" tickpolicy="catchup"></timer>
			<timer name="pit" present="yes" tickpolicy="delay"></timer>
			<timer name="hpet" present="no"></timer>
			<timer name="hypervclock" present="yes"></timer>
		</clock>
		<on_poweroff>destroy</on_poweroff>
		<on_reboot>restart</on_reboot>
		<on_crash>destroy</on_crash>
		<devices>
			<emulator>/usr/bin/kvm</emulator>
			<disk type='file' device='disk'>
				<target bus="ide" dev="hda"/>
				<driver cache='default'/>
				<source file='/var/lib/libvirt/images/ucs401-0.qcow2'/>
			</disk>
			<disk type='file' device='cdrom'>
				<target bus="ide" dev="hdb"/>
				<driver cache='default'/>
				<source file='/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso'/>
				<readonly/>
			</disk>
			<interface type='bridge'>
				<mac/>
				<source/>
			</interface>
			<input type='tablet' bus='usb'/>
			<graphics type='vnc' port='-1' autoport='yes' keymap='de'/>
		</devices>
	</domain>
	"""

	def test_new(self):
		self.domain = d = Data_Domain()
		# d.domain_type = 'kvm'
		d.name = 'ucs401'
		# d.os_type = 'hvm'
		# d.arch = 'x86_64'
		# d.boot = ['cdrom', 'hd']
		# d.maxMem = 1048576 << 10  # KiB
		d.vcpus = 1
		# d.rtc_offset = 'utc'

		disk = Disk()
		disk.type = Disk.TYPE_FILE
		disk.device = Disk.DEVICE_DISK
		# disk.driver = 'qemu'
		# disk.driver_type = 'qcow2'
		# disk.driver_cache = 'none'
		disk.source = "/var/lib/libvirt/images/ucs401-0.qcow2"
		# disk.target_dev = 'vda'
		# disk.target_bus = 'virtio'
		d.disks.append(disk)

		disk = Disk()
		disk.type = Disk.TYPE_FILE
		disk.device = Disk.DEVICE_CDROM
		# disk.driver = 'qemu'
		# disk.driver_type = 'raw'
		disk.source = "/var/univention/buildsystem2/isotests/ucs_4.0-1-latest-amd64.iso"
		disk.readonly = True
		# disk.target_dev = 'hda'
		# disk.target_bus = 'ide'
		d.disks.append(disk)

		interface = Interface()
		interface.type = Interface.TYPE_BRIDGE
		# interface.source = 'br0'
		# interface.model = 'virtio'
		d.interfaces.append(interface)

		graphic = Graphic()
		graphic.type = Graphic.TYPE_VNC
		# graphic.listen = '0.0.0.0'
		d.graphics.append(graphic)

		xml, update_xml = _domain_edit(self, d, xml=None)
		self.assertXmlEqual(self.xml, xml)


if __name__ == '__main__':
	main()
