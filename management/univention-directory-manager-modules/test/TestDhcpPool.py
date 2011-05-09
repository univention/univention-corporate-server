# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/pool tests
#
# Copyright 2004-2011 Univention GmbH
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
from TestDhcpSubnet import DhcpSubnetTestCase


class DhcpPoolTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dhcp/pool'
		super(DhcpPoolTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __createSubnet(self):
		subnet = DhcpSubnetTestCase()
		subnet.setUp()
		proc = subnet.create(subnet.createProperties)
		self.__checkProcess(proc, subnet, 'create')
		subnet.testObjectExists()
		self.__subnet = subnet

	def __removeSubnet(self):
		proc = self.__subnet.remove(dn = self.__subnet.dn)
		self.__checkProcess(proc, self.__subnet, 'remove')
		self.__subnet.tearDown()

	def setUp(self):
		super(DhcpPoolTestCase, self).setUp()
		self.__createSubnet()
		ranges = [('19.168.0.%s' % num) for num in range(110, 113)]
		# NOTE: Checking the ip range fails due to Bug #7809
		self.uncheckedProperties.add('range')
		self.superordinate(self.__subnet)
		self.createProperties = {
			'all_clients': 'allow',
			'failover_peer': '19.168.0.99',
			'dynamic_bootp_clients': 'deny',
			'known_clients': 'allow',
			'unknown_clients': 'allow',
			'range': {'append': ranges[:2]},
			}
		self.modifyProperties = {
			'all_clients': 'deny',
			'failover_peer': '',
			'dynamic_bootp_clients': 'allow',
			'known_clients': 'deny',
			'unknown_clients': 'deny',
			'range': {'append': ranges[2:],
				  'remove': ranges[:1]},
			}
		self.name = 'testdhcppool'

	def tearDown(self):
		super(DhcpPoolTestCase, self).tearDown()
		self.__removeSubnet()


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DhcpPoolTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
