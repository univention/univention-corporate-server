# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: groups/group tests
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


from GenericTest import GenericTestCase, TestError
from TestUsers import UserBaseCase


class GroupBaseCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'groups/group'
		super(GroupBaseCase, self).__init__(*args, **kwargs)

	def __checkProcess(self, proc, name, action):
		msg = 'Failed to %s user %s' % (action, name)
		proc.check(msg, self)

	def __createUser(self, name):
		user = UserBaseCase()
		user.name = name
		user.dn = self.rdn('uid=%s' % name)
		props = {
			'username': name,
			'unixhome': '/home/%s' % name,
			'lastname': name.capitalize(),
			'password': self.random(8),
		}
		proc = user.create(props)
		self.__checkProcess(proc, name, 'create')
		return user

	def __createUsers(self):
		self.__users = []
		prefix = self.random(3)
		names = [('test%s%s' % (prefix, num)) for num in range(1, 4)]
		for name in names:
			self.__users.append(self.__createUser(name))

	def __removeUser(self, user):
		proc = user.remove(dn = user.dn)
		self.__checkProcess(proc, user.name, 'remove')

	def __removeUsers(self):
		for user in self.__users:
			self.__removeUser(user)

	def setUp(self):
		super(GroupBaseCase, self).setUp()
		self.__createUsers()
		dns = [user.dn for user in self.__users]
		self.createProperties = {
			'description':	  'some test group',
			#'mailAddress':	  'testgroup@testdomain',
			'sambaGroupType': '2',
			'sambaRID':	  '11',
			'users':	  {'append': dns[:2]},
			}
		self.modifyProperties = {
			'description':	  'Some Tested Group',
			#'mailAddress':	  'testedgroup@testeddomain',
			'sambaGroupType': '3',
			'users':	  {'append': dns[2:],
					   'remove': dns[:1]}
			}

	def __testGroupnameLock(self):
		proc = self.create({}, name = self.name)
		self.assertRaises(TestError, proc.check)

	def __testGidnumberLock(self, dn):
		attrs = self.ldap.get(dn = self.dn, attr = ['gidNumber'])
		if not 'gidNumber' in attrs:
			return
		props = {
			'gidNumber': attrs['gidNumber'][0],
			}
		proc = self.create(props, name = 'shmoogroup')
		self.assertRaises(TestError, proc.check)

	def hookAfterCreated(self, dn):
		super(GroupBaseCase, self).hookAfterCreated(dn)
		self.__testGroupnameLock()
		self.__testGidnumberLock(dn)

	def tearDown(self):
		super(GroupBaseCase, self).tearDown()
		self.__removeUsers()


class GroupTestCase(GroupBaseCase):
	def setUp(self):
		super(GroupTestCase, self).setUp()
		self.name = 'testgroup'

class SingleLetterGroupTestCase(GroupBaseCase):
	def setUp(self):
		super(SingleLetterGroupTestCase, self).setUp()
		self.name = 't'

	def shortDescription(self):
		desc = super(SingleLetterGroupTestCase, self).shortDescription()
		return '%s(single letter name)' % desc


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(GroupTestCase())
	suite.addTest(SingleLetterGroupTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
