# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/sambadomain tests
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


class SettingsSambaDomainTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/sambadomain'
		super(SettingsSambaDomainTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(SettingsSambaDomainTestCase, self).setUp()
		self.createProperties = {
			'SID':          '2.3.4.5',
			'NextUserRid':  '114',
			'NextGroupRid': '215',
			'NextRid':      '316',
			}
		self.modifyProperties = {
			'NextUserRid':  '115',
			'NextGroupRid': '216',
			'NextRid':      '317',
			}
		self.name = 'testsambadomainsetting'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsSambaDomainTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
