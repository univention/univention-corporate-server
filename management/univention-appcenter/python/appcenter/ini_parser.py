#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Tools for reading ini files
#
# Copyright 2015-2017 Univention GmbH
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
#


from ConfigParser import RawConfigParser, ParsingError
import re

from univention.appcenter.meta import UniventionMetaClass, UniventionMetaInfo
from univention.appcenter.log import get_base_logger


ini_logger = get_base_logger().getChild('ini')


class IniFileReadError(Exception):
	pass


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

	def __init__(self, required=False, default=None):
		self.required = required
		self.default = default

	def parse(self, value):
		return value


class IniSectionListAttribute(IniSectionAttribute):
	def parse(self, value):
		if value is None:
			return []
		return re.split(', ', value)


class IniSectionObject(object):
	__metaclass__ = UniventionMetaClass
	_main_attr_name = 'name'

	def __init__(self, **kwargs):
		for attr in self._attrs.values():
			setattr(self, attr.name, kwargs.get(attr.name, attr.default))
		setattr(self, self._main_attr_name, kwargs.get(self._main_attr_name))

	def __repr__(self):
		return '%s(%s=%r)' % (self.__class__.__name__, self._main_attr_name, getattr(self, self._main_attr_name))

	@classmethod
	def _find_attr(cls, name):
		canonical_name = filter(str.isalnum, name).lower()
		for attr in cls._attrs.values():
			if attr.name.replace('_', '').lower() == canonical_name:
				return attr

	@classmethod
	def from_parser(cls, parser, section):
		kwargs = {cls._main_attr_name: section}
		for name, value in parser.items(section):
			attr = cls._find_attr(name)
			if attr:
				kwargs[attr.name] = attr.parse(value)
		for attr in cls._attrs.values():
			if attr.required and attr.name not in kwargs:
				raise IniFileReadError('%s missing in [%s]' % (attr.name, section))
		return cls(**kwargs)

	@classmethod
	def all_from_file(cls, fname):
		ret = []
		parser = read_ini_file(fname)
		for section in parser.sections():
			try:
				obj = cls.from_parser(parser, section)
			except IniFileReadError as exc:
				raise IniFileReadError('%s: %s' % (fname, exc))
			else:
				ret.append(obj)
		return ret
