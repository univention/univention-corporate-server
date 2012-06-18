# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/subnet tests
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
