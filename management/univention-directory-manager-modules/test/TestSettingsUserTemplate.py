# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/usertemplate tests
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


class SettingsUserTemplateTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'settings/usertemplate'
		super(SettingsUserTemplateTestCase,
		      self).__init__(*args, **kwargs)

	def setUp(self):
		super(SettingsUserTemplateTestCase, self).setUp()
		self.name = 'testsettingsusertemplate'
		email = ['<username>@univention.de',
			 '<username>@example.com',
			 'master@<username>.example.com']
		self.createProperties = {
			'description':  'this is some user',
			'title':        'none',
			'organisation': 'univention',
			'sambahome':    '/smb/home/<username>',
			'scriptpath':   '/smb/scripts/<username>',
			'profilepath':  '/home/<username>/profile',
			'unixhome':     '/home/<username>',
			'shell':        '/bin/bash',
			'homedrive':    'I',
			'e-mail': {'append': email[:2]},
			}
		self.modifyProperties = {
			'description':  'this is some awesome user',
			'title':        'Master',
			'organisation': 'gummikraut',
			'sambahome':    '/home/<username>',
			'scriptpath':   '/home/smbscripts/<username>',
			'profilepath':  '/homedrive/home/<username>/profile',
			'unixhome':     '/homedrive/home/<username>',
			'shell':        '/bin/ksh',
			'homedrive':    'J',
			'e-mail': {'append': email[2:],
				   'remove': email[:1]},
			}
		


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsUserTemplateTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
