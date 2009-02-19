# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/sambaconfig tests
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


class SettingsSambaConfigTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/sambaconfig'
		super(SettingsSambaConfigTestCase,
		      self).__init__(*args, **kwargs)

	# NOTE: `logonToChangePW' is unchecked due to Bug #7765
	def setUp(self):
		super(SettingsSambaConfigTestCase, self).setUp()
		self.uncheckedProperties.add('logonToChangePW')
		self.createProperties = {
			'passwordLength':        '9',
			'passwordHistory':       '3',
			'minPasswordAge':        '50',
			'maxPasswordAge':        '60',
			'badLockoutAttempts':    '5',
			'lockoutDuration':       '33',
			'resetCountMinutes':     '22',
			'logonToChangePW':       '1',
			'disconnectTime':        '24',
			'refuseMachinePWChange': '0',
			}
		self.modifyProperties = {
			'passwordLength':        '10',
			'passwordHistory':       '4',
			'minPasswordAge':        '51',
			'maxPasswordAge':        '61',
			'badLockoutAttempts':    '6',
			'lockoutDuration':       '34',
			'resetCountMinutes':     '23',
			'logonToChangePW':       '0',
			'disconnectTime':        '25',
			'refuseMachinePWChange': '1',
			}
		self.name = 'testsambaconfigsetting'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsSambaConfigTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
