# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/dhcp_leasetime tests
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


class PolicyDhcpLeasetimeTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/dhcp_leasetime'
		super(PolicyDhcpLeasetimeTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyDhcpLeasetimeTestCase, self).setUp()
		self.createProperties = {
			'requiredObjectClasses': 'univentionHost',
			'prohibitedObjectClasses': 'posixAccount',
			'fixedAttributes': 'univentionDhcpLeaseTimeDefault',
			'lease_time_min': '5',
			'lease_time_max': '15',
			'lease_time_default': '10',
			}
		self.modifyProperties = {
			'requiredObjectClasses': 'posixAccount',
			'prohibitedObjectClasses': 'univentionHost',
			'fixedAttributes': 'univentionDhcpLeaseTimeMax',
			'lease_time_min': '15',
			'lease_time_max': '25',
			'lease_time_default': '20',
			}
		self.name = 'testdhcpleasetimepolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyDhcpLeasetimeTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
