# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: computers/windows tests
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
from TestNetworksNetwork import NetworksNetworkTestCase


class ComputersWindowsTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'computers/windows'
		super(ComputersWindowsTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __createNetworks(self):
		net = NetworksNetworkTestCase()
		net.setUp(11)
		net.name += '1'
		proc = net.create(net.createProperties)
		self.__checkProcess(proc, net, 'create')
		net.testObjectExists()
		self.__network1 = net
		net = NetworksNetworkTestCase()
		net.setUp(21)
		net.name += '2'
		proc = net.create(net.createProperties)
		self.__checkProcess(proc, net, 'create')
		net.testObjectExists()
		self.__network2 = net

	def __removeNetworks(self):
		proc = self.__network1.remove(dn = self.__network1.dn)
		self.__checkProcess(proc, self.__network1, 'remove')
		self.__network1.tearDown()
		proc = self.__network2.remove(dn = self.__network2.dn)
		self.__checkProcess(proc, self.__network2, 'remove')
		self.__network2.tearDown()

	def setUp(self):
		super(ComputersWindowsTestCase, self).setUp()
		self.__createNetworks()
		self.uncheckedProperties.add('password')
		# TODO: `password' isn't even in the list of properties...
		# TODO: After (successfully) removing the computer object, an
		# object is left under the (second) networks forward zone.
		# This leads to errors removing the forward zone.
		# The object is a mac-address lock BTW.
		self.createProperties = {
			'position': self.rdn('cn=computers'),
			'description': 'some test windows computer',
			#'password': 'foobarbaz',
			'mac': '00:12:25:34:44:32',
			#'network': self.__network1.dn,
			}
		self.modifyProperties = {
			'description': 'Some Tested Windows Computer',
			#'password': 'foobarbazi',
			'mac': '00:12:25:34:44:33',
			#'network': self.__network2.dn,
			}
		self.name = 'testcomputer'

	def tearDown(self):
		super(ComputersWindowsTestCase, self).tearDown()
		self.__removeNetworks()


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(ComputersWindowsTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
