#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2003-2022 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
import unittest
import os

import univention.license as ul


class TestBasic(unittest.TestCase):
	def test_double_free(self):
		ul.free()
		ul.free()

	def test_getValues(self):
		"""
		Return value from globally selected licence.
		"""
		with self.assertRaises(KeyError):
			ul.getValue('doesNotExists')


@unittest.skipUnless(os.access('/etc/machine.secret', os.R_OK), 'Requires /etc/machine.secret')
class TestSelect(unittest.TestCase):
	def test_select(self):
		"""
		Select licence by LDAP search `(univentionLicenseModule=admin)`
		"""
		ret = ul.select('admin')
		self.assertEqual(ret, 0)
		ul.free()
		ul.free()

	def test_getValues(self):
		"""
		Return value from globally selected licence.
		"""
		ret = ul.select('admin')
		self.assertEqual(ret, 0)
		val = ul.getValue('univentionLicenseBaseDN')
		self.assertIsNotNone(val)
		ul.free()

	@unittest.skip('WIP')
	def test_selectDN(self):
		"""
		Select licence by LDAP DN.
		"""
		ret = ul.selectDN('cn=admin,cn=license,cn=univention,%s')
		self.assertEqual(ret, 0)
		ul.free()

	@unittest.skip('WIP')
	def test_check(self):
		"""
		Just check licence by LDAP DN. Returns bit-field:

		0b0001: Invalid signature
		0b0010: Invalid end date
		0b0100: Invalid base DN
		0b1000: Invalid search path
		"""
		ret = ul.check('cn=admin,cn=license,cn=univention,%s')
		self.assertEqual(ret, 0)
		ul.free()


if __name__ == '__main__':
	unittest.main()
