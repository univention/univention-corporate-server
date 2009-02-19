# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/admin_container tests
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


class PolicyPackagesBaseCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/%spackages' % self.type
		super(PolicyPackagesBaseCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyPackagesBaseCase, self).setUp()
		self.createProperties = {
			'%sPackages' % self.type: 'this',
			'%sPackagesRemove' % self.type: 'that',
			}
		self.modifyProperties = {
			'%sPackages' % self.type: 'these',
			'%sPackagesRemove' % self.type: 'those',
			}
		self.name = 'test%spackagespolicy' % self.type


class PolicyMasterPackagesTestCase(PolicyPackagesBaseCase):
	def __init__(self, *args, **kwargs):
		self.type = 'master'
		super(PolicyMasterPackagesTestCase,
		      self).__init__(*args, **kwargs)

class PolicySlavePackagesTestCase(PolicyPackagesBaseCase):
	def __init__(self, *args, **kwargs):
		self.type = 'slave'
		super(PolicySlavePackagesTestCase,
		      self).__init__(*args, **kwargs)

class PolicyMemberPackagesTestCase(PolicyPackagesBaseCase):
	def __init__(self, *args, **kwargs):
		self.type = 'member'
		super(PolicyMemberPackagesTestCase,
		      self).__init__(*args, **kwargs)

class PolicyManagedClientPackagesTestCase(PolicyPackagesBaseCase):
	def __init__(self, *args, **kwargs):
		self.type = 'managedclient'
		super(PolicyManagedClientPackagesTestCase,
		      self).__init__(*args, **kwargs)
		self.type = 'client'

class PolicyMobileClientPackagesTestCase(PolicyPackagesBaseCase):
	def __init__(self, *args, **kwargs):
		self.type = 'mobileclient'
		super(PolicyMobileClientPackagesTestCase,
		      self).__init__(*args, **kwargs)
		self.type = 'client'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyMasterPackagesTestCase())
	suite.addTest(PolicySlavePackagesTestCase())
	suite.addTest(PolicyMemberPackagesTestCase())
	suite.addTest(PolicyManagedClientPackagesTestCase())
	suite.addTest(PolicyMobileClientPackagesTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
