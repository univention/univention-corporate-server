# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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
Functions to map between |UDM| properties and |LDAP| attributes.
"""

from __future__ import absolute_import

import inspect
import base64

import univention.debug as ud
import univention.admin.uexceptions
from univention.admin import localization

translation = localization.translation('univention/admin')

_ = translation.translate

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


def MapToBytes(udm_value, encoding=()):
	if isinstance(udm_value, (list, tuple)):
		return [MapToBytes(udm_val, encoding=encoding) for udm_val in udm_value]
	return unicode(udm_value).encode(*encoding)


def UnmapToUnicode(ldap_value, encoding=()):
	if isinstance(ldap_value, (list, tuple)):
		return [UnmapToUnicode(ldap_val, encoding=encoding) for ldap_val in ldap_value]
	return ldap_value.decode(*encoding)


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
	>>> ListToString([b'value'])
	'value'
	"""
	if value:
		return UnmapToUnicode(value, encoding)[0]
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
	>>> ListToIntToString([b'x'])
	''
	>>> ListToIntToString([b'1'])
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
	>>> ListToLowerString([b'Value'])
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


def IgnoreNone(value, encoding=()):
	# type: (str) -> Union[None, str]
	"""
	Return the value if it is not the string `None`.

	:param value: Some element(s).
	:returns: The element(s) if it is not `None`.

	>>> IgnoreNone('1')
	b'1'
	>>> IgnoreNone('None')
	"""
	if value != u'None':
		return value.encode(*encoding)
	return None  # FIXME


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

	>>> unmapUNIX_TimeInterval(['0'])  # doctest: +ALLOW_UNICODE
	['0', 'days']
	>>> unmapUNIX_TimeInterval(('1',))  # doctest: +ALLOW_UNICODE
	['1', 'seconds']
	>>> unmapUNIX_TimeInterval('60')  # doctest: +ALLOW_UNICODE
	['1', 'minutes']
	>>> unmapUNIX_TimeInterval('3600')  # doctest: +ALLOW_UNICODE
	['1', 'hours']
	>>> unmapUNIX_TimeInterval('86400')  # doctest: +ALLOW_UNICODE
	['1', 'days']
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
	b'0'
	>>> mapUNIX_TimeInterval([1, 'days'])
	b'86400'
	>>> mapUNIX_TimeInterval((1, 'hours'))
	b'3600'
	>>> mapUNIX_TimeInterval((1, 'minutes'))
	b'60'
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

	>>> unmapBase64([b'a'])
	'YQ=='
	>>> unmapBase64([b'a', b'b'])
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
	# type: (Union[List[str], str]) -> Union[List[bytes], bytes]
	# @overload (List[str]) -> List[bytes]
	# @overload (str) -> bytes
	"""
	Convert Base64 encoded |UDM| property values to binary data (for storage in |LDAP|).

	:param value: some base64 encoded value.
	:returns: the decoded binary data.

	>>> mapBase64('*')
	'*'
	>>> mapBase64(['YQ=='])
	[b'a']
	>>> mapBase64('YQ==')
	b'a'
	"""
	if value == b'*':
		# special case for filter pattern '*'
		return value
	if isinstance(value, list):
		try:
			return [base64.b64decode(x) for x in value]
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in mapBase64: %s' % e)
	else:
		try:
			return base64.b64decode(value)
		except Exception as e:
			ud.debug(ud.ADMIN, ud.ERROR, 'ERROR in mapBase64: %s' % e)
	return b""


def BooleanListToString(list, encoding=()):
	# type: (List[str]) -> str
	"""
	Convert |LDAP| boolean to |UDM|.

	:param list: list of |LDAP| attribute values.
	:returns: the empty string for `False` or otherwise the first element.

	>>> BooleanListToString([b'0'])
	''
	>>> BooleanListToString([b'1'])
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
	b''
	>>> BooleanUnMap('1')
	b'1'
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
		unmap_name, map_value = self._map.pop(map_name, ('', None))
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
		b'value'
		>>> map.register('udm', 'ldap', lambda udm: udm.lower().encode('utf-8'), None)
		>>> map.mapValue('udm', None)
		b''
		>>> map.mapValue('udm', [0])
		b''
		>>> map.mapValue('udm', 'UDM')
		b'udm'
		>>> map.register('sambaLogonHours', 'ldap')
		>>> map.mapValue('sambaLogonHours', [0])
		[b'0']
		"""
		map_value = self._map[map_name][1]

		if not value:
			return b''

		if not any(value) and map_name != 'sambaLogonHours':
			# sambaLogonHours might be [0], see Bug #33703
			return b''

		encoding, strictness = self._map_encoding.get(map_name, ('UTF-8', 'strict'))
		if not map_value:
			map_value = MapToBytes
		kwargs = {}
		if 'encoding' in getfullargspec(map_value).args:
			kwargs['encoding'] = (encoding, strictness)

		try:
			value = map_value(value, **kwargs)
		except UnicodeEncodeError:
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Invalid encoding for %s') % (map_name,))
		return value

	def mapValueDecoded(self, map_name, value):
		value = self.mapValue(map_name, value)
		if isinstance(value, (list, tuple)):
			ud.debug(ud.ADMIN, ud.WARN, 'mapValueDecoded returns a list for %s. This is probably not wanted?' % map_name)
			value = [val.decode(*self.getEncoding(map_name)) for val in value]
		else:
			value = value.decode(*self.getEncoding(map_name))
		return value

	def unmapValue(self, unmap_name, value):
		"""
		Map |LDAP| attribute value to |UDM| property value.

		>>> map = mapping()
		>>> map.unmapValue('unknown', None) #doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		...
		KeyError:
		>>> map.register('udm', 'ldap')
		>>> map.unmapValue('ldap', b'value')
		'value'
		>>> map.register('udm', 'ldap', None, lambda ldap: ldap.decode('utf-8').upper())
		>>> map.unmapValue('ldap', b'ldap')
		'LDAP'
		"""
		unmap_value = self._unmap[unmap_name][1]
		if not unmap_value:
			unmap_value = UnmapToUnicode

		encoding, strictness = self._unmap_encoding.get(unmap_name, ('UTF-8', 'strict'))
		kwargs = {}
		if 'encoding' in getfullargspec(unmap_value).args:
			kwargs['encoding'] = (encoding, strictness)

		try:
			return unmap_value(value, **kwargs)
		except UnicodeDecodeError:
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Invalid encoding for %s') % (unmap_name,))

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

	def getEncoding(self, map_name):
		return self._map_encoding.get(map_name, self._unmap_encoding.get(map_name, ()))


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
		_, f = mapping._map[key]
		if mapping.shouldMap(key) and f:
			return f(old) == f(new)
		return old == new
	except KeyError:
		return old == new


def mapDict(mapping, old):
	"""
	Convert dictionary mapping LDAP_attriute_name to LDAP_value to a (partial)
	dictionary mapping UDM_property_name to UDM_value.

	>>> map = mapping()
	>>> map.register('udm', 'ldap', None, lambda ldap: ldap.decode('utf-8').upper())
	>>> mapDict(map, {'ldap': b'ldap', 'unknown': None})
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
	>>> map.register('udm', 'ldap', lambda udm: udm.lower().encode('utf-8'), None)
	>>> mapDiff(map, [('udm', 'OLD', 'NEW')])
	[('ldap', b'old', b'new')]
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
	>>> map.register('udm', 'ldap', lambda udm: udm.lower().encode('utf-8'), None)
	>>> mapDiffAl(map, [('udm', 'OLD', 'NEW'), ('unknown', None, None)])
	[('ldap', b'new')]
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
	>>> map.register('udm', 'ldap', lambda udm: udm.lower().encode('utf-8'), None)
	>>> f = Namespace(variable='udm', value='UDM'); mapRewrite(f, map); (f.variable, f.value)
	('ldap', b'udm')
	"""
	try:
		key = filter.variable
		if not mapping.shouldMap(key):
			return
		k = mapping.mapName(key)
		v = mapping.mapValueDecoded(key, filter.value)
	except KeyError:
		return
	if k:
		filter.variable = k
		filter.value = v
