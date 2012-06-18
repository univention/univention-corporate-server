# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/repositorysync tests
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


class PolicyRepositorySyncTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/repositorysync'
		super(PolicyRepositorySyncTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyRepositorySyncTestCase, self).setUp()
		months = ['June', 'February', 'March']
		weekdays = ['Tuesday', 'Thursday', 'Friday']
		days = ['2', '5', '6']
		hours = ['6', '7', '8']
		minutes = ['5', '10', '15']
		self.createProperties = {
			'month': {'append': months[:2]},
			'weekday': {'append': weekdays[:2]},
			'day': {'append': days[:2]},
			'hour': {'append': hours[:2]},
			'minute': {'append': minutes[:2]},
			}
		self.modifyProperties = {
			'month': {'append': months[2:],
				  'remove': months[:1]},
			'weekday': {'append': weekdays[2:],
				    'remove': weekdays[:1]},
			'day': {'append': days[2:],
				'remove': days[:1]},
			'hour': {'append': hours[2:],
				 'remove': hours[:1]},
			'minute': {'append': minutes[2:],
				   'remove': minutes[:1]},
			}
		self.name = 'testrepositorysyncpolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyRepositorySyncTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
