# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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
# <https://www.gnu.org/licenses/>.

"""
En/Decoders for object properties.
"""

from __future__ import absolute_import, unicode_literals
import datetime
import lazy_object_proxy
from univention.admin.syntax import sambaGroupType
from .binary_props import Base64BinaryProperty, Base64Bzip2BinaryProperty
from .udm import UDM
from typing import Any, Dict, List, Optional, Text, Type, TypeVar


BaseEncoderTV = TypeVar('BaseEncoderTV', bound='univention.udm.encoders.BaseEncoder')


__dn_list_property_encoder_class_cache = {}  # type: Dict[Text, Type[DnListPropertyEncoder]]
__dn_property_encoder_class_cache = {}  # type: Dict[Text, Type[DnPropertyEncoder]]


class BaseEncoder(object):
	static = False    # type: bool

	def __init__(self, property_name=None, *args, **kwargs):  # type: (Optional[Text], *Any, **Any) -> None
		...

	def __repr__(self):  # type: () -> Text
		...

	def encode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
		...

	def decode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
		...


class Base64BinaryPropertyEncoder(BaseEncoder):
	def decode(self, value=None):  # type: (Optional[Text]) -> Optional[Base64BinaryProperty]
		...

	def encode(self, value=None):  # type: (Optional[Base64BinaryProperty]) -> Optional[Text]
		...


class Base64Bzip2BinaryPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):  # type: (Optional[Text]) -> Optional[Base64Bzip2BinaryProperty]
		...

	def encode(self, value=None):  # type: (Optional[Base64Bzip2BinaryProperty]) -> Optional[Text]
		...


class DatePropertyEncoder(BaseEncoder):
	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> Optional[datetime.date]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[datetime.date]) -> Optional[Text]
		...


class DisabledPropertyEncoder(BaseEncoder):
	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> bool
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[bool]) -> Text
		...


class HomePostalAddressPropertyEncoder(BaseEncoder):
	@staticmethod
	def decode(value=None):  # type: (Optional[List[List[Text]]]) -> Optional[List[Dict[Text, Text]]]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[List[Dict[Text, Text]]]) -> Optional[List[List[Text]]]
		...


class ListOfListOflTextToDictPropertyEncoder(BaseEncoder):
	@staticmethod
	def decode(value=None):  # type: (Optional[List[List[Text]]]) -> Optional[Dict[Text, Text]]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[Dict[Text, Text]]) -> Optional[List[List[Text]]]
		...


class MultiLanguageTextAppcenterPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[List[Text]]) -> Optional[Dict[Text, Text]]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[Dict[Text, Text]]) -> Optional[List[Text]]
		...


class SambaGroupTypePropertyEncoder(BaseEncoder):
	static = True
	choices = dict(sambaGroupType.choices)
	choices_reverted = dict((v, k) for k, v in sambaGroupType.choices)

	@classmethod
	def decode(cls, value=None):  # type: (Optional[List[Text]]) -> Optional[Text]
		...

	@classmethod
	def encode(cls, value=None):  # type: (Optional[Text]) -> Optional[List[Text]]
		...


class SambaLogonHoursPropertyEncoder(BaseEncoder):
	static = True
	_weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

	@classmethod
	def decode(cls, value=None):  # type: (Optional[List[int]]) -> Optional[List[Text]]
		...

	@classmethod
	def encode(cls, value=None):  # type: (Optional[List[Text]]) -> Optional[List[int]]
		...


class StringCaseInsensitiveResultLowerBooleanPropertyEncoder(BaseEncoder):
	static = True
	result_case_func = 'lower'
	false_string = 'false'
	true_string = 'true'

	@classmethod
	def decode(cls, value=None):  # type: (Optional[Text]) -> bool
		...

	@classmethod
	def encode(cls, value=None):  # type: (Optional[bool]) -> Text
		...


class StringCaseInsensitiveResultUpperBooleanPropertyEncoder(StringCaseInsensitiveResultLowerBooleanPropertyEncoder):
	result_case_func = 'upper'


class StringIntBooleanPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):  # type: (Optional[Text]) -> bool
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[bool]) -> Text
		...


class StringIntPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):  # type: (Optional[Text]) -> Optional[int]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[int]) -> Optional[Text]
		...


class StringListToList(BaseEncoder):
	static = True
	separator = ' '

	@classmethod
	def decode(cls, value=None):  # type: (Optional[Text]) -> Optional[List[Text]]
		...

	@classmethod
	def encode(cls, value=None):  # type: (Optional[List[Text]]) -> Optional[Text]
		...


class DnListPropertyEncoder(BaseEncoder):
	static = False
	udm_module_name = ''

	class DnsList(list):
		# a list with an additional member variable
		objs = None  # type: DnListPropertyEncoder.MyProxy

		def __deepcopy__(self, memodict=None):
			...

	class MyProxy(lazy_object_proxy.Proxy):
		# overwrite __repr__ for better navigation in ipython
		def __repr__(self, __getattr__=object.__getattribute__):
			...

	def __init__(self, property_name=None, connection=None, api_version=None, *args, **kwargs):
		# type: (Optional[Text], Optional[Any], Optional[int], *Any, **Any) -> None
		assert connection is not None, 'Argument "connection" must not be None.'
		assert api_version is not None, 'Argument "api_version" must not be None.'
		super(DnListPropertyEncoder, self).__init__(property_name, *args, **kwargs)
		self._udm = None  # type: UDM

	def __repr__(self):  # type: () -> Text
		...

	def _list_of_dns_to_list_of_udm_objects(self, value):
		...

	def decode(self, value=None):  # type: (Optional[List[Text]]) -> Optional[List[Text]]
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[List[Text]]) -> Optional[List[Text]]
		...

	@property
	def udm(self):
		...


class CnameListPropertyEncoder(DnListPropertyEncoder):
	udm_module_name = 'dns/alias'

	def _list_of_dns_to_list_of_udm_objects(self, value):
		...


class DnsEntryZoneAliasListPropertyEncoder(DnListPropertyEncoder):
	udm_module_name = 'dns/alias'

	def _list_of_dns_to_list_of_udm_objects(self, value):
		...


class DnsEntryZoneForwardListMultiplePropertyEncoder(DnListPropertyEncoder):
	udm_module_name = 'dns/forward_zone'

	@staticmethod
	def _itemgetter(value):
		...

	def _list_of_dns_to_list_of_udm_objects(self, value):
		...


class DnsEntryZoneForwardListSinglePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
	udm_module_name = 'dns/forward_zone'

	@staticmethod
	def _itemgetter(value):
		...


class DnsEntryZoneReverseListMultiplePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
	udm_module_name = 'dns/reverse_zone'

	@staticmethod
	def _itemgetter(value):
		return value[0]


class DnsEntryZoneReverseListSinglePropertyEncoder(DnsEntryZoneReverseListMultiplePropertyEncoder):
	udm_module_name = 'dns/reverse_zone'

	@staticmethod
	def _itemgetter(value):
		...


class DnPropertyEncoder(BaseEncoder):
	static = False
	udm_module_name = ''

	class DnStr(str):
		# a string with an additional member variable
		obj = None  # type: DnPropertyEncoder.MyProxy

		def __deepcopy__(self, memodict=None):
			...

	class MyProxy(lazy_object_proxy.Proxy):
		# overwrite __repr__ for better navigation in ipython
		def __repr__(self, __getattr__=object.__getattribute__):
			...

	def __init__(self, property_name=None, connection=None, api_version=None, *args, **kwargs):
		assert connection is not None, 'Argument "connection" must not be None.'
		assert api_version is not None, 'Argument "api_version" must not be None.'
		super(DnPropertyEncoder, self).__init__(property_name, *args, **kwargs)
		self._udm = None  # type: UDM

	def __repr__(self):  # type: () -> Text
		...

	def _dn_to_udm_object(self, value):
		...

	def decode(self, value=None):  # type: (Optional[Text]) -> str
		...

	@staticmethod
	def encode(value=None):  # type: (Optional[Text]) -> Optional[Text]
		...

	@property
	def udm(self):  # type: () -> UDM
		...


def _classify_name(name):  # type: (Text) -> Text
	...


def dn_list_property_encoder_for(udm_module_name):  # type: (Text) -> Type[DnListPropertyEncoder]
	...


def dn_property_encoder_for(udm_module_name):  # type: (Text) -> Type[DnPropertyEncoder]
	...
