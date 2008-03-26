# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: networks/network tests
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from GenericTest import GenericTestCase
from TestDhcpService    import DhcpServiceTestCase
from TestDnsForwardZone import DnsForwardZoneTestCase
from TestDnsReverseZone import DnsReverseZoneTestCase


class NetworksNetworkTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'networks/network'
		super(NetworksNetworkTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __create(self, klass, subnet, suffix = ''):
		thing = klass()
		thing.setUp(subnet)
		thing.name += str(suffix)
		proc = thing.create(thing.createProperties)
		self.__checkProcess(proc, thing, 'create')
		thing.testObjectExists()
		return thing

	def __createObjects(self, subnet):
		self.__dhcp1 = self.__create(DhcpServiceTestCase, subnet, 1)
		self.__frwd1 = self.__create(DnsForwardZoneTestCase, subnet)
		self.__rvrs1 = self.__create(DnsReverseZoneTestCase, subnet)
		subnet = str(int(subnet) + 1)
		self.__dhcp2 = self.__create(DhcpServiceTestCase, subnet, 2)
		self.__frwd2 = self.__create(DnsForwardZoneTestCase, subnet)
		self.__rvrs2 = self.__create(DnsReverseZoneTestCase, subnet)

	def __removeObject(self, thing):
		proc = thing.remove(dn = thing.dn)
		self.__checkProcess(proc, thing, 'remove')
		thing.tearDown()

	def setUp(self, subnet = None):
		super(NetworksNetworkTestCase, self).setUp()
		if subnet is None:
			subnet = self.random(2)
		self.__createObjects(subnet)
		ranges = ['19.168.%s.32 19.168.%s.254' % (subnet, subnet),
			  '19.168.%s.30 19.168.%s.31'  % (subnet, subnet),
			  '19.168.%s.28 19.168.%s.29'  % (subnet, subnet),]
		# NOTE: Checking the ip range fails due to Bug #7809
		self.uncheckedProperties.add('ipRange')
		self.createProperties = {
			'network': '19.168.%s.0' % subnet,
			'netmask': '24',
			'ipRange': {'append': ranges[:2]},
			'dhcpEntryZone':       self.__dhcp1.dn,
			'dnsEntryZoneForward': self.__frwd1.dn,
			'dnsEntryZoneReverse': self.__rvrs1.dn,
			}
		self.modifyProperties = {
			'ipRange': {'remove': ranges[:1],
				    'append': ranges[2:]},
			'dhcpEntryZone':       self.__dhcp2.dn,
			'dnsEntryZoneForward': self.__frwd2.dn,
			'dnsEntryZoneReverse': self.__rvrs2.dn,
			}
		self.name = 'testnetwork'

	def tearDown(self):
		super(NetworksNetworkTestCase, self).tearDown()
		self.__removeObject(self.__dhcp1)
		self.__removeObject(self.__frwd1)
		self.__removeObject(self.__rvrs1)
		self.__removeObject(self.__dhcp2)
		self.__removeObject(self.__frwd2)
		self.__removeObject(self.__rvrs2)


def suite():
	import unittest
	suite = unittest.TestSuite()
	# NOTE: disabled due to Bug #7814.
	#suite.addTest(NetworksNetworkTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
