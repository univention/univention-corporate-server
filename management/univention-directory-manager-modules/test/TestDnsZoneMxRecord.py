# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dns/zone_mx_record tests
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


class DnsZoneMxRecordTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dns/zone_mx_record'
		super(DnsZoneMxRecordTestCase, self).__init__(*args, **kwargs)

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
		super(DnsZoneMxRecordTestCase, self).setUp()
		self.__createZone()
		self.superordinate(self.__zone)
		self.createProperties = {
			'mx': '4 winzigweich',
			}
		self.modifyProperties = {
			'mx': '10 univention',
			}
		self.dn = self.__zone.dn

	def hookAfterCreated(self, dn):
		self.arg(self.createProperties['mx'])

	def hookAfterModified(self, dn):
		self.arg(self.modifyProperties['mx'])

	# We cannot delete the record at the DN yet, so we can't check for
	# object non-existence by DN, so we need to override this method and
	# disable the check for object non-existence.
	def testRemove(self):
		proc = self.remove(dn = self.dn)
		self._checkProcess(proc, 'remove')
		self.hookAfterRemoved(self.dn)

	def tearDown(self):
		super(DnsZoneMxRecordTestCase, self).tearDown()
		self.__removeZone()


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DnsZoneMxRecordTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
