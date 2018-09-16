# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

"""
En/Decoders for object properties.
"""

from __future__ import absolute_import, unicode_literals
import datetime
import time
from .binary_props import Base64BinaryProperty
from univention.admin.uexceptions import valueInvalidSyntax

try:
	from typing import Any, Dict, List, Optional, Text
except ImportError:
	pass


class BaseEncoder(object):
	static = False  # whether to create an instance or use a class/static method

	def __init__(self, property_name=None, *args, **kwargs):  # type: (Optional[Text], *Any, **Any) -> None
		self.property_name = property_name

	def __repr__(self):  # type: () -> Text
		return '{}({})'.format(self.__class__.__name__, self.property_name)

	def encode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
		raise NotImplementedError()

	def decode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
		raise NotImplementedError()


class Base64BinaryPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):  # type: (Optional[Text]) -> Optional[Base64BinaryProperty]
		if value:
			return Base64BinaryProperty(self.property_name, value)
		else:
			return value

	def encode(self, value=None):  # type: (Optional[Base64BinaryProperty]) -> Optional[Text]
		if value:
			return value.encoded
		else:
			return value


class DatePropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> Optional[datetime.date]
		if value:
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])
		else:
			return value

	@staticmethod
	def encode(value=None):  # type: (Optional[datetime.date]) -> Optional[Text]
		if value:
			return value.strftime('%Y-%m-%d')
		else:
			return value


class DisabledPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> bool
		return value == '1'

	@staticmethod
	def encode(value=None):  # type: (Optional[bool]) -> Text
		return '1' if value else '0'


class HomePostalAddressPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[List[List[Text]]]) -> Optional[List[Dict[Text, Text]]]
		if value:
			return [{'street': v[0], 'zipcode': v[1], 'city': v[2]} for v in value]
		else:
			return value

	@staticmethod
	def encode(value=None):  # type: (Optional[List[Dict[Text, Text]]]) -> Optional[List[List[Text]]]
		if value:
			return [[v['street'], v['zipcode'], v['city']] for v in value]
		else:
			return value


class MultiLanguageTextPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[List[List[Text]]]) -> Optional[Dict[Text, Text]]
		if value:
			return dict(value)
		else:
			return value

	@staticmethod
	def encode(value=None):  # type: (Optional[Dict[Text, Text]]) -> Optional[List[List[Text]]]
		if value:
			return [[k, v] for k, v in value.items()]
		else:
			return value


class SambaLogonHoursPropertyEncoder(BaseEncoder):
	static = True
	_weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

	@classmethod
	def decode(cls, value=None):  # type: (Optional[List[int]]) -> Optional[List[Text]]
		if value:
			return ['{} {}-{}'.format(cls._weekdays[v/24], v % 24, v % 24 + 1) for v in value]
		else:
			return value

	@classmethod
	def encode(cls, value=None):  # type: (Optional[List[Text]]) -> Optional[List[int]]
		if value:
			try:
				values = [v.split() for v in value]
				return [cls._weekdays.index(w) * 24 + int(h.split('-', 1)[0]) for w, h in values]
			except (IndexError, ValueError):
				raise valueInvalidSyntax('One or more entries in sambaLogonHours have invalid syntax.')
		else:
			return value


class StringBooleanPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> bool
		return value == 'TRUE'

	@staticmethod
	def encode(value=None):  # type: (Optional[bool]) -> Text
		if value:
			return 'TRUE'
		else:
			return 'FALSE'
