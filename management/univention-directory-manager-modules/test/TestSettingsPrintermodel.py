# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/printermodel tests
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


class SettingsPrinterModelTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/printermodel'
		super(SettingsPrinterModelTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(SettingsPrinterModelTestCase, self).setUp()
		self.superordinate(self.rdn('cn=univention'))
		foo1 = '"fooprinter.ppd" "fooprinter 1 cups v2"'
		foo2 = '"fooprinter2.ppd" "fooprinter 2 cups v2"'
		foo3 = '"fooprinter3.ppd" "fooprinter 3 cups v2"'
		self.createProperties = {
			'printmodel': {'append': [foo1, foo2]},
			}
		self.modifyProperties = {
			'printmodel': {'append': [foo3], 'remove': [foo1]},
			}
		self.name = 'testprintermodels'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsPrinterModelTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
