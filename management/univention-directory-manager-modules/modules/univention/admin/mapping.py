# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  mappings
#
# Copyright 2004-2011 Univention GmbH
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

import univention.debug
import types

def DaysToSeconds(days):
	return str(int(days)*24*60*60)

def SecondsToDays(seconds):
	return str((int(seconds[0]))/(60*60*24))

def StringToLower(string):
	return string.lower()

def ListUniq(list):
	result = []
	if list:
		for element in list:
			if not element in result:
				result.append(element)
	return result

def ListToString(list):
	if len(list)>0:
		return list[0]
	else:
		return ''

def ListToLowerString(list):
	return StringToLower(ListToString(list))

def ListToLowerList(list):
	return [ StringToLower(string) for string in list ]

def ListToLowerListUniq(list):
	return ListUniq(ListToLowerList(list))

def nothing(a):
	pass

def IgnoreNone(list):
	if list != 'None':
		return list

def unmapUNIX_TimeInterval( value ):
	if type(value) == types.ListType:
		value = int(value[0])
	else:
		value = int(value)
	unit = 'seconds'
	if value % 60 == 0:
		value /= 60
		unit = 'minutes'
		if value % 60 == 0:
			value /= 60
			unit = 'hours'
			if value % 24 == 0:
				value /= 24
				unit = 'days'
	return [ unicode( value ), unit ]

def mapUNIX_TimeInterval( value ):
	unit = 'seconds'
	if isinstance( value, ( tuple, list ) ):
		if len( value ) > 1:
			unit = value[ 1 ]
		value = int( value[ 0 ] )
	else:
		value = int( value )
	if unit == 'days':
		value *= 24 * 60 * 60
	elif unit == 'hours':
		value *= 60 * 60
	elif unit == 'minutes':
		value *= 60
	return unicode( value )

class mapping:
	def __init__(self):
		self._map={}
		self._unmap={}
	def register(self, map_name, unmap_name, map_value=None, unmap_value=None):
		self._map[map_name]=(unmap_name, map_value)
		self._unmap[unmap_name]=(map_name, unmap_value)
	def unregister(self, map_name):
		if self._map.has_key(map_name):
			del(self._map[map_name])
		else:
			#univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Trying to remove nonexistent key %s'%map_name)
			pass
	def mapName(self, map_name):
		if self._map.has_key(map_name):
			res=self._map[map_name][0]
		else:
			res=''
		#univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'mapping name %s->%s' % (map_name, res))
		return res
	def unmapName(self, unmap_name):
		if self._unmap.has_key(unmap_name):
			res=self._unmap[unmap_name][0]
		else:
			res=''
		return res
	def mapValue(self, map_name, value):
		if not value:
			return ''
		else:
			empty=1
			for v in value:
				if v:
					empty=0
			if empty:
				return ''

		if self._map[map_name][1]:
			res=self._map[map_name][1](value)
		else:
			res=value
		return res
	def unmapValue(self, unmap_name, value):
		if self._unmap[unmap_name][1]:
			res=self._unmap[unmap_name][1](value)
		else:
			res=value
		return res

def mapCmp(mapping, key, old, new):
	try:
		map = mapping._map[key]
		if map[1]:
			return map[1](old) == map[1](new)
		return old == new
	except KeyError:
		return old == new

def mapDict(mapping, old):
	new={}
	if old:
		for key, value in old.items():
			try:
				k=mapping.unmapName(key)
				v=mapping.unmapValue(key, value)
			except KeyError:
				continue
			new[k]=v
	return new

def mapList(mapping, old):
	new=[]
	if old:
		for i in old:
			try:
				k=mapping.unmapName(i)
			except KeyError:
				continue
			new.append(k)
	return new

def mapDiff(mapping, diff):
	ml=[]
	if diff:
		for key, oldvalue, newvalue in diff:
			try:
				k=mapping.mapName(key)
				ov=mapping.mapValue(key, oldvalue)
				nv=mapping.mapValue(key, newvalue)
			except KeyError:
				continue
			if k:
				ml.append((k, ov, nv))
	return ml

def mapDiffAl(mapping, diff):
	ml=[]
	if diff:
		for key, oldvalue, newvalue in diff:
			try:
				k=mapping.mapName(key)
				nv=mapping.mapValue(key, newvalue)
			except KeyError:
				continue
			ml.append((k, nv))
	return ml

def mapRewrite(filter, mapping):
	try:
		k=mapping.mapName(filter.variable)
		v=mapping.mapValue(filter.variable, filter.value)
	except KeyError:
		return
	filter.variable=k
	filter.value=v

