#!/usr/share/ucs-test/runner /usr/bin/py.test
## desc: Ini Parser
## tags: [basic, coverage]
## exposure: safe

import os

import pytest

from univention.appcenter.log import log_to_logfile, log_to_stream
from univention.appcenter.ini_parser import read_ini_file, IniSectionObject, IniSectionAttribute, IniSectionBooleanAttribute, IniSectionListAttribute, NoValueError, ParseError, TypedIniSectionObject


log_to_logfile()
log_to_stream()


@pytest.yield_fixture
def valid_ini_file():
	content = '''[A section]
AKey = A Value
ABool = Yes
ADefault = Overwritten
AList = v1, v2, v3\, or something else

[Another section]
AKey = Another Value
ABool = False
AList = Just v1
Unknown = Irrelevant

[A third section]
#AKey = Another Value
ABool = False

[A fourth section]
AKey = A 4th Value
ABool = Something else'''
	fname = '/tmp/test.ini'
	with open(fname, 'wb') as fd:
		fd.write(content)
	yield fname
	os.unlink(fname)


@pytest.fixture
def missing_ini_file():
	fname = '/tmp/missing.ini'
	try:
		os.unlink(fname)
	except EnvironmentError:
		pass
	return fname


@pytest.fixture
def invalid_ini_file(valid_ini_file):
	with open(valid_ini_file) as fd:
		content = fd.read()
	with open(valid_ini_file, 'wb') as fd:
		fd.write(content[1:])
	return valid_ini_file


@pytest.fixture
def list_ini_file(valid_ini_file):
	content = '''[A section]
AList = v1, v2, v3\, or something else
AnotherList = v1, v2

[Another section]
AnotherList = v1

[A third section]
AList = X
AnotherList = X'''
	with open(valid_ini_file, 'wb') as fd:
		fd.write(content)
	return valid_ini_file


@pytest.fixture
def typed_ini_file(valid_ini_file):
	content = '''[first/item]
Type = TypedObject1
MyKey = My Value

[second/item]
Type = TypedObject2

[third/item]
Type = TypedObject3

[fourth/item]
MyKey = 4th Value'''
	with open(valid_ini_file, 'wb') as fd:
		fd.write(content)
	return valid_ini_file


@pytest.fixture
def typed_ini_file2(valid_ini_file):
	content = '''[first/item]
Klass = TypedObjectWithDefault1

[second/item]
Unknown = Irrelevant'''
	with open(valid_ini_file, 'wb') as fd:
		fd.write(content)
	return valid_ini_file


def test_valid_ini_file(valid_ini_file):
	parser = read_ini_file(valid_ini_file)
	assert parser.get('A section', 'AKey') == 'A Value'
	assert parser.get('Another section', 'AKey') == 'Another Value'


def test_missing_ini_file(missing_ini_file):
	parser = read_ini_file(missing_ini_file)
	assert len(parser.sections()) == 0


def test_invalid_ini_file(invalid_ini_file):
	parser = read_ini_file(invalid_ini_file)
	assert len(parser.sections()) == 0

	parser = read_ini_file(None)
	assert len(parser.sections()) == 0


class TestSectionObject(IniSectionObject):
	a_key = IniSectionAttribute()
	a_bool = IniSectionBooleanAttribute()
	a_default = IniSectionAttribute(default='The default')


def test_section_object(valid_ini_file):
	objs = TestSectionObject.all_from_file(valid_ini_file)
	assert len(objs) == 3
	obj1, obj2, obj3 = objs

	assert obj1.a_key == 'A Value'
	assert obj1.a_bool is True
	assert obj1.a_default == 'Overwritten'

	assert obj2.to_dict() == {'a_key': 'Another Value', 'a_bool': False, 'a_default': 'The default', 'name': 'Another section'}

	assert obj3.a_key is None
	assert repr(obj3) == 'TestSectionObject(name=\'A third section\')'


class AdvancedTestSectionObject(TestSectionObject):
	a_key = IniSectionAttribute(required=True, localisable=True)
	a_list = IniSectionListAttribute()


def test_localisable_attribute(valid_ini_file):
	objs = AdvancedTestSectionObject.all_from_file(valid_ini_file)
	assert len(objs) == 2
	obj1, obj2 = objs


class ListObject(IniSectionObject):
	a_list = IniSectionListAttribute()
	another_list = IniSectionListAttribute(choices=['v1', 'v2'])


def test_list_attribute(list_ini_file):
	objs = ListObject.all_from_file(list_ini_file)
	assert len(objs) == 2
	obj1, obj2 = objs

	assert obj1.a_list == ['v1', 'v2', 'v3, or something else']
	assert obj1.another_list == ['v1', 'v2']
	assert obj2.a_list == []
	assert obj2.another_list == ['v1']

	assert IniSectionListAttribute().parse(None) == []


class ChoicesObject(IniSectionObject):
	a_key = IniSectionAttribute(choices=['A Value', 'Another Value'])


def test_choices(valid_ini_file):
	objs = ChoicesObject.all_from_file(valid_ini_file)
	assert len(objs) == 3
	obj1, obj2, obj3 = objs

	assert obj1.a_key == 'A Value'
	assert obj2.a_key == 'Another Value'
	assert obj3.a_key is None


def test_no_value_error(valid_ini_file):
	parser = read_ini_file(valid_ini_file)
	with pytest.raises(NoValueError) as exc:
		AdvancedTestSectionObject.from_parser(parser, 'A third section', 'en')
	assert str(exc.value) == 'Missing a_key in A third section'


def test_parse_error(valid_ini_file):
	parser = read_ini_file(valid_ini_file)
	with pytest.raises(ParseError) as exc:
		TestSectionObject.from_parser(parser, 'A fourth section', 'en')
	assert str(exc.value) == 'Cannot parse abool in A fourth section: Not a Boolean'


class TypedObject(TypedIniSectionObject):
	my_key = IniSectionAttribute(default='Typed0')


class TypedObject1(TypedObject):
	my_key = IniSectionAttribute(default='Typed1')


class TypedObject2(TypedObject1):
	my_key = IniSectionAttribute(default='Typed2')


class TypedObjectWithDefault(TypedIniSectionObject):
	_type_attr = 'klass'
	klass = IniSectionAttribute(default='DefaultTypedObject')
	my_key = IniSectionAttribute(default='Typed0')


class TypedObjectWithDefault1(TypedObjectWithDefault):
	my_key = IniSectionAttribute(default='Typed1')


class DefaultTypedObject(TypedObjectWithDefault):
	my_key = IniSectionAttribute(default='Typed9')


def test_typed_section_object(typed_ini_file):
	objs = TypedObject.all_from_file(typed_ini_file)
	assert len(objs) == 4
	obj1, obj2, obj3, obj4 = objs

	assert obj1.__class__ is TypedObject1
	assert obj1.my_key == 'My Value'

	assert obj2.__class__ is TypedObject2
	assert obj2.my_key == 'Typed2'

	assert obj3.__class__ is TypedObject
	assert obj3.my_key == 'Typed0'

	assert obj4.__class__ is TypedObject
	assert obj4.my_key == '4th Value'


def test_typed_section_object2(typed_ini_file2):
	objs = TypedObjectWithDefault.all_from_file(typed_ini_file2)
	assert len(objs) == 2
	obj1, obj2 = objs

	assert obj1.__class__ is TypedObjectWithDefault1
	assert obj1.my_key == 'Typed1'

	assert obj2.__class__ is DefaultTypedObject
	assert obj2.my_key == 'Typed9'
