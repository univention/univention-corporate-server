#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2017 Univention GmbH
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
# vim: set fileencoding=utf-8 :
# pylint: disable=R0903,R0201
"""
Create installer VM programmatically.
"""

from os.path import (join, split, splitext, exists, extsep)
from sys import (exit, stderr)
import argparse
import json
import libvirt
import random
from lxml import etree
from lxml.builder import E
from logging import (getLogger, basicConfig, DEBUG)
from urlparse import urlparse

__all__ = ('VirtualMachine')

ENCODING = 'UTF-8'

VM_BRIDGE = "eth0"
for potential_vm_bridge in ["virbr0", "br0"]:
	if exists(join("/sys/class/net", potential_vm_bridge, "bridge")):
		VM_BRIDGE = potential_vm_bridge
		break
VM_VNC = "0.0.0.0"
UID = 2260  # FIXME: phahn
GID = 1009  # FIXME: Tech
POOL = '/var/lib/libvirt/images'
QEMU = '/usr/bin/kvm'
LOCAL = '127.0.0.1'  # TODO: IPv6


class VirtualMachine(object):

	def __init__(self, name, server, iso_image=None, disks=1, interfaces=1):
		self.__created = False
		self.name = name
		self.vnc_host = None
		self.server = server
		self.iso_image = iso_image
		self.disks = disks
		self.interfaces = interfaces

	def __enter__(self):
		self.create()
		return self

	def __exit__(self, etype, exc, etraceback):
		self.delete()

	def create(self):
		test_vm = VmCreator(['--name', self.name, '--server', self.server, '--ucs-iso', self.iso_image, '--interfaces', str(self.interfaces), '--disks', str(self.disks)])
		test_vm.create_vm_if_possible()
		self.__created = True
		with test_vm as created_test_vm:
			(host, port) = created_test_vm.get_vnc()
			self.vnc_host = '%s:%s' % (host, port - 5900)

	def delete(self):
		if not self.__created:
			return
		conn = libvirt.open('qemu+ssh://build@%s/system' % (self.server,))
		dom = conn.lookupByName(self.name)
		dom.destroy()
		dom.undefine()


class TestXml(object):
	pass


class TestVolume(TestXml):

	def __init__(self, fname):
		super(TestVolume, self).__init__()
		if fname.startswith('/'):
			self.pool_path = fname
		else:
			self.pool_dir = POOL
			self.fname = fname
			self.suffix = None

	def source_tree(self):
		raise NotImplementedError()

	@property
	def name(self):
		return '%s.%s' % (self.fname, self.suffix)

	@property
	def pool_path(self):
		return join(self.pool_dir, self.name)

	@pool_path.setter
	def pool_path(self, value):
		self.pool_dir, fname = split(value)
		self.fname, ext = splitext(fname)
		self.suffix = ext.lstrip(extsep)


class TestDisk(TestVolume):
	def __init__(self, fname, boot_order_index, capacity=14):
		super(TestDisk, self).__init__(fname)
		self.logger = getLogger('test.disk')
		self.capacity = capacity
		self.suffix = "qcow2"
		self.boot_order_index = boot_order_index

	def volume_tree(self):
		vol = E.volume(
			E.name(self.name),
			E.source_tree(),
			E.capacity("%d" % self.capacity, unit="GiB"),
			E.target(
				E.format(type="qcow2"),
				E.permissions(
					E.mode("%04o" % 0o660),
					E.owner("%d" % UID),
					E.group("%d" % GID),
				),
			),
		)
		return vol

	def volume_xml(self):
		text = etree.tostring(
			self.volume_tree(), encoding=ENCODING, method='xml',
			pretty_print=True
		)
		return text

	def source_tree(self):
		dev = E.disk(
			E.driver(name="qemu", type="qcow2", cache="unsafe"),
			E.source(file=self.pool_path),
			E.target(dev="vd" + chr(self.boot_order_index + 96), bus="virtio"),
			E.boot(order=str(self.boot_order_index)),
			# E.transient(),
			type="file", device="disk"
		)
		return dev


class TestIso(TestVolume):
	def __init__(self, fname, boot_order_index):
		super(TestIso, self).__init__(fname)
		self.logger = getLogger('test.cdrom')
		self.suffix = "iso"
		self.boot_order_index = boot_order_index

	def source_tree(self):
		dev = E.disk(
			E.driver(name="qemu", type="raw"),
			E.source(file=self.pool_path),
			E.target(dev="hda", bus="ide"),
			E.readonly(),
			E.boot(order=str(self.boot_order_index)),
			type="file", device="cdrom"
		)
		return dev


class TestInterface(TestXml):
	def __init__(self):
		super(TestInterface, self).__init__()
		self.mac = "52:54:00:%02x:%02x:%02x" % (
			random.randint(0, 255), random.randint(0, 255),
			random.randint(0, 255)
		)

	def source_tree(self):
		interface = E.interface(
			E.mac(address=self.mac),
			E.source(bridge=VM_BRIDGE),
			E.model(type="virtio"),
			type="bridge",
		)
		return interface


class TestDomain(TestXml):
	def __init__(self, iname):
		super(TestDomain, self).__init__()
		self.logger = getLogger('test.domain')
		self.iname = iname
		self.memory = 1024
		self.disks = []
		self.interfaces = []

	def add_disk(self, disk):
		self.disks.append(disk)

	def add_interface(self, interface):
		self.interfaces.append(interface)

	def domain_tree(self):
		dom = E.domain(
			E.name(self.iname),
			#E.uuid("%s" % ...),
			E.description("Automated installer test"),
			E.memory("%d" % self.memory, unit="MiB"),
			E.vcpu("1", placement="static"),
			E.os(
				E.type("hvm", arch="x86_64", machine="pc-1.1"),
			),
			self.features(),
			E.clock(offset="utc"),
			E.on_poweroff("destroy"),
			E.on_reboot("restart"),
			E.on_crash("destroy"),
			self.devices(),
			type="kvm"
		)
		return dom

	def features(self):
		features = E.features(
			E.acpi(),
			E.apic(),
		)
		return features

	def devices(self):
		devices = E.devices(
			E.emulator(QEMU),
			E.input(type="tablet", bus="usb"),
			E.input(type="mouse", bus="ps2"),
			self.graphics(),
			self.video(),
			E.memballoon(model="virtio"),
		)
		for disk in self.disks:
			devices.append(disk.source_tree())
		for interface in self.interfaces:
			devices.append(interface.source_tree())
		return devices

	def graphics(self):
		graphics = E.graphics(
			E.listen(type="address", address=VM_VNC),
			type="vnc", port="-1", autoport="yes", listen=VM_VNC, keymap="en-us")
		return graphics

	def video(self):
		video = E.video(
			E.model(type="cirrus", vram="%d" % (9 << 10,), heads="1"),
		)
		return video

	def domain_xml(self):
		text = etree.tostring(
			self.domain_tree(), encoding=ENCODING, method='xml',
			pretty_print=True
		)
		return text


class VmCreator(object):

	def __init__(self, args=None):
		self.logger = getLogger('test')
		self.args = self.parse_args(args)
		self.kvm_server = 'qemu+ssh://build@' + self.args.kvm_server + '/system'

		self.boot_order_index = 1

		self.conn = libvirt.open(self.kvm_server)
		self.domain_xml = None
		self.dom = None

	def parse_args(self, args):
		parser = argparse.ArgumentParser(description='Create a virtual machine on a kvm server.')
		parser.add_argument('--name', dest='vm_name', default='installer-target', help='The name of the virtual machine.')
		parser.add_argument('--server', dest='kvm_server', required=True, help='The fqdn of the kvm server.')
		parser.add_argument('--ucs-iso', dest='ucs_iso', required=True, help='Path to the ISO file of the UCS-DVD to create the virtual machine with, on the kvm server.')
		parser.add_argument('--interfaces', dest='interface_count', default=1, type=int, help='The amount of network interfaces the virtual machine should get.')
		parser.add_argument('--disks', dest='disk_count', default=1, type=int, help='The amount of hard disks the virtual machine should get.')
		parser.add_argument('--resultfile', dest='resultfile', type=argparse.FileType('w'), help='Store details about the created virtual machine as JSON in the given file.')
		return parser.parse_args(args)

	def create_vm_if_possible(self):
		try:
			self.dom = self.conn.lookupByName(self.args.vm_name)
			self.logger.critical("A VM with the name %s already exists! Exiting.", self.dom.name())
			exit(1)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN:
				self.logger.error('Failed libvirt: %s', ex)
				exit(1)
			self.logger.info("Creating new VM: %s", ex)
			self.create_domain()

	def create_domain(self):
		self.domain_xml = TestDomain(self.args.vm_name)
		for i in range(self.args.interface_count):
			self.add_interface()
		for i in range(self.args.disk_count):
			self.add_disk()
		self.add_cdrom()
		xml = self.domain_xml.domain_xml()
		self.dom = self.conn.defineXML(xml)

	def create_disk(self):
		vol = TestDisk(self.args.vm_name + str(self.boot_order_index), boot_order_index=self.boot_order_index)
		self.boot_order_index += 1
		try:
			pool = self.conn.storagePoolLookupByName('default')
			disk = pool.storageVolLookupByName(vol.name)
			self.logger.info("Deleting existing volume %s", disk)
			disk.delete(0)
		except libvirt.libvirtError as ex:
			if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
				self.logger.error('Failed libvirt: %s', ex)
				exit(1)
		self.logger.info("Creating new disk")
		xml = vol.volume_xml()
		disk = pool.createXML(xml, 0)
		vol.pool_path = disk.path()
		return vol

	def add_interface(self):
		self.domain_xml.add_interface(TestInterface())

	def add_disk(self):
		vol = self.create_disk()
		self.domain_xml.add_disk(vol)

	def add_cdrom(self):
		vol = TestIso(self.args.ucs_iso, boot_order_index=self.boot_order_index)
		self.boot_order_index += 1
		self.domain_xml.add_disk(vol)

	def __enter__(self):
		self.dom.createWithFlags()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		pass
		#self.dom.destroyFlags()

	def get_vnc(self):
		host = urlparse(self.kvm_server).hostname or LOCAL

		xml = self.dom.XMLDesc()
		root = etree.fromstring(xml)
		devices = root.find('devices')
		for graphics in devices.findall('graphics'):
			port = int(graphics.attrib['port'])
			for listen in graphics.findall('listen'):
				if listen.attrib['type'] != 'address':
					continue
				addr = listen.attrib['address']
				if addr == '0.0.0.0' or (addr == LOCAL and host == LOCAL):
					return (host, port)


def main():
	basicConfig(stream=stderr, level=DEBUG)
	test_vm = VmCreator()
	test_vm.create_vm_if_possible()
	with test_vm as created_test_vm:
		if created_test_vm.args.resultfile is not None:
			(host, port) = created_test_vm.get_vnc()
			vm_name = created_test_vm.args.vm_name
			results = [{
				'vnchost': host,
				'name': vm_name,
				'vncport': (port - 5900)
			}]
			with created_test_vm.args.resultfile as resultfile:
				json.dump(results, resultfile)


if __name__ == '__main__':
	main()
