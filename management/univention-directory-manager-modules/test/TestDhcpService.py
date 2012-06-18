# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: dhcp/service tests
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


class DhcpServiceTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'dhcp/service'
		super(DhcpServiceTestCase, self).__init__(*args, **kwargs)

	def setUp(self, subnet = None):
		super(DhcpServiceTestCase, self).setUp()
		if subnet is None:
			subnet = self.random(2)
		self.createProperties = {'position': self.rdn('cn=dhcp')}
		self.name = 'testdhcpservice%s' % subnet


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(DhcpServiceTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
