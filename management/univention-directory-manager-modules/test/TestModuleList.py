# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: modules list tests
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


from BaseTest import BaseCase, TestError


_FORBIDDEN_MODULES = set((
	'users/passwd',			# searching users/passwd is forbidden
	))


# So... process handling with subprocess is really broken: it just hangs on
# large amounts of output.  To check for yourself, run the following command:
#
# > python2.6 -c "import subprocess; subprocess.call(('univention-admin', 'settings/printermodel', 'list'), stdout=subprocess.PIPE)"
#
# So we had to look for alternatives, of which subprocess names a few:
# - os.system
# - os.spawn*
# - os.popen*
# - popen2.*
#
# os.system and os.spawn* will always write to stdout, so they're unusable.
# popen2 suffers from the same problem as subprocess, demonstrated with this:
#
# > python -c "import popen2; p = Popen4('univention-admin settings/printermodel list'); p.wait()
#
# Leaving us only with os.popen*.  Which, on the plus side, perform really
# well, it's only piping and checking the return code that's really awkward.
# Also, checking the return code *before* looking at the output is impossible,
# requiring us to pump the *full* output into a list of strings -- which does
# impact performance, though not as badly as I had expected, so this seems
# like the way to go...


class ListingFailed(TestError):
	def __init__(self, test, proc):
		helper = ''
		if test.supname is not None:
			helper = ' (superordinate %s)' % test.supname
		error = '''Failed to list objects for module %s%s: subprocess %s failed (%s):
%s''' % (test.modname, helper, proc.name, proc.status, ''.join(proc.output))
		TestError.__init__(self, error, test)

class ListingForbidden(TestError):
	def __init__(self, test, proc):
		error = '''Listing of forbidden module %s succeeded: subprocess %s returned %s:
%s''' % (test.modname, proc.name, proc.status, ''.join(proc.output))
		TestError.__init__(self, error, test)


class ModuleListTestCase(BaseCase):
	def __init__(self, modname, *args, **kwargs):
		self.modname = modname
		super(ModuleListTestCase, self).__init__(*args, **kwargs)
		self.supname = getattr(self.module, 'superordinate', None)
		self.dns = set()

	def __getSuperordinateDNs(self):
		module = ModuleListTestCase(modname = self.supname,
					    methodName = 'testList')
		return module.getList()

	def __runProcess(self, superordinate = None):
		cmd = self.Command('list')
		if superordinate is not None:
			cmd.superordinate(superordinate)
		return cmd.run()

	def __runAllProcesses(self):
		if self.supname is None:
			return (self.__runProcess(),)
		return map(self.__runProcess, self.__getSuperordinateDNs())

	def __checkProcess(self, proc):
		if proc.status is not None:
			raise ListingFailed(self, proc)

	def __checkForbidden(self, proc):
		if proc.status != 3:
			raise ListingForbidden(self, proc)

	def __filterDNs(self, proc):
		dns = [line[3:].strip()
		       for line in proc.output
		       if line.startswith('DN:')]
		return dns

	def __updateDNs(self, procs):
		for p in procs:
			self.dns.update(self.__filterDNs(p))

	def testList(self, wantDNs = False):
		'''Test listing the objects of SELF.MODNAME.

		If WANTDNS is True, a collection of DNs of these objects will
		be constructed and returned.
		'''

		# check that operation is forbidden
		if self.modname in _FORBIDDEN_MODULES:
			proc = self.__runProcess()
			self.__checkForbidden(proc)
			return self.dns

		# run operations, check return codes
		procs = self.__runAllProcesses()
		map(self.__checkProcess, procs)

		# construct a list of DNs if required
		if wantDNs:
			self.__updateDNs(procs)
		return self.dns

	def getList(self):
		'''Return the collection of DNs of objects for SELF.MODNAME.
		'''
		return self.testList(wantDNs = True)

	def shortDescription(self):
		return 'listing module %s' % self.modname


def suite():
	import sys, unittest
	prefix = 'univention/admin/handlers/'
	suite = unittest.TestSuite()
	modules = [mod[len(prefix):]
		   for mod in sys.modules
		   if mod.startswith(prefix)]
	modules.sort()
	for mod in modules:
		suite.addTest(ModuleListTestCase(modname = mod,
						 methodName = 'testList'))
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())
