# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/repositoryserver tests
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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


class PolicyRepositoryServerTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/repositoryserver'
		super(PolicyRepositoryServerTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyRepositoryServerTestCase, self).setUp()
		self.createProperties = {
			'repositoryServer': 'baba'
			}
		self.modifyProperties = {
			'repositoryServer': 'bubu'
			}
		self.name = 'testrepositoryserverpolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyRepositoryServerTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
