# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/print_quota tests
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


from GenericTest import GenericTestCase, PropertyInvalidError


class PolicyPrintQuotaTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/print_quota'
		super(PolicyPrintQuotaTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyPrintQuotaTestCase, self).setUp()
		self.createProperties = {
			'quotaUsers': '5 4 Administrator',
			'quotaGroups': '6 7 Administrators',
			'quotaGroupsPerUsers': '9 10 Administrators',
			}
		self.modifyProperties = {
			'quotaUsers': '50 40 Administrator',
			'quotaGroups': '60 70 Administrators',
			'quotaGroupsPerUsers': '90 100 Administrators',
			}
		self.name = 'testprintquotapolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyPrintQuotaTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
