# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/host tests
#
# Copyright (C) 2004-2009 Univention GmbH
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


class DhcpHostTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dhcp/host'
		super(DhcpHostTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __createService(self):
		service = DhcpServiceTestCase()
		service.setUp()
		service.name += self.random()
		proc = service.create(service.createProperties)
		self.__checkProcess(proc, service, 'create')
		service.testObjectExists()
		self.__service = service

	def __removeService(self):
		proc = self.__service.remove(dn = self.__service.dn)
		self.__checkProcess(proc, self.__service, 'remove')
		self.__service.tearDown()

	def setUp(self):
		super(DhcpHostTestCase, self).setUp()
		self.__createService()
		ips = ['19.168.1.2', '19.168.1.3', '19.168.1.1']
		self.superordinate(self.__service)
		self.createProperties = {
			'hwaddress': 'ethernet 55:44:33:22:11:00',
			'fixedaddress': {'append': ips[:2]},
			}
		self.modifyProperties = {
			'hwaddress': 'ethernet 55:44:33:22:11:01',
			'fixedaddress': {'append': ips[2:],
					 'remove': ips[:1]},
			}
		self.name = 'testdhcphost'

	def tearDown(self):
		super(DhcpHostTestCase, self).tearDown()
		self.__removeService()


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DhcpHostTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
