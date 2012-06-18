# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/host tests
#
# Copyright 2004-2012 Univention GmbH
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
