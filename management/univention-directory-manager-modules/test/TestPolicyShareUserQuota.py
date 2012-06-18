# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/share_userquota tests
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


class PolicyShareUserQuotaTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/share_userquota'
		super(PolicyShareUserQuotaTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyShareUserQuotaTestCase, self).setUp()
		self.createProperties = {
			'softLimitSpace': '100',
			'hardLimitSpace': '200',
			'softLimitInodes': '30',
			'hardLimitInodes': '40',
			}
		self.modifyProperties = {
			'softLimitSpace': '200',
			'hardLimitSpace': '300',
			'softLimitInodes': '40',
			'hardLimitInodes': '50',
			}
		self.name = 'testshareuserquotapolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyShareUserQuotaTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
