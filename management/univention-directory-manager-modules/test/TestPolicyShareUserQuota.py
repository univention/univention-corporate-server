# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/share_userquota tests
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
