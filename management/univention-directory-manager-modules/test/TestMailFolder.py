# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: mail/folder tests
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


class MailFolderTestCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'mail/folder'
		super(MailFolderTestCase, self).__init__(*args, **kwargs)
		self.identifier = 'name'

	def setUp(self):
		super(MailFolderTestCase, self).setUp()
		domain = self.bc('domainname')
		adminRead  = 'Administrator@%s read' % domain
		adminAll   = 'Administrator@%s all' % domain
		nobodyRead = 'nobody@%s read' % domain
		adminsAll = 'Domain Admins all'
		usersRead = 'Domain Users read'
		usersAll  = 'Domain Users all'
		self.createProperties = {
			'mailDomain':		domain,
			'kolabHomeServer':	'nohost.%s' % domain,
			'cyrus-userquota':	'2',
			'userNamespace':	'FALSE',
			'sharedFolderUserACL':  {'append':
						 [adminRead, nobodyRead]},
			'sharedFolderGroupACL': {'append':
						 [adminsAll, usersRead]},
			}
		self.modifyProperties = {
			'kolabHomeServer':	'onehost.%s' % domain,
			'cyrus-userquota':	'4',
			'sharedFolderUserACL':  {'append': [adminAll],
						 'remove': [adminRead]},
			'sharedFolderGroupACL': {'append': [usersAll],
						 'remove': [usersRead]},
			}
		self.name = 'testmailfolder'
		self.dn = self.rdn('cn=%s@%s' % (self.name, domain))


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(MailFolderTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
