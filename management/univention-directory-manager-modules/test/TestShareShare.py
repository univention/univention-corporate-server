# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: shares/share tests
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


class MissingObjectClassError(TestError):
	def __init__(self, test, dn, missing, classes):
		e1 = 'Object %s at DN %s (module %s)' \
		     % (test.name, dn, test.modname)
		e2 = ' is missing objectClass "univentionShare%s".' % missing
		e3 = ' Present objectClasses: "%s"' % classes
		error = e1 + e2 + e3
		TestError.__init__(self, error, test)

class ErroneousObjectClassError(TestError):
	def __init__(self, test, dn, present, classes):
		e1 = 'Object %s at DN %s (module %s)' \
		     % (test.name, dn, test.modname)
		e2 = ' is erroneously has objectClass "univentionShare%s".' \
		     % present
		e3 = ' Present objectClasses: "%s"' % classes
		error = e1 + e2 + e3
		TestError.__init__(self, error, test)

class SharesShareBaseCase(GenericTestCase):
	def __init__(self, *args, **kwargs):
		self.modname = 'shares/share'
		super(SharesShareBaseCase, self).__init__(*args, **kwargs)

	# Ensure that the present objectClasses match the desired share types.
	def hookAfterCreated(self, dn):
		attr = self.ldap.get(dn = dn, attr = ['objectClass'])
		nfs = bool('univentionShareNFS' in attr['objectClass'])
		smb = bool('univentionShareSamba' in attr['objectClass'])
		if nfs != self.nfs:
			args = (self, dn, attr['objectClass'], 'NFS')
			if nfs:
				raise ErroneousObjectClassError(*args)
			else:
				raise MissingObjectClassError(*args)
		if smb != self.smb:
			args = (self, dn, attr['objectClass'], 'Samba')
			if smb:
				raise ErroneousObjectClassError(*args)
			else:
				raise MissingObjectClassError(*args)

	def setUp(self):
		super(SharesShareBaseCase, self).setUp()
		propsAdd = {
			'host': self.bc('hostname'),
			'path': '/home/share',
			}
		propsAddNfs = {
			'writeable': '1',
			}
		propsAddSamba = {
			'sambaName':               'mootestshare',
			'sambaPublic':             '0',
			'sambaBrowseable':         '1',
			'sambaWriteable':          '1',
			'sambaCreateMode':         '666',
			'sambaDirectoryMode':      '777',
			'sambaForceCreateMode':    '888',
			'sambaForceDirectoryMode': '999',
			}
		propsMod = {
			'path': '/home/sharez',
			}
		propsModNfs = {
			'writeable': '0',
			}
		propsModSamba = {
			'sambaName':               'mootestsharez',
			'sambaPublic':             '1',
			'sambaBrowseable':         '0',
			'sambaWriteable':          '0',
			'sambaCreateMode':         '555',
			'sambaDirectoryMode':      '444',
			'sambaForceCreateMode':    '333',
			'sambaForceDirectoryMode': '222',
			}
		options = []
		if self.nfs:
			propsAdd.update(propsAddNfs)
			options.append('nfs')
		if self.smb:
			propsAdd.update(propsAddSamba)
			options.append('samba')
		self.name = 'testshare'
		self.createProperties = propsAdd
		self.createOptions = options
		self.modifyProperties = propsMod

	def shortDescription(self):
		desc = super(SharesShareBaseCase, self).shortDescription()
		opts = []
		if self.nfs:
			opts.append('NFS')
		if self.smb:
			opts.append('Samba')
		return '%s(%s)' % (desc, ','.join(opts))


class SharesNfsShareTestCase(SharesShareBaseCase):
	def __init__(self, *args, **kwargs):
		self.nfs = True
		self.smb = False
		super(SharesNfsShareTestCase, self).__init__(*args, **kwargs)

class SharesSambaShareTestCase(SharesShareBaseCase):
	def __init__(self, *args, **kwargs):
		self.nfs = False
		self.smb = True
		super(SharesSambaShareTestCase, self).__init__(*args, **kwargs)

class SharesNfsSambaShareTestCase(SharesShareBaseCase):
	def __init__(self, *args, **kwargs):
		self.nfs = True
		self.smb = True
		super(SharesNfsSambaShareTestCase, self).__init__(*args, **kwargs)


def suite():
	import sys, unittest
	suite = unittest.TestSuite()
	suite.addTest(SharesNfsShareTestCase())
	suite.addTest(SharesSambaShareTestCase())
	suite.addTest(SharesNfsSambaShareTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
