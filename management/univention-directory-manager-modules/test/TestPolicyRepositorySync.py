# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/repositorysync tests
#
# Copyright (C) 2004-2009 Univention GmbH
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
