# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/directory tests
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


class SettingsDirectoryTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/directory'
		super(SettingsDirectoryTestCase, self).__init__(*args, **kwargs)
		rdn = 'cn=default containers,cn=univention'
		self.container = self.rdn(rdn)
		base = self.bc('ldap/base')
		self.defaults = {
			'computers': {'append': [self.rdn('cn=computers')],
				      'remove': [base, self.rdn('cn=users')]},
			'dhcp':      {'append': [self.rdn('cn=dhcp')],
				      'remove': [base, self.rdn('cn=users')]},
			'dns':       {'append': [self.rdn('cn=dns')],
				      'remove': [base, self.rdn('cn=users')]},
			'groups':    {'append': [self.rdn('cn=groups')],
				      'remove': [base, self.rdn('cn=users')]},
			'license':   {'append': [self.rdn('cn=license')],
				      'remove': [base, self.rdn('cn=users')]},
			'shares':    {'append': [self.rdn('cn=shares')],
				      'remove': [base, self.rdn('cn=users')]},
			'printers':  {'append': [self.rdn('cn=printers')],
				      'remove': [base, self.rdn('cn=users')]},
			'users':     {'append': [self.rdn('cn=users')],
				      'remove': [base, self.rdn('cn=groups')]}
			}

	def setUp(self):
		super(SettingsDirectoryTestCase, self).setUp()
		base = self.bc('ldap/base')
		self.modifyProperties = {
			'computers': {'set': [base, self.rdn('cn=users')]},
			'dhcp':      {'set': [base, self.rdn('cn=users')]},
			'dns':       {'set': [base, self.rdn('cn=users')]},
			'groups':    {'set': [base, self.rdn('cn=users')]},
			'license':   {'set': [base, self.rdn('cn=users')]},
			'printers':  {'set': [base, self.rdn('cn=users')]},
			'shares':    {'set': [base, self.rdn('cn=users')]},
			'users':     {'set': [base, self.rdn('cn=groups')]},
			}
		self.__success = False

	def runTest(self):
		self.dn = self.container
		self.name = 'default containers'
		self.testModify()
		self.modifyProperties = self.defaults
		self.testModify()
		self.__success = True

	def tearDown(self):
		super(SettingsDirectoryTestCase, self).tearDown()
		if not self.__success:
			self.modify(self.defaults, self.dn)


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsDirectoryTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
