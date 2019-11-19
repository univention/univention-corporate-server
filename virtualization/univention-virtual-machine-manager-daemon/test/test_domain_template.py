#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""Test univention.uvmm.node.DomainTemplate"""
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
from univention.uvmm.node import DomainTemplate  # noqa: F402


class _DomainTemplate(TestCase):

	def setUp(self):
		xml = dedent(self.__doc__)
		self.kvm = DomainTemplate.list_from_xml(xml)


class TestDomainTemplateKVM(_DomainTemplate):

	"""
	<capabilities>
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
	</capabilities>
	"""

	def test_len(self):
		self.assertEqual(3, len(self.kvm))

	def test_os_type(self):
		t = self.kvm[0]
		self.assertEqual('hvm', t.os_type)

	def test_arch(self):
		t = self.kvm[0]
		self.assertEqual('i686', t.arch)

	def test_domain_type(self):
		t = self.kvm[0]
		self.assertEqual('qemu', t.domain_type)

	def test_emulator(self):
		t = self.kvm[0]
		self.assertEqual('/usr/bin/qemu', t.emulator)

	def test_machines(self):
		t = self.kvm[0]
		self.assertEqual(['pc'], t.machines)

	def test_features(self):
		t = self.kvm[0]
		self.assertEqual(['pae', 'acpi', 'apic'], t.features)


if __name__ == '__main__':
	main()
