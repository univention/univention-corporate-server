# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: policies/thinclient tests
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


class PolicyThinclientTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'policies/thinclient'
		super(PolicyThinclientTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(PolicyThinclientTestCase, self).setUp()
		windows = ['unsinkbar2', 'titanic', 'logotoroi']
		linux = ['none', 'mob', 'anyboo']
		files = ['goo', 'poo', 'pooly']
		auths = ['some', 'any', 'nogohali']
		self.createProperties = {
			'requiredObjectClasses': 'univentionHost',
			'prohibitedObjectClasses': 'posixAccount',
			'fixedAttributes': 'univentionWindowsDomain',
			'windowsDomain': 'loo',
			'windowsTerminalServer': {'append': windows[:2]},
			'linuxTerminalServer': {'append': linux[:2]},
			'fileServer': {'append': files[:2]},
			'authServer': {'append': auths[:2]},
			'position': self.rdn('cn=policies')
			}
		self.modifyProperties = {
			'requiredObjectClasses': 'posixAccount',
			'prohibitedObjectClasses': 'univentionHost',
			'fixedAttributes': 'univentionWindowsDomain',
			'windowsDomain': 'goo',
			'windowsTerminalServer': {'append': windows[2:],
						  'remove': windows[:1]},
			'linuxTerminalServer': {'append': linux[2:],
						'remove': linux[:1]},
			'fileServer': {'append': files[2:],
				       'remove': files[:1]},
			'authServer': {'append': auths[2:],
				       'remove': auths[:1]},
			}
		self.name = 'testthinclientpolicy'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(PolicyThinclientTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
