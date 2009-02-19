# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  mappings
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import univention.debug

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

