# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dns/alias tests
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
from TestDnsForwardZone import DnsForwardZoneTestCase


class DnsAliasTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dns/alias'
		super(DnsAliasTestCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, thing, action):
		msg = 'Failed to %s %s %s' % (action, thing.modname, thing.name)
		proc.check(msg, self)

	def __createZone(self):
		zone = DnsForwardZoneTestCase()
		zone.setUp()
		zone.name += self.random()
		proc = zone.create(zone.createProperties)
		self.__checkProcess(proc, zone, 'create')
		zone.testObjectExists()
		self.__zone = zone

	def __removeZone(self):
		proc = self.__zone.remove(dn = self.__zone.dn)
		self.__checkProcess(proc, self.__zone, 'remove')
		self.__zone.tearDown()

	def setUp(self):
		super(DnsAliasTestCase, self).setUp()
		self.__createZone()
		self.superordinate(self.__zone)
		self.createProperties = {
			'cname': 'betumen',
			'zonettl': '5',
			}
		self.modifyProperties = {
			'cname': 'mojave',
			'zonettl': '77',
			}
		self.name = 'testdnsalias'

	def tearDown(self):
		super(DnsAliasTestCase, self).tearDown()
		self.__removeZone()


def suite():
	import unittest
	suite = unittest.TestSuite()
	# NOTE: disabled due to Bug #7813
	#suite.addTest(DnsAliasTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
