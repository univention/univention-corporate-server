# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dns/alias tests
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
