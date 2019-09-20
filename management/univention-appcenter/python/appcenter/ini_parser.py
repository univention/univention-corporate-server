#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Tools for reading ini files
#
# Copyright 2017-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
#


from ConfigParser import RawConfigParser, ParsingError, NoSectionError, NoOptionError
import re
from copy import deepcopy

from univention.appcenter.utils import get_locale
from univention.appcenter.meta import UniventionMetaClass, UniventionMetaInfo
from univention.appcenter.log import get_base_logger


ini_logger = get_base_logger().getChild('ini')


class NoValueError(Exception):
	def __init__(self, name, section):
		self.name = name
		self.section = section

	def __str__(self):
		return 'Missing %s in %s' % (self.name, self.section)


class ParseError(Exception):
	def __init__(self, name, section, message):
		self.name = name
		self.section = section
		self.message = message

	def __str__(self):
		return 'Cannot parse %s in %s: %s' % (self.name, self.section, self.message)


def read_ini_file(filename, parser_class=RawConfigParser):
	parser = parser_class()
	try:
		with open(filename, 'rb') as f:
			parser.readfp(f)
	except TypeError:
		pass
	except EnvironmentError:
		pass
	except ParsingError as exc:
		ini_logger.warn('Could not parse %s' % filename)
		ini_logger.warn(str(exc))
	else:
		return parser
	# in case of error return empty parser
	return parser_class()


class IniSectionAttribute(UniventionMetaInfo):
	save_as_dict = '_attrs'
	pop = True
	auto_set_name = True

	def __init__(self, required=False, default=None, localisable=False, choices=None):
		self.required = required
		self.default = deepcopy(default)
		self.localisable = localisable
		self.choices = choices

	def _canonical_name(self):
		return re.sub('_', '', self.name)

	@classmethod
	def _fetch_from_parser(cls, parser, section, name):
		return parser.get(section, name)

	def get(self, parser, section, locale):
		name = self._canonical_name()
		names = [name]
		if self.localisable and locale:
			names.insert(0, '%s[%s]' % (name, locale))
		for name in names:
			try:
				value = self._fetch_from_parser(parser, section, name)
			except (NoSectionError, NoOptionError):
				pass
			else:
				try:
					return self.parse(value)
				except ValueError as exc:
					raise ParseError(name, section, str(exc))
		else:
			if self.required:
				raise NoValueError(self.name, section)
			return self.default

	def parse(self, value):
		if self.choices:
			if value not in self.choices:
				raise ValueError('%r not in %r' % (value, self.choices))
		return value


class IniSectionBooleanAttribute(IniSectionAttribute):
	def _fetch_from_parser(self, parser, section, name):
		try:
			return parser.getboolean(section, name)
		except ValueError:
			raise ParseError(name, section, 'Not a Boolean')


class IniSectionListAttribute(IniSectionAttribute):
	def __init__(self, required=False, default=[], localisable=False, choices=None):
		super(IniSectionListAttribute, self).__init__(required, default, localisable, choices)

	def parse(self, value):
		'''Returns a list; splits on "," (stripped, whitespaces before
		and after are removed).  If a single value needs to contain a
		",", it can be escaped with backslash: "My \\, value".'''
		if value is None:
			return []
		value = re.split(r'(?<=[^\\])\s*,\s*', value)
		values = [re.sub(r'\\,', ',', val) for val in value]
		if self.choices:
			for val in values:
				if val not in self.choices:
					raise ValueError('%r not in %r' % (val, self.choices))
		return values


class IniSectionObject(object):
	__metaclass__ = UniventionMetaClass
	_main_attr_name = 'name'

	def __init__(self, **kwargs):
		for attr in self._attrs.values():
			setattr(self, attr.name, kwargs.get(attr.name, attr.default))
		setattr(self, self._main_attr_name, kwargs.get(self._main_attr_name))

	def __repr__(self):
		return '%s(%s=%r)' % (self.__class__.__name__, self._main_attr_name, getattr(self, self._main_attr_name))

	def to_dict(self):
		ret = {self._main_attr_name: getattr(self, self._main_attr_name)}
		for key, value in self._attrs.items():
			ret[key] = getattr(self, value.name)
		return ret

	@classmethod
	def from_parser(cls, parser, section, locale):
		return cls.build(parser, section, locale)

	@classmethod
	def build(cls, parser, section, locale):
		kwargs = {cls._main_attr_name: section}
		for attr in cls._attrs.values():
			kwargs[attr.name] = attr.get(parser, section, locale)
		return cls(**kwargs)

	@classmethod
	def all_from_file(cls, fname, locale=None):
		if locale is None:
			locale = get_locale()
		ret = []
		parser = read_ini_file(fname)
		for section in parser.sections():
			try:
				obj = cls.from_parser(parser, section, locale)
			except (NoValueError, ParseError) as exc:
				ini_logger.warn('%s: %s' % (fname, exc))
			else:
				ret.append(obj)
		return ret


class TypedIniSectionObjectMetaClass(UniventionMetaClass):
	@classmethod
	def _add_class_type(mcs, name, base, klass):
		if hasattr(base, '_class_types'):
			base._class_types[name] = klass
			for _base in base.__bases__:
				mcs._add_class_type(name, _base, klass)

	def __new__(mcs, name, bases, attrs):
		new_cls = super(TypedIniSectionObjectMetaClass, mcs).__new__(mcs, name, bases, attrs)
		new_cls._class_types = {}
		for base in bases:
			mcs._add_class_type(name, base, new_cls)
		return new_cls


class TypedIniSectionObject(IniSectionObject):
	__metaclass__ = TypedIniSectionObjectMetaClass
	_type_attr = 'type'

	@classmethod
	def get_class(cls, name):
		return cls._class_types.get(name, cls)

	@classmethod
	def from_parser(cls, parser, section, locale):
		try:
			value = parser.get(section, cls._type_attr)
		except (NoSectionError, NoOptionError):
			attr = cls._attrs.get(cls._type_attr)
			if attr:
				value = attr.default
			else:
				value = None
		klass = cls.get_class(value)
		return klass.build(parser, section, locale)
