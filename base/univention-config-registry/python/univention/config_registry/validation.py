# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

"""
|UCR| type validation classes.

Checks validity of type definitions and type compatibility of values to be set.
"""

import ipaddress
import json
import re
from six.moves.urllib.parse import urlsplit
from typing import Dict, Iterator, Optional, Pattern, Type as _Type, Union, cast  # noqa: F401

import univention.config_registry_info as cri
from univention.config_registry.backend import BooleanConfigRegistry


class BaseValidator(object):
	"""
	Base class for |UCR| type validators.
	"""

	NAME = ""

	def __init__(self, attrs):  # type: (Dict[str, str]) -> None
		pass

	def is_valid(self, value):
		# type: (str) -> bool
		"""
		Check if value is valid.

		:returns: ``True`` if valid, ``False`` otherwise.
		"""
		try:
			return bool(self.validate(value))
		except Exception:
			return False

	def validate(self, value):
		# type: (str) -> object
		"""
		Check is value is valid.

		:returns: somethings that can be evaulated with ``bool()``.
		:raises Exception: on errors.
		"""
		raise NotImplementedError()

	@classmethod
	def _recurse_subclasses(cls):
		# type: () -> Iterator[_Type[BaseValidator]]
		for clazz in cls.__subclasses__():
			if clazz.NAME:
				yield clazz

			# FIXME: Python 3.5: yield from clazz._recurse_subclasses()
			for sub in clazz._recurse_subclasses():
				yield sub


class String(BaseValidator):
	"""
	Validator for |UCR| type "str".

	Supports a Python compatible regular expression defined in the optional `regex` constraints
	"""

	NAME = "str"
	REGEX = None  # type: Optional[Pattern]

	def __init__(self, attrs):  # type: (Dict[str, str]) -> None
		self.regex = attrs.get('regex', self.REGEX)  # type: ignore

	@property
	def regex(self):
		# type: () -> Optional[str]
		return self._rxc.pattern if self._rxc else None

	@regex.setter
	def regex(self, regex):
		# type: (Union[None, str, Pattern]) -> None
		rxc = None
		if regex is not None:
			try:
				rxc = re.compile(regex)
			except (ValueError, TypeError, re.error):
				raise ValueError('error compiling regex: %s' % regex)
		self._rxc = rxc

	def validate(self, value):
		# type: (str) -> object
		if self._rxc:
			return self._rxc.match(value)
		else:
			return isinstance(value, str)


class URLProxy(BaseValidator):
	"""
	Validator for |UCR| type "url_proxy".
	"""

	NAME = "url_proxy"

	def validate(self, value):
		# type: (str) -> object
		o = urlsplit(value)
		o.port  # may raise ValueError
		return o.scheme in {"http", "https"} and not o.path and not o.query and not o.fragment


class IPv4Address(BaseValidator):
	"""
	Validator for |UCR| type "ipv4address".
	"""

	NAME = "ipv4address"

	def validate(self, value):
		# type: (str) -> object
		return ipaddress.IPv4Address(u"%s" % value)  # FIXME: remove Python 2.7 unicoding


class IPv6Address(BaseValidator):
	"""
	Validator for |UCR| type "ipv6address".
	"""

	NAME = "ipv6address"

	def validate(self, value):
		# type: (str) -> object
		return ipaddress.IPv6Address(u"%s" % value)  # FIXME: remove Python 2.7 unicoding


class IPAddress(BaseValidator):
	"""
	Validator for |UCR| type "ipaddress".
	"""

	NAME = "ipaddress"

	def validate(self, value):
		# type: (str) -> object
		return ipaddress.ip_address(u"%s" % value)  # FIXME: remove Python 2.7 unicoding


class Integer(BaseValidator):
	"""
	Validator for |UCR| type "int".

	Supports optional 'min' and 'max' constraints
	"""

	NAME = "int"

	MIN = None  # type: Optional[int]
	MAX = None  # type: Optional[int]

	def __init__(self, attrs):
		# type: (Dict[str, str]) -> None
		self._min = None  # type: Optional[int]
		self._max = None  # type: Optional[int]
		self.min = cast(Optional[int], attrs.get('min', self.MIN))
		self.max = cast(Optional[int], attrs.get('max', self.MAX))

	@property
	def min(self):
		# type: () -> Optional[int]
		return self._min

	@min.setter
	def min(self, value):
		# type: (Optional[str]) -> None
		if value is None:
			self._min = None
			return

		val = int(value)
		if self._max is not None and val > self._max:
			raise ValueError('min %d > max %d' % (val, self._max))

		self._min = val

	@property
	def max(self):
		# type: () -> Optional[int]
		return self._max

	@max.setter
	def max(self, value):
		# type: (Optional[str]) -> None
		if value is None:
			self._max = None
			return

		val = int(value)
		if self._min is not None and self._min > val:
			raise ValueError('min %d > max %d' % (self._min, val))

		self._max = val

	def validate(self, value):
		# type: (str) -> object
		val = int(value)
		if self._min is not None and val < self._min:
			return False
		if self._max is not None and val > self._max:
			return False
		return True


class UnsignedNumber(Integer):
	"""
	Validator for |UCR| type "uint".
	"""

	NAME = "uint"
	MIN = 0


class PositiveNumber(Integer):
	"""
	Validator for |UCR| type "pint".
	"""

	NAME = "pint"
	MIN = 1


class PortNumber(Integer):
	"""
	Validator for |UCR| type "portnumber".
	"""

	NAME = "portnumber"
	MIN = 0
	MAX = 65535


class Bool(BaseValidator):
	"""
	Validator for |UCR| type "bool".
	"""

	NAME = "bool"
	_BCR = BooleanConfigRegistry()

	def validate(self, value):
		# type: (str) -> object
		return self._BCR.is_true(value=value) or self._BCR.is_false(value=value)


class Json(BaseValidator):
	"""
	Validator for |UCR| type "json".
	"""

	NAME = "json"

	def validate(self, value):
		# type: (str) -> object
		return json.loads(value) or True


class List(BaseValidator):
	"""
	Validator for |UCR| type "list".
	"""

	NAME = "list"
	DEFAULT_SEPARATOR = ','

	def __init__(self, attrs):
		# type: (Dict[str, str]) -> None
		self.element_type = attrs.get('elementtype')
		regex = attrs.get('separator', self.DEFAULT_SEPARATOR)
		try:
			self.separator = re.compile(regex)
		except re.error:
			raise ValueError('error compiling regex: %s' % regex)
		typ = Type.TYPE_CLASSES.get(self.element_type, String)
		self.checker = typ(attrs)

	def validate(self, value):
		# type: (str) -> object
		if self.element_type is None:
			return False
		vinfo = cri.Variable()
		vinfo['type'] = self.element_type
		val = Type(vinfo)
		return all(val.check(element.strip()) for element in self.separator.split(value))


class Type(object):
	"""
	Basic |UCR| type validation class.

	Usage::

		try:
			validator = Type(vinfo)
		except (TypeError, ValueError):
			# invalid type
		else:
			if validator.check(value_to_be_set):
				# check ok: set value
			else:
				# value is not compatible with type definition
	"""
	TYPE_CLASSES = {
		clazz.NAME: clazz
		for clazz in BaseValidator._recurse_subclasses()
	}  # type: Dict[Optional[str], _Type[BaseValidator]]

	def __init__(self, vinfo):
		# type: (cri.Variable) -> None
		self.vinfo = vinfo
		self.vtype = self.vinfo.get('type')  # type: Optional[str]
		typ = self.TYPE_CLASSES.get(self.vtype, String)
		self.checker = typ(self.vinfo)

	def check(self, value):
		# type: (str) -> bool
		return self.checker.is_valid(value)
