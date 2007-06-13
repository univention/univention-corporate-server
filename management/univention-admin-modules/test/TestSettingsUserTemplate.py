# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/usertemplate tests
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
