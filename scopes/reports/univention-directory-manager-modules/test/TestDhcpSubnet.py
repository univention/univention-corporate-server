# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/subnet tests
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
from TestDhcpService import DhcpServiceTestCase


class DhcpSubnetTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dhcp/subnet'
		super(DhcpSubnetTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __createService(self, subnet):
		service = DhcpServiceTestCase()
		service.setUp(subnet)
		proc = service.create(service.createProperties)
		self.__checkProcess(proc, service, 'create')
		service.testObjectExists()
		self.__service = service

	def __removeService(self):
		proc = self.__service.remove(dn = self.__service.dn)
		self.__checkProcess(proc, self.__service, 'remove')
		self.__service.tearDown()

	def setUp(self, subnet = None):
		super(DhcpSubnetTestCase, self).setUp()
		if subnet is None:
			subnet = self.random(2)
		self.__createService(subnet)
		ranges = ['19.168.%s.100 19.168.%s.150' % (subnet, subnet),
			  '19.168.%s.151 19.168.%s.200' % (subnet, subnet),
			  '19.168.%s.100 19.168.%s.130' % (subnet, subnet)]
		# NOTE: Checking the ip range fails due to Bug #7809
		self.uncheckedProperties.add('range')
		# NOTE: subnetmask is given in the format used internally
		self.superordinate(self.__service)
		self.createProperties = {
			'subnetmask': '24',
			'range': {'append': ranges[:2]},
			}
		self.modifyProperties = {
			'subnetmask': '16',
			'range': {'append': ranges[2:],
				  'remove': ranges[:1]},
			}
		self.name = '19.168.%s.0' % subnet

	def tearDown(self):
		super(DhcpSubnetTestCase, self).tearDown()
		self.__removeService()


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DhcpSubnetTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
