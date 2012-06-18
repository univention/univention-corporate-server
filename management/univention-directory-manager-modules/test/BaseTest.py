# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: basic test support
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


from unittest import TestCase

import os, random, string


import univention.config_registry
import univention.admin.uexceptions as uex
import univention.admin.config	    as uconf
import univention.admin.modules     as umod
import univention.admin.uldap       as uldap


_OPTIONS = ('binddn', 'bindpw', 'position', 'tls')
_UNIVENTION_ADMIN = '/usr/sbin/univention-admin'


class TestError(AssertionError):
	'''Base class for exceptions in the test suite.

	Inherit from this class if you want to define your own test-specific
	error cases.  You want to pass your error message, optionally along
	with the failed test object, to this classes constructor.'''
	# TODO: I want to extract test case information from the docstring.
	def __init__(self, error, test = None):
		if test is not None:
			if test.__doc__ is not None:
				t = 'Failed to: %s\n'
				t = t % test.__doc__.split('\n')[0]
				error = t + error
		AssertionError.__init__(self, error)

class ProcessFailedError(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when a subprocess failed.
	'''
	def __init__(self, proc, message = '', test = None):
		self.name = proc.name
		self.status = proc.status
		self.output = proc.output
		if message:
			message += '\n'
		error = '''%ssubprocess %s failed (%s):
%s''' % (message, proc.name, proc.status, ''.join(proc.output))
		TestError.__init__(self, error, test)


class BaseCase(TestCase):
	'''Base class for Univention Admin test cases.

	Provides access to the Univention Admin command-line interface,
	Univention Baseconfig, the LDAP DIT and assorted low-level features.

	NOTE: If you want to define a test case for a Univention Admin module,
	you really want to inherit from GenericTestCase instead.
	'''
	def __init__(self, options = None, *args, **kwargs):
		super(BaseCase, self).__init__(*args, **kwargs)
		self.__initModule()
		self.__initBaseConfig()
		self.__initConfig()
		self.__initOptions(options)
		self.ldap = self.__initAccess()
		self.__superordinate = None
		self.__arg = None

	def __getDefaultBinddn(self):
		return self.rdn('cn=admin')

	def __getDefaultBindpw(self):
		secret = open('/etc/ldap.secret', 'r')
		passwd = secret.readline().strip()
		secret.close()
		return passwd

	def __getDefaultFilter(self):
		if self.identifier is None:
			return ''
		mapping = self.module.mapping
		ident = self.module.mapping.mapName(self.identifier)
		if ident:
			name = mapping.mapValue(self.identifier, self.name)
		else:
			ident = self.identifier
			name = self.name
		return '(%s=%s)' % (ident, name)

	def __initAccess(self):
		baseDN = self.bc('ldap/base')
		master = self.bc('ldap/master')
		binddn = self.__options['binddn']
		bindpw = self.__options['bindpw']
		tls = self.__options.get('tls', 2)
		try:
			return uldap.access(host = master, base = baseDN,
					    binddn = binddn, bindpw = bindpw,
					    start_tls = tls)
		except uex.authFail:
			# TODO: handle authentication failure
			return None

	def __initBaseConfig(self):
		self.__configRegistry = univention.config_registry.ConfigRegistry()
		self.__configRegistry.load()

	def __initConfig(self):
		self.__config = uconf.config(host = self.bc('ldap/master'))

	def __initModule(self):
		self.module = None
		self.identifier = None
		if getattr(self, 'modname', None) is None:
			return
		self.module = umod.get(self.modname)
		if getattr(self, 'identifier', None) is None:
			descriptions = self.module.property_descriptions
			identifiers = [prop for prop in descriptions
				       if descriptions[prop].identifies]
			if identifiers:
				self.identifier = identifiers[0]

	def __initOptions(self, options):
		self.__options = options
		if options is None:
			self.__options = {}
		if not 'binddn' in self.__options:
			self.__options['binddn'] = self.__getDefaultBinddn()
		if not 'bindpw' in self.__options:
			self.__options['bindpw'] = self.__getDefaultBindpw()

	def bc(self, key, default = None):
		'''Fetch "key" from Univention Baseconfig.

		Return "default" if not "key" in Baseconfig. [default: None]
		'''
		return self.__configRegistry.get(key, default)

	def random(self, digits = 4):
		'''Return a string of "Digit" random digits. [default: 4]
		'''
		return ''.join(random.sample(string.digits, digits))

	def rdn(self, rdn):
		'''Construct a DN from 'RDN' relative to the LDAP base DN.
		'''
		return '%s,%s' % (rdn, self.bc('ldap/base'))

	def open(self, dn = None, filter = None):
		'''Lookup and open a univention admin object.

		"DN", if given, is the DN of the object to open.
		"Filter", if given, is an LDAP fitler to find the object with.
		By default, the current object will be opened.
		Return the opened object.
		'''
		kwargs = {}
		# filter by identifier by default
		if filter is None:
			filter = self.__getDefaultFilter()
		# don't filter, search by DN
		if dn is not None:
			filter = None
			kwargs = { 'base': dn, 'scope': 'base' }
		# set superordinate if present
		kwargs.setdefault('superordinate', self.superordinate())
		obj = self.module.lookup(self.__config, self.ldap,
					 filter, **kwargs)[0]
		obj.open()
		return obj

	def search(self, filter = None, dn = None):
		'''Search an LDAP object.

		"DN", if given, is the DN of the object to search for.
		"Filter", if given, is an LDAP fitler to find the object with.
		By default, the current object will be searched for.
		Return the first LDAP search result.
		'''
		# don't filter, search by DN
		if dn is not None:
			return dn, self.ldap.get(dn = dn)
		# filter by identifier by default
		if filter is None:
			filter = self.__getDefaultFilter()
		result = self.ldap.search(filter = filter)
		if result:
			return result[0]
		return None, None

	def arg(self, argument = None):
		'''Set or query the current objects "arg".

		Set "arg" to "Argument", if given, otherwise just return it.

		Some objects are not stored in their own LDAP object but are
		attached to an existing object.  To identify such an object,
		both the DN and the "arg" are needed.
		'''
		if argument is None:
			return self.__arg
		self.__arg = argument
		return self.__arg

	def superordinate(self, argument = None):
		'''Set or query the current objectts "superordinate".

		Set the superordinate to "Argument", if given; otherwise just
		return it.

		If "Argument" is a DN, the superordinate object will be
		fetched from that DN and stored; otherwise, it is assumed to
		be an object and will be queried for the DN to fetch the
		superordinate object from.
		'''
		if argument is None:
			return self.__superordinate
		supmod = umod.superordinate(self.modname)
		if isinstance(argument, basestring):
			dn = argument
			sup = None
		else:
			dn = argument.dn
			sup = getattr(argument, 'superordinate')
		if callable(sup):
			sup = sup()
		kwargs = { 'base': dn, 'scope': 'base', 'superordinate': sup } 
		res = supmod.lookup(self.__config, self.ldap, '', **kwargs)
		self.__superordinate = res[0]
		return self.__superordinate

	class __Command(object):
		'''A command line object to call "univention-admin".

		Contains the module and action to perform and can be extended
		with further options to the "univention-admin" call.  Also
		contains authentication information.
		'''

		def __init__(self, test, action, module, options):
			self.__test = test
			self.name = _UNIVENTION_ADMIN
			self.output = None
			self.status = None
			cmd = [self.name, module, action]
			for opt in _OPTIONS:
				try:
					cmd.extend(('--%s' % opt,
						    str(options[opt])))
				except KeyError:
					pass
			self.__command = cmd

		def __escape(self, string):
			return '"%s"' % string.replace('"', r'\"')

		def position(self, position):
			'''Set the "position" argument.'''
			self.__command.append('--position')
			self.__command.append(self.__escape(position))

		def superordinate(self, superordinate):
			'''Set the "superordinate" argument.'''
			self.__command.append('--superordinate')
			self.__command.append(self.__escape(superordinate))

		def arg(self, arg):
			'''Set the "arg" argument.'''
			self.__command.append('--arg')
			self.__command.append(self.__escape(arg))

		def dn(self, dn):
			'''Set the "dn" argument.'''
			self.__command.append('--dn')
			self.__command.append(self.__escape(dn))

		def filter(self, filter):
			'''Set the "filter" argument.'''
			self.__command.append('--filter')
			self.__command.append(self.__escape(filter))

		def recursive(self):
			'''Set the "recursive" argument.'''
			self.__command.append('--recursive')

		def set(self, key, value):
			'''Set the "set" argument.'''
			value = self.__escape(value)
			self.__command.append('--set')
			self.__command.append('%s=%s' % (key, value))

		def append(self, key, value):
			'''Set the "append" argument.'''
			value = self.__escape(value)
			self.__command.append('--append')
			self.__command.append('%s=%s' % (key, value))

		def remove(self, key, value):
			'''Set the "remove" argument.'''
			value = self.__escape(value)
			self.__command.append('--remove')
			self.__command.append('%s=%s' % (key, value))

		def option(self, option):
			'''Set the "option" argument.'''
			self.__command.append('--option')
			self.__command.append(option)

		def run(self):
			'''Run the assembled command.'''
			command = ' '.join(self.__command)
			pipe = os.popen(command)
			output = pipe.readlines()
			status = pipe.close()
			if status is not None:
				status = os.WEXITSTATUS(status)
			self.output = output
			self.status = status
			return self

		def check(self, message = '', test = None):
			'''Check that the command ran successfully.

			"Message" is an optional error message to print if the
			command failed.
			"Test", if given, is the test object that issued the
			command that might have failed.

			Raise "ProcessFailedError" if the command failed.
			'''
			if self.status is not None:
				raise ProcessFailedError(self, message, test)

	def Command(self, action, module = None):
		'''Create a command line object to perform "Action" on "Module".

		"Module" defaults to the current module.
		'''

		# default to current module
		if module is None:
			module = self.modname
		# construct command object
		cmd = self.__Command(self, action, module, self.__options)
		# set superordinate if present
		if self.__superordinate:
			cmd.superordinate(self.__superordinate.dn)
		# set arg if present
		if self.__arg:
			cmd.arg(self.__arg)
		return cmd
