# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/default tests
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


class SettingsDefaultTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/default'
		super(SettingsDefaultTestCase, self).__init__(*args, **kwargs)
		self.container = self.rdn('cn=default,cn=univention')
		self.defaults = {
			'defaultGroup': \
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultComputerGroup': \
			self.rdn('cn=Windows Hosts,cn=groups'),
			'defaultDomainControllerGroup': \
			self.rdn('cn=DC Slave Hosts,cn=groups'),
			'defaultKdeProfiles': \
			{'append':
			 ['none',
			  '/usr/share/univention-kde-profiles/kde.lockeddown',
			  '/usr/share/univention-kde-profiles/kde.restricted'],
			 'remove':
			 ['moobaz', 'goobaz']},
			}

	def setUp(self):
		super(SettingsDefaultTestCase, self).setUp()
		self.modifyProperties = {
			'defaultGroup': \
			self.rdn('cn=Domain Admins,cn=groups'),
			'defaultComputerGroup': \
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultDomainControllerGroup': \
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultKdeProfiles': \
			{'append': ['moobaz', 'goobaz'],
			 'remove': []},
			}
		self.__success = False

	def runTest(self):
		self.dn = self.container
		self.name = 'default'
		self.testModify()
		self.modifyProperties = self.defaults
		self.testModify()
		self.__success = True

	def tearDown(self):
		super(SettingsDefaultTestCase, self).tearDown()
		if not self.__success:
			self.modify(self.defaults, self.dn)


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsDefaultTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
