# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2023 Univention GmbH
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

from __future__ import absolute_import, unicode_literals

import datetime  # noqa: F401
from typing import Any, Dict, List, Optional, Type, TypeVar  # noqa: F401

import lazy_object_proxy

import univention
from univention.admin.syntax import sambaGroupType

from .binary_props import Base64BinaryProperty, Base64Bzip2BinaryProperty  # noqa: F401
from .udm import UDM  # noqa: F401


BaseEncoderTV = TypeVar('BaseEncoderTV', bound=univention.udm.encoders.BaseEncoder)  # noqa: PYI001


__dn_list_property_encoder_class_cache = {}  # type: Dict[str, Type[DnListPropertyEncoder]]
__dn_property_encoder_class_cache = {}  # type: Dict[str, Type[DnPropertyEncoder]]


class BaseEncoder(object):
    static = False    # type: bool

    def __init__(self, property_name=None, *args, **kwargs):  # type: (Optional[str], *Any, **Any) -> None
        ...

    def __repr__(self):  # type: () -> str
        ...

    def encode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
        ...

    def decode(self, value=None):  # type: (Optional[Any]) -> Optional[Any]
        ...


class Base64BinaryPropertyEncoder(BaseEncoder):
    def decode(self, value=None):  # type: (Optional[str]) -> Optional[Base64BinaryProperty]
        ...

    def encode(self, value=None):  # type: (Optional[Base64BinaryProperty]) -> Optional[str]
        ...


class Base64Bzip2BinaryPropertyEncoder(BaseEncoder):
    static = False

    def decode(self, value=None):  # type: (Optional[str]) -> Optional[Base64Bzip2BinaryProperty]
        ...

    def encode(self, value=None):  # type: (Optional[Base64Bzip2BinaryProperty]) -> Optional[str]
        ...


class DatePropertyEncoder(BaseEncoder):
    @staticmethod
    def decode(value=None):  # type: (Optional[str]) -> Optional[datetime.date]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[datetime.date]) -> Optional[str]
        ...


class DisabledPropertyEncoder(BaseEncoder):
    @staticmethod
    def decode(value=None):  # type: (Optional[str]) -> bool
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[bool]) -> str
        ...


class HomePostalAddressPropertyEncoder(BaseEncoder):
    @staticmethod
    def decode(value=None):  # type: (Optional[List[List[str]]]) -> Optional[List[Dict[str, str]]]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[List[Dict[str, str]]]) -> Optional[List[List[str]]]
        ...


class ListOfListOflTextToDictPropertyEncoder(BaseEncoder):
    @staticmethod
    def decode(value=None):  # type: (Optional[List[List[str]]]) -> Optional[Dict[str, str]]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[Dict[str, str]]) -> Optional[List[List[str]]]
        ...


class MultiLanguageTextAppcenterPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value=None):  # type: (Optional[List[str]]) -> Optional[Dict[str, str]]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[Dict[str, str]]) -> Optional[List[str]]
        ...


class SambaGroupTypePropertyEncoder(BaseEncoder):
    static = True
    choices = dict(sambaGroupType.choices)
    choices_reverted = ...

    @classmethod
    def decode(cls, value=None):  # type: (Optional[List[str]]) -> Optional[str]
        ...

    @classmethod
    def encode(cls, value=None):  # type: (Optional[str]) -> Optional[List[str]]
        ...


class SambaLogonHoursPropertyEncoder(BaseEncoder):
    static = True
    _weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

    @classmethod
    def decode(cls, value=None):  # type: (Optional[List[int]]) -> Optional[List[str]]
        ...

    @classmethod
    def encode(cls, value=None):  # type: (Optional[List[str]]) -> Optional[List[int]]
        ...


class StringCaseInsensitiveResultLowerBooleanPropertyEncoder(BaseEncoder):
    static = True
    result_case_func = 'lower'
    false_string = 'false'
    true_string = 'true'

    @classmethod
    def decode(cls, value=None):  # type: (Optional[str]) -> bool
        ...

    @classmethod
    def encode(cls, value=None):  # type: (Optional[bool]) -> str
        ...


class StringCaseInsensitiveResultUpperBooleanPropertyEncoder(StringCaseInsensitiveResultLowerBooleanPropertyEncoder):
    result_case_func = 'upper'


class StringIntBooleanPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value=None):  # type: (Optional[str]) -> bool
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[bool]) -> str
        ...


class StringIntPropertyEncoder(BaseEncoder):
    static = False

    def decode(self, value=None):  # type: (Optional[str]) -> Optional[int]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[int]) -> Optional[str]
        ...


class StringListToList(BaseEncoder):
    static = True
    separator = ' '

    @classmethod
    def decode(cls, value=None):  # type: (Optional[str]) -> Optional[List[str]]
        ...

    @classmethod
    def encode(cls, value=None):  # type: (Optional[List[str]]) -> Optional[str]
        ...


class DnListPropertyEncoder(BaseEncoder):
    static = False
    udm_module_name = ''

    class DnsList(list):
        # a list with an additional member variable
        objs = None  # type: DnListPropertyEncoder.MyProxy  # noqa: PYI026

        def __deepcopy__(self, memodict=None):
            ...

    class MyProxy(lazy_object_proxy.Proxy):
        # overwrite __repr__ for better navigation in ipython
        def __repr__(self, __getattr__=object.__getattribute__):
            ...

    def __init__(self, property_name=None, connection=None, api_version=None, *args, **kwargs):
        # type: (Optional[str], Optional[Any], Optional[int], *Any, **Any) -> None
        assert connection is not None, 'Argument "connection" must not be None.'
        assert api_version is not None, 'Argument "api_version" must not be None.'
        super(DnListPropertyEncoder, self).__init__(property_name, *args, **kwargs)
        self._udm = None  # type: UDM

    def __repr__(self):  # type: () -> str
        ...

    def _list_of_dns_to_list_of_udm_objects(self, value):
        ...

    def decode(self, value=None):  # type: (Optional[List[str]]) -> Optional[List[str]]
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[List[str]]) -> Optional[List[str]]
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
        ...


class DnsEntryZoneReverseListSinglePropertyEncoder(DnsEntryZoneReverseListMultiplePropertyEncoder):
    udm_module_name = 'dns/reverse_zone'

    @staticmethod
    def _itemgetter(value):
        ...


class DnPropertyEncoder(BaseEncoder):
    static = False
    udm_module_name = ''

    class DnStr(str):  # noqa: SLOT000
        # a string with an additional member variable
        obj = None  # type: DnPropertyEncoder.MyProxy  # noqa: PYI026

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

    def __repr__(self):  # type: () -> str
        ...

    def _dn_to_udm_object(self, value):
        ...

    def decode(self, value=None):  # type: (Optional[str]) -> str
        ...

    @staticmethod
    def encode(value=None):  # type: (Optional[str]) -> Optional[str]
        ...

    @property
    def udm(self):  # type: () -> UDM
        ...


def _classify_name(name):  # type: (str) -> str
    ...


def dn_list_property_encoder_for(udm_module_name):  # type: (str) -> Type[DnListPropertyEncoder]
    ...


def dn_property_encoder_for(udm_module_name):  # type: (str) -> Type[DnPropertyEncoder]
    ...
