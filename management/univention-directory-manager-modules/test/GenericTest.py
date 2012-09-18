# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: generic object tests
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


from BaseTest import BaseCase, TestError, ProcessFailedError


class ObjectNotFoundError(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when a created object cannot be found.
	'''
	def __init__(self, test, dn):
		helper = ''
		if dn is not None:
			helper = ' at DN ' + dn
		error = 'Failed to find object %s%s (module %s)' \
			% (test.name, helper, test.modname)
		TestError.__init__(self, error, test)

class LeftoverObjectFound(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when a deleted object can still be found.
	'''
	def __init__(self, test, dn):
		helper = ''
		if dn is not None:
			helper = ' at DN ' + dn
		error = 'Leftover object %s found%s (module %s)' \
			% (test.name, helper, test.modname)
		TestError.__init__(self, error, test)

class ObjectNotIdentifiedError(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when a found object cannot be identified.
	'''
	def __init__(self, test, dn):
		error = 'Failed to identify object %s at DN %s (module %s)' \
			% (test.name, dn, test.modname)
		TestError.__init__(self, error, test)

class PropertyInvalidError(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when an object has an incorrect property.
	'''
	def __init__(self, test, dn, property, expected, actual):
		d = test.module.property_descriptions
		description = d[property].short_description
		e1 = 'Incorrect property %s (%s)' % (property, description)
		e2 = 'of object %s at DN %s (module %s).' \
		     % (test.name, dn, test.modname)
		e3= 'Expected: "%s" Actual: "%s"' % (expected, actual)
		error = '%s %s %s' % (e1, e2, e3)
		TestError.__init__(self, error, test)

class ObjectClassNotPresentError(TestError):
	'''Assertion error in the Univention Admin test suite.

	Raised when an object has an incorrect objectClass.
	'''
	def __init__(self, test, dn, option, expected, actual):
		o = test.module.options
		description = o[option].short_description
		e1 = 'Incorrect objectClasses for option %s (%s)' \
		     % (option, description)
		e2 = 'of object %s at DN %s (module %s).' \
		     % (test.name, dn, test.modname)
		e3= 'Expected: "%s" Actual: "%s"' % (expected, actual)
		error = '%s %s %s' % (e1, e2, e3)
		TestError.__init__(self, error, test)


class GenericTestCase(BaseCase):
	'''A generic test case for a Univention Admin module.

	Provides methods to create, modify and remove the current object.
	Also provides methods to surround these with useful tests and to run a
	default set of operations with their respective tests.  And provides
	methods to reuse the default testing behaviour in customized ways.

	When defining a new test case, you probably want to derive from
	GenericTestCase and override "setUp" (and "tearDown"!) to set up the
	properties you want.
	For more control, override "hookAfterCreated", "hookAfterModified" or
	"hookAfterRemoved" to plug in additional tests of actions.
	For absolute control, override "runTest" and run exactly what you
	want.

	For improved diagnostics, override "shortDescription" and "id".

	The methods for operating on the object are "create", "modify" and
	"remove".
	The methods for testing these operatinos are "testCreate",
	"testModify" and "testRemove".
	The methods for the most common tests are "testObjectExists",
	"testObjectExistsNot", "testObjectIdentify", "testObjectOptions" and
	"testObjectProperties".
	The methods you should use for additional checks on Commands and
	properties are "_checkProcess" and "_testProperty", respectively.

	NOTE: Many methods refer to "mappings from property names to values".
	The protocol for these is as follows:
	For every mapping M with key K and value V such that M[K] == V,
	K is the name of a property P defined in the current module.  If P is
	single-valued, V is a string denoting the desired value for P.  If P
	is multi-valued, V is either a string denoting the single desired
	value for P or a mapping from the special keys "set, "append" and
	"remove" to a sequence of strings denoting the values to be set,
	appended or removed, respectively.
	If K is the special key "position", V is a string denoting the DN of
	the container the object is/will be stored in.

	NOTE: You should override the constructor, starting with this template:
		def __init__(self, *args, **kwargs):
			self.modname = "custom/module"
			super(MyTestCase, self).__init__(*args, **kwargs)
	'''
	def __init__(self, *args, **kwargs):
		super(GenericTestCase, self).__init__(*args, **kwargs)

	def __setupCommandSelect(self, cmd, name, dn):
		if dn is not None:
			cmd.dn(dn)
			return
		# NOTE: this filter might be a little fragile...
		cmd.filter('%s="%s"' % (self.identifier, self.name))

	def __setupCommandUpdate(self, cmd, name, properties, options = None):
		descriptions = self.module.property_descriptions
		special = set(('position',))
		single = (p for p in properties
			  if not p in special
			  if not descriptions[p].multivalue)
		multi  = (p for p in properties
			  if not p in special
			  if descriptions[p].multivalue)
		# set identifying property
		if name is not None:
			cmd.set(self.identifier, name)
		# set special properties
		for key in special:
			if key in properties:
				setattr(self, key, properties[key])
				getattr(cmd, key)(properties[key])
		# set single-value properties
		for prop in single:
			cmd.set(prop, properties[prop])
		# set multi-value properties
		for prop in multi:
			if isinstance(properties[prop], basestring):
				cmd.set(prop, properties[prop])
				continue
			for key in properties[prop]:
				for val in properties[prop][key]:
					getattr(cmd, key)(prop, val)
		# set options
		if options is not None:
			for opt in options:
				cmd.option(opt)

	def _checkProcess(self, proc, action):
		'''Check a command operating on the current object for errors.

		"Proc" must be a Command object that was run before this call.
		"Action" should be a short description of the action the
		command was supposed to perform.

		Raise "ProcessFailedError" if the command failed.
		'''
		msg = 'Failed to %s object (module %s)' % (action, self.modname)
		proc.check(msg, self)

	def _testSinglePropertyEqual(self, p, obj, props):
		'''Check equality of a single-valued property.

		"P" must be the name of the checked property.
		"Obj" must be a Univention Admin object to test against the
		current object.
		"Props" must be a mapping from property names to values and
		must contain the property "P".

		Raise "PropertyInvalidError" if the property values differ.
		'''
		descriptions = self.module.property_descriptions
		syntax = descriptions[p].syntax
		v1 = props[p]
		v2 = syntax.tostring(obj[p])
		if v1 != v2:
			raise PropertyInvalidError(self, self.dn, p, v1, v2)

	def _testMultiPropertyEqual(self, p, obj, props):
		'''Check equality of a multi-valued property.

		"P" must be the name of the checked property.
		"Obj" must be a Univention Admin object to test against the
		current object.
		"Props" must be a mapping from property names to values and
		must contain the property "P".

		Raise "PropertyInvalidError" if the property values differ.
		'''
		args = (self, self.dn, p, props[p], obj[p])
		descriptions = self.module.property_descriptions
		syntax = descriptions[p].syntax
		present = set([syntax.tostring(v) for v in obj[p]])
		if isinstance(props[p], basestring):
			if not props[p] in present:
				raise PropertyInvalidError(*args)
			return
		removed = set(props[p].get('remove', []))
		a1 = set(props[p].get('set', []))
		a2 = set(props[p].get('append', []))
		added = a1.union(a2)
		if removed.intersection(present):
			raise PropertyInvalidError(*args)
		if not added.issubset(present):
			raise PropertyInvalidError(*args)

	def _testProperty(self, p, obj, props):
		'''Check equality of a property.

		"P" must be the name of the checked property. Whether "P" is
		single- or multi-valued will be checked automatically.
		"Obj" must be a Univention Admin object to test against the
		current object.
		"Props" must be a mapping from property names to values and
		must contain the property "P".

		Raise "PropertyInvalidError" if the property values differ.
		'''
		descriptions = self.module.property_descriptions
		if descriptions[p].multivalue:
			return self._testMultiPropertyEqual(p, obj, props)
		return self._testSinglePropertyEqual(p, obj, props)

	def useDN(self, dn):
		'''Register "DN" for the current object.

		Registering a DN for the object has the following effects:
		- Access to "self.dn" will return the last registered DN.
		- After the test fixture has run, -all- registered DNs will be
		  deleted.
		'''
		self.dn = dn
		self.__leftover_dns.add(dn)

	def testObjectExists(self, dn = None):
		'''Check that the object exists.

		"DN", if given, indicates the DN of the object to test.
		
		Raise "ObjectNotFoundError" if it does not exists.
		'''
		dn, attr = self.search(dn = dn)
		if attr is None:
			raise ObjectNotFoundError(self, dn)
		self.useDN(dn)

	def testObjectExistsNot(self, dn = None):
		'''Check that the object does not exists.

		"DN", if given, indicates the DN of the object to test.

		Raise "LeftoverObjectFound" if it does exists.
		'''
		dn, attr = self.search(dn = dn)
		if bool(attr):
			self.useDN(dn)
			raise LeftoverObjectFound(self, dn)

	def testObjectIdentify(self):
		'''Check that the object is handled by the current module.

		Raise "ObjectNotIdentifiedError" if the module cannot identify
		the current object.
		'''
		_, attr = self.search(dn = self.dn)
		if not self.module.identify(self.dn, attr):
			raise ObjectNotIdentifiedError(self, self.dn)

	def testObjectOptions(self, options):
		'''Check that the given options are present on the object.

		"Options" is a collection of options to check for.

		Raise "ObjectClassNotPresentError" if an option is not present.
		'''
		attr = self.ldap.get(dn = self.dn, attr = ['objectClass'])
		for o in options:
			classes = self.module.options[o].objectClasses
			if not classes:
				continue
			if classes.issubset(attr['objectClass']):
				continue
			args = (self, self.dn, o, classes, attr['objectClass'])
			raise ObjectClassNotPresentError(*args)

	def testObjectProperties(self, properties):
		'''Check that the given properties have the expected values.

		"Properties" is a mapping from properties to expected values.

		Raise "PropertyInvalidError" if a property contains unexpected
		values.
		'''
		special = set(('position',))
		props = (p for p in properties
			 if not p in special
			 if not p in self.uncheckedProperties)
		obj = self.open(dn = self.dn)
		for prop in props:
			self._testProperty(prop, obj, properties)

	def create(self, properties, options = None, name = None):
		'''Create an object of the current module.

		"Properties" is a mapping from property names to values.
		"Options", is a collection of options (defaults to None).
		"Name" is the name of the object to create (defaults to the current objects name).
		Returns the generated command object.
		'''
		if name is None:
			name = self.name
		cmd = self.Command('create')
		self.__setupCommandUpdate(cmd, name, properties, options)
		return cmd.run()

	def modify(self, properties, dn = None, name = None, newName = None):
		'''Modify an object of the current module.
		
		"Properties" is a mapping from property names to values;
		only values that should be changed need to be included.
		"DN", if given, is the DN of the object to modify.
		"Name" is the name of the object to modify (defaults to the current objects name).
		"NewName", if given, is the name of the object after modification.
		Returns the generated command object.
		'''
		if name is None:
			name = self.name
		if newName is None:
			newName = self.newName
		cmd = self.Command('modify')
		self.__setupCommandSelect(cmd, name, dn)
		self.__setupCommandUpdate(cmd, newName, properties)
		return cmd.run()

	def remove(self, name = None, dn = None, recursive = False):
		'''Remove an object of the current module.
		
		"Name" is the name of the object to remove (defaults to the current objects name).
		"DN", if given, is the DN of the object to remove.
		"Recursive" should be True to remove the object recursively.
		Returns the generated command object.
		'''
		if name is None:
			name = self.name
		cmd = self.Command('remove')
		self.__setupCommandSelect(cmd, name, dn)
		if recursive:
			cmd.recursive()
		return cmd.run()
	
	def hookAfterCreated(self, dn):
		'''Perform additional actions after creating an object.

		Override this method to plug in additional code after the
		object was created.
		'''
		pass

	def hookAfterModified(self, dn):
		'''Perform additional actions after modifying an object.

		Override this method to plug in additional code after the
		object was modified.
		'''
		pass

	def hookAfterRemoved(self, dn):
		'''Perform additional tests after removing an object.

		Override this method to plug in additional code after the
		object was removed.
		'''
		pass

	def setUp(self):
		'''Hook method for setting up the test fixture before exercising it.
		
		Override this method to set up values for these properties:
		"name": The name of the object that will be tested.
			You most definitely want to set this one.
		"newName": The name of the object after modification.
			Defaults to None, in which case the object will not be renamed.
		"createProperties": The properties to create the object with.
			Must be a mapping from property names to values.
			NOTE: See "GenericTestCase" for the complete protocol.
			Defaults to the empty dict.
		"createOptions": The options to create the object with.
			Should be a collection of strings.
			Defaults to the empty set.
		"modifyProperties": The properties to modify the object with.
			The protocol is equivalent to that of "createProperties".
			Defaults to the empty dict.
		"uncheckedProperties": Properties that cannot be auto-checked.
			A set of property names, defaults to the empty set.
			If any properties cannot be checked automatically,
			add them to this set.
			You may still test them with the "hook*" methods.
		"dn": The DN of the object.
			Will be set automatically when the object is found,
			so in most cases you do not need to bother.
			If you want to test an existing object, or need to
			override the default search, set the DN here.

		This is also a good place to call "superordinate" is necessary.
		See "BaseCase" for information about that method.

		When overriding this method, make sure you call to your
		superclass first!
		'''
		self.name = None
		self.newName = None
		self.oldName = None
		self.createProperties = {}
		self.modifyProperties = {}
		self.uncheckedProperties = set()
		self.createOptions = set()
		self.dn = None
		self.superordinate()
		self.arg()
		self.__leftover_dns = set()

	def runTest(self):
		'''Test operation of the current module.

		This test creates a new object, modifies it and finally removes it.
		Override this method to perform a different set of tests or
		to have more fine-grained control over the tests you run.

		You might want to check out overriding "hookAfterCreated",
		"hookAfterModified" or "hookAfterRemoved" instead.
		'''
		self.testCreate()
		self.testModify()
		self.testRemove()

	def testCreate(self):
		'''Test object creation for the current module.

		This test creates a new object and then checks that it exists,
		is identified by the module and has the correct options and
		property values set.
		'''
		proc = self.create(self.createProperties,
				   self.createOptions)
		self._checkProcess(proc, 'create')
		self.testObjectExists(self.dn)
		self.testObjectIdentify()
		self.testObjectOptions(self.createOptions)
		self.testObjectProperties(self.createProperties)
		self.hookAfterCreated(self.dn)

	def testModify(self):
		'''Test object modification for the current module.

		This test modifies the current object and then checks that it
		exists, is identified by the module and has the correct property
		values set.
		'''
		proc = self.modify(self.modifyProperties, dn = self.dn)
		self._checkProcess(proc, 'modify')
		if self.newName is not None:
			self.dn = None
			self.oldName, self.name = self.name, self.newName
		self.testObjectExists(self.dn)
		self.testObjectIdentify()
		self.testObjectProperties(self.modifyProperties)
		self.hookAfterModified(self.dn)

	def testRemove(self):
		'''Test object removal for the current module.

		This test removes the current object and then checks that it
		does not exist any more.
		'''
		proc = self.remove(dn = self.dn)
		self._checkProcess(proc, 'remove')
		self.testObjectExistsNot(self.dn)
		self.hookAfterRemoved(self.dn)

	def tearDown(self):
		'''Hook method for deconstructing the test fixture after testing it.

		Override this method to perform additional cleanup.

		When overriding this method, make sure you call to your superclass first!
		'''
		for dn in self.__leftover_dns:
			self.remove(dn = dn, recursive = True)

	def shortDescription(self):
		return 'testing module %s' % self.modname
