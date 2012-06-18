# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dns/forward_zone tests
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


class DnsForwardZoneTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dns/forward_zone'
		super(DnsForwardZoneTestCase, self).__init__(*args, **kwargs)

	def setUp(self, subnet = None):
		super(DnsForwardZoneTestCase, self).setUp()
		if subnet is None:
			subnet = self.random(2)
		hosts = ['19.168.%s.201' % subnet,
			 '19.168.%s.202' % subnet,
			 '19.168.%s.203' % subnet]
		self.createProperties = {
			'position': self.rdn('cn=dns'),
			'refresh': '10',
			'zonettl': '10',
			'retry': '10',
			'ttl': '20',
			'contact': 'root@testzone.example.com',
			'expire': '12',
			'serial': '4',
			'nameserver': {'append': hosts[:2]},
			}
		self.modifyProperties = {
			'refresh': '11',
			'zonettl': '12',
			'retry': '13',
			'ttl': '14',
			'contact': 'toor@testzone.example.com',
			'expire': '15',
			'serial': '16',
			'nameserver': {'remove': hosts[:1],
				       'append': hosts[2:]},
			}
		self.name = 'testdnsforwardzone' + str(subnet)


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DnsForwardZoneTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
