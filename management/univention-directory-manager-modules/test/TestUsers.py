# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: users/user tests
#
# Copyright 2004-2011 Univention GmbH
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

import univention.admin.uexceptions as uex
import univention.admin.uldap       as uldap


class GroupMembershipError(TestError):
	def __init__(self, test, group):
		e1 = 'User %s at DN %s (module %s)' \
		     % (test.name, test.dn, test.modname)
		e2 = ' not registered as a member of group %s' % group
		error = e1 + e2
		TestError.__init__(self, error, test)

class AccountEnabledError(TestError):
	def __init__(self, test, type):
		e1 = 'User %s at DN %s (module %s)' \
		     % (test.name, test.dn, test.modname)
		e2 = ': %s account not disabled' % type.upper()
		error = e1 + e2
		TestError.__init__(self, error, test)


class UserBaseCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'users/user'
		super(UserBaseCase, self).__init__(*args, **kwargs)
		self.__options = ('kerberos', 'mail', 'person', 'posix', 'samba')
		self.kerberos = False
		self.mail = False
		self.person = False
		self.posix = False
		self.samba = False

	def __setCreateProps(self):
		propsAdd = {
			'position': self.rdn('cn=users'),
			'username': 'foobar',
			'lastname': 'Bar',
			'password': self.random(8),
			'description': 'some test user',
			}
		propsAddKerberos = {}
		propsAddMail = {
			'mailPrimaryAddress': 'foobar@example.com',
			'mailGlobalSpamFolder': '1',
			'mailAlternativeAddress': 'barfooz@example.com',
			}
		propsAddPerson = {
			'title': 'Dr.',
			'firstname': 'Foo',
			'organisation': 'Univention',
			'street': 'Herrstr. 5',
			'postcode': '28355',
			'city': 'Bremen',
			'roomNumber': '345',
			'employeeNumber': '13',
			'employeeType': 'paperboy',
			'e-mail': {'append': ['foobar@example.com',
					      'foobar@%s' \
					      % self.bc('domainname')]},
			'phone': {'append': ['(+44)421-3424324322',
					     '2421/3424324322']},
			'mobileTelephoneNumber': {'append': ['007',
							     '207']},
			'pagerTelephoneNumber':  {'append': ['008',
							     '208']},
			'homeTelephoneNumber':   {'append': ['009',
							     '209']},
			'homePostalAddress':     {'append': ['somewhere',
							     'somewhere2']},
			'secretary': self.rdn('uid=Administrator,cn=users'),
			}
		propsAddPosix = {
			'unixhome': '/home/foobar',
			'shell': '/bin/ksh',
			'primaryGroup': self.__groups[0],
			'groups': {'set': self.__groups[1:-1]},
			}
		propsAddSamba = {
			'sambahome': '//Master/home',
			'scriptpath': 'Master/script',
			'homedrive': 'Master/foo',
			'profilepath': '//Master/foobar',
			'sambaLogonHours': '011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111',
			}
		propsAddPSK = {
			'userexpiry': '22.02.15',
			'disabled': '1',
			}
		if self.kerberos:
			propsAdd.update(propsAddKerberos)
		if self.mail:
			propsAdd.update(propsAddMail)
		if self.person:
			propsAdd.update(propsAddPerson)
		if self.posix:
			propsAdd.update(propsAddPosix)
		if self.samba:
			propsAdd.update(propsAddSamba)
		if self.posix or self.samba or self.kerberos:
			propsAdd.update(propsAddPSK)
		self.createProperties = propsAdd

	def __setModifyProps(self):
		propsMod = {
			'lastname': 'Baz',
			'password': self.random(8),
			'description': 'Some Tested User',
			}
		propsModKerberos = {}
		propsModMail = {
			'mailPrimaryAddress': 'foo_bar@example.com',
			'mailGlobalSpamFolder': '0',
			'mailAlternativeAddress': {'set':
						   ['bar_fooz@example.com']},
			}
		propsModPerson = {
			'title': 'Mooh',
			'firstname': 'Mooh',
			'organisation': 'Kuhnivention',
			'street': 'Muhhstr. 5',
			'postcode': '55555',
			'city': 'Kuheim',
			'roomNumber': '543',
			'employeeNumber': '14',
			'employeeType': 'milkman',
			'e-mail': {'append': ['mooh@%s' \
					      % self.bc('domainname')],
				   'remove': ['foobar@%s' \
					      % self.bc('domainname')]},
			'phone': {'append': ['05555555555',],
				  'remove': ['(+44)421-3424324322',]},
			'mobileTelephoneNumber': {'append': ['008'],
						  'remove': ['007']},
			'pagerTelephoneNumber':  {'append': ['009'],
						  'remove': ['008']},
			'homeTelephoneNumber':   {'append': ['010'],
						  'remove': ['009']},
			'homePostalAddress':     {'append': ['somewhere3'],
						  'remove': ['somewhere']},
			'secretary': self.rdn('uid=foobar,cn=users'),
			}
		propsModPosix = {
			'unixhome': '/home/foobari',
			'shell': '/bin/kshi',
			'primaryGroup': self.__groups[0],
			'groups': {'set': self.__groups[3:]},
			}
		propsModSamba = {
			'sambahome': '//Master/homies',
			'scriptpath': 'Master/scripties',
			'homedrive': 'Master/fooies',
			'profilepath': '//Master/foobaries',
			'sambaLogonHours': '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111',
			}
		propsModPSK = {
			'userexpiry': '23.03.15',
			}
		self.modifyProperties = propsMod
		if self.kerberos:
			propsMod.update(propsModKerberos)
		if self.mail:
			propsMod.update(propsModMail)
		if self.person:
			propsMod.update(propsModPerson)
		if self.posix:
			propsMod.update(propsModPosix)
		if self.samba:
			propsMod.update(propsModSamba)
		if self.posix or self.samba or self.kerberos:
			propsMod.update(propsModPSK)
		self.modifyProperties = propsMod

	def setUp(self):
		super(UserBaseCase, self).setUp()
		self.name = 'foobar'
		self.uncheckedProperties.add('password')
		self.__groups = [self.rdn('cn=Domain Guests,cn=groups'),
				 self.rdn('cn=Domain Users,cn=groups'),
				 self.rdn('cn=Domain Admins,cn=groups'),
				 self.rdn('cn=Users,cn=groups')]
		self.__setCreateProps()
		self.__setModifyProps()
		for o in self.__options:
			if getattr(self, o):
				self.createOptions.add(o)
		self.dn = 'uid=%s,%s' \
			  % (self.name, self.createProperties['position'])

	def __testGroupMember(self, group):
		if not self.posix:
			return
		attrs = self.ldap.get(dn = group, attr = ['uniqueMember'])
		if not ('uniqueMember' in attrs and
			self.dn in attrs['uniqueMember']):
			raise GroupMembershipError(self, group)

	def __testPosixDisabled(self, passwd):
		if not self.posix:
			return
		try:
			master = self.bc('ldap/master')
			ldap = uldap.access(binddn = self.dn, bindpw = passwd,
					    host = master, base = self.dn)
			raise AccountEnabledError(self, 'posix')
		except uex.authFail:
			pass

	def __testSambaDisabled(self):
		if not self.samba:
			return
		attrs = self.ldap.get(dn = self.dn, attr = ['sambaAcctFlags'])
		if not attrs['sambaAcctFlags']:
			return
		if not 'D' in attrs['sambaAcctFlags'][0]:
			raise AccountEnabledError(self, 'samba')

	def __testUsernameLock(self):
		props = {
			'username': self.name,
			'lastname': 'Bar',
			'password': 'barfoobaz',
			'description': 'testuser',
			}
		proc = self.create(props)
		self.assertRaises(TestError, proc.check)

	def __testUidnumberLock(self, dn):
		attrs = self.ldap.get(dn = self.dn, attr = ['uidNumber'])
		if not 'uidNumber' in attrs:
			return
		props = {
			'uidNumber': attrs['uidNumber'][0],
			'username': 'moobar',
			'lastname': 'Bar',
			'password': 'barfoobaz',
			'description': 'testuser',
			}
		proc = self.create(props)
		self.assertRaises(TestError, proc.check)

	def hookAfterCreated(self, dn):
		super(UserBaseCase, self).hookAfterCreated(dn)
		self.__testPosixDisabled(self.createProperties['password'])
		self.__testSambaDisabled()
		for group in self.__groups[0:3]:
			self.__testGroupMember(group)
		self.__testUsernameLock()
		self.__testUidnumberLock(dn)

	def hookAfterModified(self, dn):
		super(UserBaseCase, self).hookAfterModified(dn)
		self.__testPosixDisabled(self.modifyProperties['password'])
		self.__testSambaDisabled()
		for group in [self.__groups[0], self.__groups[3]]:
			self.__testGroupMember(group)

	def tearDown(self):
		super(UserBaseCase, self).tearDown()
		pass

	def shortDescription(self):
		desc = super(UserBaseCase, self).shortDescription()
		opts = []
		for attr in ('kerberos', 'mail', 'person', 'posix', 'samba'):
			if getattr(self, attr):
				opts.append(attr.capitalize())
		return '%s(%s)' % (desc, ','.join(opts))


class UserFullTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserFullTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = True
		self.person = True
		self.posix = True
		self.samba = True

class UserNoKrbTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserNoKrbTestCase, self).__init__(*args, **kwargs)
		self.kerberos = False
		self.mail = True
		self.person = True
		self.posix = True
		self.samba = True

class UserNoMailTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserNoMailTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = False
		self.person = True
		self.posix = True
		self.samba = True

class UserNoPrsnTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserNoPrsnTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = True
		self.person = False
		self.posix = True
		self.samba = True

class UserNoPsxTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserNoPsxTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = True
		self.person = True
		self.posix = False
		self.samba = True

class UserNoSmbTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserNoSmbTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = True
		self.person = True
		self.posix = True
		self.samba = False

class UserKrbTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserKrbTestCase, self).__init__(*args, **kwargs)
		self.kerberos = True
		self.mail = False
		self.person = False
		self.posix = False
		self.samba = False

class UserMailTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserMailTestCase, self).__init__(*args, **kwargs)
		self.kerberos = False
		self.mail = True
		self.person = False
		self.posix = False
		self.samba = False

class UserPrsnTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserPrsnTestCase, self).__init__(*args, **kwargs)
		self.kerberos = False
		self.mail = False
		self.person = True
		self.posix = False
		self.samba = False

class UserPsxTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserPsxTestCase, self).__init__(*args, **kwargs)
		self.kerberos = False
		self.mail = False
		self.person = False
		self.posix = True
		self.samba = False

class UserSmbTestCase(UserBaseCase):
	def __init__(self, *args, **kwargs):
		super(UserSmbTestCase, self).__init__(*args, **kwargs)
		self.kerberos = False
		self.mail = False
		self.person = False
		self.posix = False
		self.samba = True

class UserMinimalTestCase(UserBaseCase):
	# All options are implicitly False anyway
	pass


def suite():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(UserFullTestCase())
	suite.addTest(UserMinimalTestCase())
	return suite

def extended():
	import unittest
	suite = unittest.TestSuite()
	suite.addTest(UserFullTestCase())
	suite.addTest(UserNoKrbTestCase())
	suite.addTest(UserNoMailTestCase())
	suite.addTest(UserNoPrsnTestCase())
	suite.addTest(UserNoPsxTestCase())
	suite.addTest(UserNoSmbTestCase())
	# NOTE: these are supposed to fail
	# User objects require one of the
	# person, posix or samba options
	#suite.addTest(UserKrbTestCase())
	#suite.addTest(UserMailTestCase())
	# NOTE: This fails due to Bug #7331
	#suite.addTest(UserPrsnTestCase())
	# NOTE: This fails due to Bug #7751
	#suite.addTest(UserPsxTestCase())
	suite.addTest(UserSmbTestCase())
	suite.addTest(UserMinimalTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
