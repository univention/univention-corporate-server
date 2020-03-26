# -*- coding: utf-8 -*-
"""
Functions to map between |UDM| properties and |LDAP| attributes.
"""
# Copyright 2004-2020 Univention GmbH
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

from __future__ import absolute_import

import six
import inspect

import univention.debug as ud
import base64
try:
	from typing import List, Text, Tuple, TypeVar, Union  # noqa F401
	_E = TypeVar('_E')
except ImportError:
	pass

getfullargspec = getattr(inspect, 'getfullargspec', inspect.getargspec)

try:
	unicode
except NameError:
	unicode = str


def DaysToSeconds(days):
	# type: (str) -> str
	"""
	Convert number of days to seconds.

	:param day: the number of days.
	:returns: the number of seconds.

	>>> DaysToSeconds('1')
	'86400'
	"""
	return str(int(days) * 24 * 60 * 60)


def SecondsToDays(seconds):
	# type: (str) -> str
	"""
	Convert number of seconds to number of complete days.

	:param seconds: 1-tuple with the number of seconds.
	:returns: the number of complete days.

	>>> SecondsToDays(('86401',))
	'1'
	"""
	return str((int(seconds[0])) // (60 * 60 * 24))


def StringToLower(string):
	# type: (str) -> str
	"""
	Convert string to lower-case.

	:param string: a string.
	:returns: the lower-cased string.

	>>> StringToLower("Aa")
	'aa'
	"""
	return string.lower()


def ListUniq(list):
	# type: (List[_E]) -> List[_E]
	"""
	Return list of unique items.

	:param list: A list of elements.
	:returns: a list with duplicate elements removed.

	>>> ListUniq(['1', '1', '2'])
	['1', '2']
	"""
	result = []  # type: List[_E]
	if list:
		for element in list:
			if element not in result:
				result.append(element)
	return result


def ListToString(value, encoding=()):
	# type: (List[str]) -> str
	"""
	Return first element from list.
	This is right mapping for single-valued properties, as |LDAP| always returns lists of values.

	:param list: A list of elements.
	:returns: the first element or the empty string.

	>>> ListToString([])
	''
	>>> ListToString(['value'])
	'value'
	"""
	if value:
		return value[0].decode(*encoding)
	else:
		return u''


def ListToIntToString(list_):
	# type: (List[str]) -> str
	"""
	Return first element from list if it is an integer.

	:param list: A list of elements.
	:returns: the first element or the empty string.

	>>> ListToIntToString([])
	''
	>>> ListToIntToString(['1'])
	'1'
	"""
	if list_:
		try:
			return str(int(list_[0]))
		except (ValueError, TypeError):
			pass
	return ''


def ListToLowerString(list):
	# type: (List[str]) -> str
	"""
	Return first element from list lower-cased.

	:param list: A list of elements.
	:returns: the first element lower-cased or the empty string.

	>>> ListToLowerString([])
	''
	>>> ListToLowerString(['Value'])
	'value'
	"""
	return StringToLower(ListToString(list))


def ListToLowerList(list):
	# type: (List[str]) -> List[str]
	"""
	Return the list with all elements converted to lower-case.

	:param list: A list of elements.
	:returns: a list of the elemets converted to lower case.

	>>> ListToLowerList(['A', 'a'])
	['a', 'a']
	"""
	return [StringToLower(string) for string in list]


def ListToLowerListUniq(list):
	# type: (List[str]) -> List[str]
	"""
	Return the list with all elements converted to lower-case and duplicates removed.

	:param list: A list of elements.
	:returns: a list of the elemets converted to lower case with duplicates removed.

	>>> ListToLowerListUniq(['A', 'a'])
	['a']
	"""
	return ListUniq(ListToLowerList(list))


def nothing(a):
	"""
	'Do nothing' mapping returning `None`.
	"""
	pass


def IgnoreNone(list):
	# type: (str) -> Union[None, str]
	"""
	Return the value if it is not the sting `None`.

	:param list: Some element(s).
	:returns: The element(s) if it is not `None`.

	>>> IgnoreNone('1')
	'1'
	>>> IgnoreNone('None')
	"""
	if list != 'None':
		return list


def _stringToInt(value):
	# type: (str) -> int
	"""
	Try to convert string into integer.

	:param value: a srting.
	:returns: the integer value or `0`.

	>>> _stringToInt('1')
	1
	>>> _stringToInt('ucs')
	0
	"""
	try:
		return int(value)
	except (ValueError, TypeError):
		return 0


def unmapUNIX_TimeInterval(value):
	# type: (Union[List[str], Tuple[str], str]) -> List[Text]
	"""
	Map number of seconds to a human understandable time interval.

	:param value: number of seconds
	:returns: a 2-tuple (value, unit)

	>>> unmapUNIX_TimeInterval(['0'])
	[u'0', u'days']
	>>> unmapUNIX_TimeInterval(('1',))
	[u'1', u'seconds']
	>>> unmapUNIX_TimeInterval('60')
	[u'1', u'minutes']
	>>> unmapUNIX_TimeInterval('3600')
	[u'1', u'hours']
	>>> unmapUNIX_TimeInterval('86400')
	[u'1', u'days']
	"""
	if isinstance(value, (list, tuple)):
		value = value[0]
	value = _stringToInt(value)
	unit = u'seconds'
	if value % 60 == 0:
		value //= 60
		unit = u'minutes'
		if value % 60 == 0:
			value //= 60
			unit = u'hours'
			if value % 24 == 0:
				value //= 24
				unit = u'days'
	return [unicode(value), unit]


def mapUNIX_TimeInterval(value):
	# type: (Union[List[str], Tuple[str], str]) -> Text
	"""
	Unmap a human understandable time interval back to number of seconds.

	:param value: a 2-tuple (value, unit)
	:returns: the number of seconds.

	>>> mapUNIX_TimeInterval(0)
	'0'
	>>> mapUNIX_TimeInterval([1, 'days'])
	'86400'
	>>> mapUNIX_TimeInterval((1, 'hours'))
	'3600'
	>>> mapUNIX_TimeInterval((1, 'minutes'))
	'60'
	"""
	unit = 'seconds'
	if isinstance(value, (tuple, list)):
		if len(value) > 1:
			unit = value[1]
		value = value[0]
	value = _stringToInt(value)
	if unit == u'days':
		value *= 24 * 60 * 60
	elif unit == u'hours':
		value *= 60 * 60
	elif unit == u'minutes':
		value *= 60
	return unicode(value).encode('ASCII')


def unmapBase64(value):
	"""
	Convert binary data (as found in |LDAP|) to Base64 encoded |UDM| property value(s).

	:param value: some binary data.
	:returns: the base64 encoded data or the empty string on errors.

	>>> unmapBase64(['a'])
	'YQ=='
	>>> unmapBase64(['a', 'b'])
	['YQ==', 'Yg==']
	>>> unmapBase64([None])
	''
	"""
	if len(value) > 1:
		try:
			return [base64.b64encode(x).decode('ASCII') for x in value]
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in unmapBase64: %s' % e)
	else:
		try:
			return base64.b64encode(value[0]).decode('ASCII')
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in unmapBase64: %s' % e)
	return ""


def mapBase64(value):
	# type: (Union[List[str], str]) -> Union[List[str], str]
	# @overload (List[str]) -> List[str]
	# @overload (str) -> str
	"""
	Convert Base64 encoded |UDM| property values to binary data (for storage in |LDAP|).

	:param value: some base64 encoded value.
	:returns: the decoded binary data.

	>>> mapBase64('*')
	'*'
	>>> mapBase64(['YQ=='])
	['a']
	>>> mapBase64('YQ==')
	'a'
	"""
	if value == '*':
		# special case for filter pattern '*'
		return value
	if isinstance(value, list):
		try:
			return map(base64.b64decode, value)
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in mapBase64: %s' % e)
	else:
		try:
			return base64.b64decode(value)
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in mapBase64: %s' % e)
	return ""


def BooleanListToString(list, encoding=()):
	# type: (List[str]) -> str
	"""
	Convert |LDAP| boolean to |UDM|.

	:param list: list of |LDAP| attribute values.
	:returns: the empty string for `False` or otherwise the first element.

	>>> BooleanListToString(['0'])
	''
	>>> BooleanListToString(['1'])
	'1'
	"""
	v = ListToString(list, encoding=encoding)
	if v == u'0':
		return u''
	return v


def BooleanUnMap(value, encoding=()):
	# type: (str) -> str
	"""
	Convert |UDM| boolean to |LDAP|.

	:param list: One |LDAP| attribute values.
	:returns: the empty string for `False` or otherwise the first element.

	>>> BooleanUnMap('0')
	''
	>>> BooleanUnMap('1')
	'1'
	"""
	if value == u'0':
		return b''
	return value.encode(*encoding)


class dontMap(object):
	"""
	'Do nothing' mapping.
	"""
	pass


class mapping(object):
	"""
	Map |LDAP| attribute names and values to |UDM| property names and values and back.
	"""

	def __init__(self):
		self._map = {}
		self._unmap = {}
		self._map_func = {}
		self._unmap_func = {}
		self._map_encoding = {}
		self._unmap_encoding = {}

	def register(self, map_name, unmap_name, map_value=None, unmap_value=None, encoding='UTF-8', encoding_errors='strict'):
		"""
		Register a new mapping.

		:param map_name: |UDM| property name.
		:param unmap_name: |LDAP| attribute name.
		:param map_value: function to map |UDM| property values to |LDAP| attribute values.
		:param unmap_value: function to map |LDAP| attribute values to |UDM| property values.
		"""
		self._map[map_name] = (unmap_name, map_value)
		self._unmap[unmap_name] = (map_name, unmap_value)
		self._map_encoding[map_name] = (encoding, encoding_errors)
		self._unmap_encoding[unmap_name] = (encoding, encoding_errors)

	def unregister(self, map_name, pop_unmap=True):
		# type: (str, bool) -> None
		"""
		Remove a mapping |UDM| to |LDAP| (and also the reverse).

		:param map_name: |UDM| property name.
		:param pop_unmap: `False` prevents the removal of the mapping from |LDAP| to |UDM|, which the default `True` also does.
		"""
		# unregister(pop_unmap=False) is used by LDAP_Search syntax classes with viewonly=True.
		# See SimpleLdap._init_ldap_search().
		unmap_name, map_value = self._map.pop(map_name, [None, None])
		self._map_encoding.pop(map_name, None)
		if pop_unmap:
			self._unmap.pop(unmap_name, None)
			self._unmap_encoding.pop(unmap_name, None)

	def registerUnmapping(self, unmap_name, unmap_value, encoding='UTF-8', encoding_errors='strict'):
		"""
		Register a new unmapping from |LDAP| to |UDM|.

		:param unmap_name: |LDAP| attribute name.
		:param unmap_value: function to map |LDAP| attribute values to |UDM| property values.
		"""
		self._unmap_func[unmap_name] = unmap_value
		self._unmap_encoding[unmap_name] = (encoding, encoding_errors)

	def mapName(self, map_name):
		"""
		Map |UDM| property name to |LDAP| attribute name.

		>>> map = mapping()
		>>> map.mapName('unknown')
		''
		>>> map.register('udm', 'ldap')
		>>> map.mapName('udm')
		'ldap'
		"""
		return self._map.get(map_name, [''])[0]

	def unmapName(self, unmap_name):
		"""
		Map |LDAP| attribute name to |UDM| property name.

		>>> map = mapping()
		>>> map.unmapName('unknown')
		''
		>>> map.register('udm', 'ldap')
		>>> map.unmapName('ldap')
		'udm'
		"""
		return self._unmap.get(unmap_name, [''])[0]

	def mapValue(self, map_name, value):
		"""
		Map |UDM| property value to |LDAP| attribute value.

		>>> map = mapping()
		>>> map.mapValue('unknown', None) #doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		...
		KeyError:
		>>> map.register('udm', 'ldap')
		>>> map.mapValue('udm', 'value')
		'value'
		>>> map.register('udm', 'ldap', lambda udm: udm.lower(), None)
		>>> map.mapValue('udm', None)
		''
		>>> map.mapValue('udm', [0])
		''
		>>> map.mapValue('udm', 'UDM')
		'udm'
		>>> map.register('sambaLogonHours', 'ldap')
		>>> map.mapValue('sambaLogonHours', [0])
		[0]
		"""
		map_value = self._map[map_name][1]

		if not value:
			return b''

		if not any(value) and map_name != 'sambaLogonHours':
			# sambaLogonHours might be [0], see Bug #33703
			return b''

		encoding, strictness = self._map_encoding.get(map_name, ('UTF-8', 'strict'))
		kwargs = {}
		if map_value and 'encoding' in getfullargspec(map_value).args:
			kwargs['encoding'] = (encoding, strictness)

		if six.PY3 and not map_value:
			if isinstance(value, (list, tuple)):
				# FIXME: properties that have not been unmapped e.g. via ListToString (like 'secretary') end up as Lists in diff_ml:
				value = [x.encode(encoding, strictness) for x in value]
			else:
				value = value.encode(encoding, strictness)
		return map_value(value, **kwargs) if map_value else value

	def unmapValue(self, unmap_name, value):
		"""
		Map |LDAP| attribute value to |UDM| property value.

		>>> map = mapping()
		>>> map.unmapValue('unknown', None) #doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		...
		KeyError:
		>>> map.register('udm', 'ldap')
		>>> map.unmapValue('ldap', 'value')
		'value'
		>>> map.register('udm', 'ldap', None, lambda ldap: ldap.upper())
		>>> map.unmapValue('ldap', 'ldap')
		'LDAP'
		"""
		unmap_value = self._unmap[unmap_name][1]

		encoding, strictness = self._unmap_encoding.get(unmap_name, ('UTF-8', 'strict'))
		kwargs = {}
		if unmap_value and 'encoding' in getfullargspec(unmap_value).args:
			kwargs['encoding'] = (encoding, strictness)

		if six.PY3 and not unmap_value:
			value = [val.decode(encoding, strictness) for val in value]
		return unmap_value(value, **kwargs) if unmap_value else value

	def unmapValues(self, oldattr):
		"""
		Unmaps |LDAP| attribute values to |UDM| property values.
		"""
		info = mapDict(self, oldattr)
		for key, func in self._unmap_func.items():
			kwargs = {}
			if 'encoding' in getfullargspec(func).args:
				kwargs['encoding'] = self._unmap_encoding.get(key, ('UTF-8', 'strict'))
			info[key] = func(oldattr, **kwargs)
		return info

	def shouldMap(self, map_name):
		return not isinstance(self._map[map_name][1], dontMap)

	def shouldUnmap(self, unmap_name):
		return not isinstance(self._unmap[unmap_name][1], dontMap)


def mapCmp(mapping, key, old, new):
	"""
	Compare old and new for equality (mapping back to LDAP value if possible).

	>>> map = mapping()
	>>> mapCmp(map, 'unknown', 'old', 'new')
	False
	>>> mapCmp(map, 'unknown', 'same', 'same')
	True
	>>> map.register('udm', 'ldap')
	>>> mapCmp(map, 'udm', 'old', 'new')
	False
	>>> mapCmp(map, 'udm', 'same', 'same')
	True
	>>> map.register('udm', 'ldap', lambda udm: udm.lower(), None)
	>>> mapCmp(map, 'udm', 'case', 'CASE')
	True
	"""
	try:
		map = mapping._map[key]
		if mapping.shouldMap(key) and map[1]:
			return map[1](old) == map[1](new)
		return old == new
	except KeyError:
		return old == new


def mapDict(mapping, old):
	"""
	Convert dictionary mapping LDAP_attriute_name to LDAP_value to a (partial)
	dictionary mapping UDM_property_name to UDM_value.

	>>> map = mapping()
	>>> map.register('udm', 'ldap', None, lambda ldap: ldap.upper())
	>>> mapDict(map, {'ldap': 'ldap', 'unknown': None})
	{'udm': 'LDAP'}
	"""
	new = {}
	if old:
		for key, value in old.items():
			try:
				if not mapping.shouldUnmap(key):
					continue
				k = mapping.unmapName(key)
				v = mapping.unmapValue(key, value)
			except KeyError:
				continue
			new[k] = v
	return new


def mapList(mapping, old):  # UNUSED
	"""
	Convert list of LDAP attribute names to list of UDM property names.

	>>> map = mapping()
	>>> mapList(map, None)
	[]
	>>> mapList(map, ['unknown'])
	['']
	>>> map.register('udm', 'ldap', None, None)
	>>> mapList(map, ['ldap', 'unknown'])
	['udm', '']
	"""
	new = []
	if old:
		for i in old:
			try:
				k = mapping.unmapName(i)
			except KeyError:
				# BUG: never happens because unmapName() returns ''
				continue
			new.append(k)
	return new


def mapDiff(mapping, diff):
	"""
	Convert mod-list of UDM property names/values to mod-list of LDAP attribute names/values.

	>>> map = mapping()
	>>> mapDiff(map, None)
	[]
	>>> mapDiff(map, [('unknown', None, None)])
	[]
	>>> map.register('udm', 'ldap', lambda udm: udm.lower(), None)
	>>> mapDiff(map, [('udm', 'OLD', 'NEW')])
	[('ldap', 'old', 'new')]
	>>> mapDiff(map, [('udm', 'case', 'CASE')])
	[]
	"""
	ml = []
	if diff:
		for key, oldvalue, newvalue in diff:
			try:
				if not mapping.shouldMap(key):
					continue
				k = mapping.mapName(key)
				ov = mapping.mapValue(key, oldvalue)
				nv = mapping.mapValue(key, newvalue)
			except KeyError:
				continue
			if k and ov != nv:
				ml.append((k, ov, nv))
	return ml


def mapDiffAl(mapping, diff):  # UNUSED
	"""
	Convert mod-list of UDM property names/values to add-list of LDAP attribute names/values.

	>>> map = mapping()
	>>> mapDiffAl(map, None)
	[]
	>>> mapDiffAl(map, [('unknown', None, None)])
	[]
	>>> map.register('udm', 'ldap', lambda udm: udm.lower(), None)
	>>> mapDiffAl(map, [('udm', 'OLD', 'NEW'), ('unknown', None, None)])
	[('ldap', 'new')]
	"""
	ml = []
	if diff:
		for key, oldvalue, newvalue in diff:
			try:
				if not mapping.shouldMap(key):
					continue
				k = mapping.mapName(key)
				nv = mapping.mapValue(key, newvalue)
			except KeyError:
				continue
			ml.append((k, nv))
	return ml


def mapRewrite(filter, mapping):
	"""
	Re-write UDM property name/value in UDM filter expression to LDAP attribute name/value.

	>>> from argparse import Namespace
	>>> map = mapping()
	>>> f = Namespace(variable='unknown', value=None); mapRewrite(f, map); (f.variable, f.value)
	('unknown', None)
	>>> map.register('udm', 'ldap', lambda udm: udm.lower(), None)
	>>> f = Namespace(variable='udm', value='UDM'); mapRewrite(f, map); (f.variable, f.value)
	('ldap', 'udm')
	"""
	try:
		key = filter.variable
		if not mapping.shouldMap(key):
			return
		k = mapping.mapName(key)
		v = mapping.mapValue(key, filter.value)
	except KeyError:
		return
	if k:
		filter.variable = k
		filter.value = v


if __name__ == '__main__':
	import doctest
	doctest.testmod()
