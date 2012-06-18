# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: shares/printer tests
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


class SharesPrinterTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'shares/printer'
		super(SharesPrinterTestCase, self).__init__(*args, **kwargs)

	def setUp(self):
		super(SharesPrinterTestCase, self).setUp()
		self.createProperties = {
			'description': 'some test printer',
			'location':    'somewhere',
			'model':       'clown 6.1',
			'uri':         '//host/printer',
			'spoolHost':   {'append': ['host1', 'host2']},
			}
		self.modifyProperties = {
			'description': 'Some Tested Printer',
			'location':    'Somewhere Else',
			'model':       'clown 6.2',
			'uri':         '//host/coffee',
			'spoolHost':   {'append': ['host3'],
					'remove': ['host1']},
			}
		self.name = 'testprinter'


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SharesPrinterTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
