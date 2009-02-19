# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: computers/trustaccount tests
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


from GenericTest import GenericTestCase, PropertyInvalidError

import os, random, string


class ComputerTrustAccountTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'computers/trustaccount'
		super(ComputerTrustAccountTestCase,
		      self).__init__(*args, **kwargs)

	def __checkPassword(self, dn, password):
		hashes = ['sambaNTPassword', 'sambaLMPassword']
		prop = 'password'
		attr = self.ldap.get(dn = dn, attr = hashes)
		try:
			pipe = os.popen('echo "%s" | univention-smbencrypt' \
					% password)
			lm1, nt1 = pipe.readline().strip().split(':')
			lm2 = attr['sambaLMPassword'][0]
			nt2 = attr['sambaNTPassword'][0]
		except:
			# An exception here means that
			# a) not all pwd attrs are stored in LDAP
			# b) the smbencrypt subprocess failed
			# I should raise an appropriate exception here.
			raise		# TODO
		if lm1 != lm2:
			raise PropertyInvalidError(self, dn, prop, lm1, lm2)
		if nt1 != nt2:
			raise PropertyInvalidError(self, dn, prop, nt1, nt2)

	def hookAfterCreated(self, dn):
		self.__checkPassword(dn, self.createProperties['password'])

	def hookAfterModified(self, dn):
		self.__checkPassword(dn, self.modifyProperties['password'])

	def setUp(self):
		super(ComputerTrustAccountTestCase, self).setUp()
		self.uncheckedProperties.add('password')
		self.createProperties = {
			'position': self.rdn('cn=computers'),
			'password': ''.join(random.sample(string.letters, 8)),
			}
		self.modifyProperties = {
			'password': ''.join(random.sample(string.letters, 8)),
			}
		self.name = 'testtrustaccount'


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(ComputerTrustAccountTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
