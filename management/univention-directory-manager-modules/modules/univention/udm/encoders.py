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
import sys
import six
import datetime
import time
import lazy_object_proxy
from .binary_props import Base64BinaryProperty, Base64Bzip2BinaryProperty
from .udm import UDM
from .utils import UDebug
from .exceptions import NoObject, UnknownModuleType
from univention.admin.uexceptions import valueInvalidSyntax
from univention.admin.syntax import sambaGroupType

__dn_list_property_encoder_class_cache = {}
__dn_property_encoder_class_cache = {}


class BaseEncoder(object):
	static = False  # whether to create an instance or use a class/static method

	def __init__(self, property_name=None, *args, **kwargs):
		self.property_name = property_name

	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, self.property_name)

	def encode(self, value=None):
		raise NotImplementedError()

	def decode(self, value=None):
		raise NotImplementedError()


class Base64BinaryPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):
		if value:
			return Base64BinaryProperty(self.property_name, value)
		else:
			return value

	def encode(self, value=None):
		if value:
			if not isinstance(value, Base64BinaryProperty):
				value = Base64BinaryProperty(self.property_name, raw_value=value)
			return value.encoded
		else:
			return value


class Base64Bzip2BinaryPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):
		if value:
			return Base64Bzip2BinaryProperty(self.property_name, value)
		else:
			return value

	def encode(self, value=None):
		if value:
			return value.encoded
		else:
			return value


class DatePropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		if value:
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])
		else:
			return value

	@staticmethod
	def encode(value=None):
		if value:
			return value.strftime('%Y-%m-%d')
		else:
			return value


class DisabledPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		return value == '1'

	@staticmethod
	def encode(value=None):
		return '1' if value else '0'


class HomePostalAddressPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		if value:
			return [{'street': v[0], 'zipcode': v[1], 'city': v[2]} for v in value]
		else:
			return value

	@staticmethod
	def encode(value=None):
		if value:
			return [[v['street'], v['zipcode'], v['city']] for v in value]
		else:
			return value


class ListOfListOflTextToDictPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		if value:
			return dict(value)
		else:
			return value

	@staticmethod
	def encode(value=None):
		if value:
			return [[k, v] for k, v in value.items()]
		else:
			return value


class MultiLanguageTextAppcenterPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		if value:
			res = {}
			for s in value:
				lang, txt = s.split(' ', 1)
				lang = lang.strip('[]')
				res[lang] = txt
			return res
		else:
			return value

	@staticmethod
	def encode(value=None):
		if value:
			return ['[{}] {}'.format(k, v) for k, v in value.items()]
		else:
			return value


class SambaGroupTypePropertyEncoder(BaseEncoder):
	static = True
	choices = dict(sambaGroupType.choices)
	choices_reverted = dict((v, k) for k, v in sambaGroupType.choices)

	@classmethod
	def decode(cls, value=None):
		try:
			return cls.choices[value]
		except KeyError:
			return value

	@classmethod
	def encode(cls, value=None):
		try:
			return cls.choices_reverted[value]
		except KeyError:
			return value


class SambaLogonHoursPropertyEncoder(BaseEncoder):
	static = True
	_weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

	@classmethod
	def decode(cls, value=None):
		if value:
			return ['{} {}-{}'.format(cls._weekdays[v / 24], v % 24, v % 24 + 1) for v in value]
		else:
			return value

	@classmethod
	def encode(cls, value=None):
		if value:
			try:
				values = [v.split() for v in value]
				return [cls._weekdays.index(w) * 24 + int(h.split('-', 1)[0]) for w, h in values]
			except (IndexError, ValueError):
				six.reraise(valueInvalidSyntax, valueInvalidSyntax('One or more entries in sambaLogonHours have invalid syntax.'), sys.exc_info()[2])
		else:
			return value


class StringCaseInsensitiveResultLowerBooleanPropertyEncoder(BaseEncoder):
	static = True
	result_case_func = 'lower'
	false_string = 'false'
	true_string = 'true'

	@classmethod
	def decode(cls, value=''):
		return type(value) == str and value.lower() == cls.true_string

	@classmethod
	def encode(cls, value=None):
		assert cls.result_case_func in ('lower', 'upper')
		if value:
			return getattr(cls.true_string, cls.result_case_func)()
		else:
			return getattr(cls.false_string, cls.result_case_func)()


class StringCaseInsensitiveResultUpperBooleanPropertyEncoder(StringCaseInsensitiveResultLowerBooleanPropertyEncoder):
	result_case_func = 'upper'


class StringIntBooleanPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		return value == '1'

	@staticmethod
	def encode(value=None):
		if value:
			return '1'
		else:
			return '0'


class StringIntPropertyEncoder(BaseEncoder):
	static = False

	def decode(self, value=None):
		if value in ('', None):
			return None
		else:
			try:
				return int(value)
			except ValueError:
				six.reraise(valueInvalidSyntax, valueInvalidSyntax('Value of {!r} must be an int (is {!r}).'.format(self.property_name, value)), sys.exc_info()[2])

	@staticmethod
	def encode(value=None):
		if value is None:
			return value
		else:
			return str(value)


class StringListToList(BaseEncoder):
	static = True
	separator = ' '

	@classmethod
	def decode(cls, value=None):
		if value:
			return value.split(cls.separator)
		else:
			return value

	@classmethod
	def encode(cls, value=None):
		if value:
			return cls.separator.join(value)
		else:
			return value


class DnListPropertyEncoder(BaseEncoder):
	"""
	Given a list of DNs, return the same list with an additional member
	``objs``. ``objs`` is a lazy object that will become the list of UDM
	objects the DNs refer to, when accessed.

	:py:func:`dn_list_property_encoder_for()` will dynamically produce
	subclasses of this for every UDM module required.
	"""
	static = False
	udm_module_name = ''

	class DnsList(list):
		# a list with an additional member variable
		objs = None

		def __deepcopy__(self, memodict=None):
			return list(self)

	class MyProxy(lazy_object_proxy.Proxy):
		# overwrite __repr__ for better navigation in ipython
		def __repr__(self, __getattr__=object.__getattribute__):
			return super(DnListPropertyEncoder.MyProxy, self).__str__()

	def __init__(self, property_name=None, connection=None, api_version=None, *args, **kwargs):
		assert connection is not None, 'Argument "connection" must not be None.'
		assert api_version is not None, 'Argument "api_version" must not be None.'
		super(DnListPropertyEncoder, self).__init__(property_name, *args, **kwargs)
		self._udm = UDM(connection, api_version)

	def _list_of_dns_to_list_of_udm_objects(self, value):
		udm_module = None
		res = []
		for dn in value:
			try:
				if self.udm_module_name == 'auto':
					obj = self.udm.obj_by_dn(dn)
				else:
					if not udm_module:
						udm_module = self.udm.get(self.udm_module_name)
					obj = udm_module.get(dn)
			except UnknownModuleType as exc:
				UDebug.warn(str(exc))
			except NoObject as exc:
				UDebug.warn(str(exc))
			else:
				res.append(obj)
		return res

	def decode(self, value=None):
		if value is None:
			return value
		else:
			assert hasattr(value, '__iter__'), 'Value is not iterable: {!r}'.format(value)
			new_list = self.DnsList(value)
			new_list.objs = self.MyProxy(lambda: self._list_of_dns_to_list_of_udm_objects(value))
			return new_list

	@staticmethod
	def encode(value=None):
		try:
			del value.objs
		except AttributeError:
			pass
		return value

	@property
	def udm(self):
		return self._udm


class CnameListPropertyEncoder(DnListPropertyEncoder):
	"""
	Given a list of CNAMEs, return the same list with an additional member
	``objs``. ``objs`` is a lazy object that will become the list of UDM
	objects the CNAMEs refer to, when accessed.
	"""
	udm_module_name = 'dns/alias'

	def _list_of_dns_to_list_of_udm_objects(self, value):
		udm_module = self.udm.get(self.udm_module_name)
		return [list(udm_module.search('relativeDomainName={}'.format(cname)))[0] for cname in value]


class DnsEntryZoneAliasListPropertyEncoder(DnListPropertyEncoder):
	"""
	Given a list of dnsEntryZoneAlias entries, return the same list with an
	additional member ``objs``. ``objs`` is a lazy object that will become
	the list of UDM objects the dnsEntryZoneAlias entries refer to, when
	accessed.
	"""
	udm_module_name = 'dns/alias'

	def _list_of_dns_to_list_of_udm_objects(self, value):
		udm_module = self.udm.get(self.udm_module_name)
		return [udm_module.get('relativeDomainName={},{}'.format(v[2], v[1])) for v in value]


class DnsEntryZoneForwardListMultiplePropertyEncoder(DnListPropertyEncoder):
	"""
	Given a list of dnsEntryZoneForward entries, return the same list with an
	additional member ``objs``. ``objs`` is a lazy object that will become
	the list of UDM objects the dnsEntryZoneForward entries refer to, when
	accessed.
	"""
	udm_module_name = 'dns/forward_zone'

	@staticmethod
	def _itemgetter(value):
		return value[0]

	def _list_of_dns_to_list_of_udm_objects(self, value):
		udm_module = self.udm.get(self.udm_module_name)
		return [udm_module.get(self._itemgetter(v)) for v in value]


class DnsEntryZoneForwardListSinglePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
	"""
	Given a list of dnsEntryZoneForward entries, return the same list with an
	additional member ``objs``. ``objs`` is a lazy object that will become
	the list of UDM objects the dnsEntryZoneForward entries refer to, when
	accessed.
	"""
	udm_module_name = 'dns/forward_zone'

	@staticmethod
	def _itemgetter(value):
		return value


class DnsEntryZoneReverseListMultiplePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
	"""
	Given a list of dnsEntryZoneReverse entries, return the same list with an
	additional member ``objs``. ``objs`` is a lazy object that will become
	the list of UDM objects the dnsEntryZoneReverse entries refer to, when
	accessed.
	"""
	udm_module_name = 'dns/reverse_zone'

	@staticmethod
	def _itemgetter(value):
		return value[0]


class DnsEntryZoneReverseListSinglePropertyEncoder(DnsEntryZoneReverseListMultiplePropertyEncoder):
	"""
	Given a list of dnsEntryZoneReverse entries, return the same list with an
	additional member ``objs``. ``objs`` is a lazy object that will become
	the list of UDM objects the dnsEntryZoneReverse entries refer to, when
	accessed.
	"""
	udm_module_name = 'dns/reverse_zone'

	@staticmethod
	def _itemgetter(value):
		return value


class DnPropertyEncoder(BaseEncoder):
	"""
	Given a DN, return a string object with the DN and an additional member
	``obj``. ``obj`` is a lazy object that will become the UDM object the DN
	refers to, when accessed.

	:py:func:`dn_property_encoder_for()` will dynamically produce
	subclasses of this for every UDM module required.
	"""
	static = False
	udm_module_name = ''

	class DnStr(str):
		# a string with an additional member variable
		obj = None

		def __deepcopy__(self, memodict=None):
			return str(self)

	class MyProxy(lazy_object_proxy.Proxy):
		# overwrite __repr__ for better navigation in ipython
		def __repr__(self, __getattr__=object.__getattribute__):
			return super(DnPropertyEncoder.MyProxy, self).__str__()

	def __init__(self, property_name=None, connection=None, api_version=None, *args, **kwargs):
		assert connection is not None, 'Argument "connection" must not be None.'
		assert api_version is not None, 'Argument "api_version" must not be None.'
		super(DnPropertyEncoder, self).__init__(property_name, *args, **kwargs)
		self._udm = UDM(connection, api_version)

	def _dn_to_udm_object(self, value):
		try:
			if self.udm_module_name == 'auto':
				return self.udm.obj_by_dn(value)
			else:
				udm_module = self.udm.get(self.udm_module_name)
				return udm_module.get(value)
		except UnknownModuleType as exc:
			UDebug.error(str(exc))
		except NoObject as exc:
			UDebug.warn(str(exc))
		return None

	def decode(self, value=None):
		if value in (None, ''):
			return None
		new_str = self.DnStr(value)
		if value:
			new_str.obj = self.MyProxy(lambda: self._dn_to_udm_object(value))
		return new_str

	@staticmethod
	def encode(value=None):
		try:
			del value.obj
		except AttributeError:
			pass
		return value

	@property
	def udm(self):
		return self._udm


def _classify_name(name):
	mod_parts = name.split('/')
	return ''.join('{}{}'.format(mp[0].upper(), mp[1:]) for mp in mod_parts)


def dn_list_property_encoder_for(udm_module_name):
	"""
	Create a (cached) subclass of DnListPropertyEncoder specific for each UDM
	module.

	:param str udm_module_name: name of UDM module (e.g. `users/user`) or
		`auto` if auto-detection should be done. Auto-detection requires one
		additional LDAP-query per object (still lazy though)!
	:return: subclass of DnListPropertyEncoder
	:rtype: type(DnListPropertyEncoder)
	"""
	if udm_module_name not in __dn_list_property_encoder_class_cache:
		cls_name = str('DnListPropertyEncoder{}').format(_classify_name(udm_module_name))
		specific_encoder_cls = type(cls_name, (DnListPropertyEncoder,), {})
		specific_encoder_cls.udm_module_name = udm_module_name
		__dn_list_property_encoder_class_cache[udm_module_name] = specific_encoder_cls
	return __dn_list_property_encoder_class_cache[udm_module_name]


def dn_property_encoder_for(udm_module_name):
	"""
	Create a (cached) subclass of DnPropertyEncoder specific for each UDM
	module.

	:param str udm_module_name: name of UDM module (e.g. `users/user`) or
		`auto` if auto-detection should be done. Auto-detection requires one
		additional LDAP-query per object (still lazy though)!
	:return: subclass of DnPropertyEncoder
	:rtype: type(DnPropertyEncoder)
	"""
	if udm_module_name not in __dn_property_encoder_class_cache:
		cls_name = str('DnPropertyEncoder{}').format(_classify_name(udm_module_name))
		specific_encoder_cls = type(cls_name, (DnPropertyEncoder,), {})
		specific_encoder_cls.udm_module_name = udm_module_name
		__dn_property_encoder_class_cache[udm_module_name] = specific_encoder_cls
	return __dn_property_encoder_class_cache[udm_module_name]
