# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2014 Univention GmbH
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

from types import BuiltinMethodType, MethodType, FunctionType, TypeType, NoneType

import re

BASE_TYPES = (int, float, long, bool, basestring, NoneType, list, tuple)

def object2dict(obj):
	"""
	Converts the attributes of an object to a dictionary.
	"""
	if isinstance(obj, BASE_TYPES):
		return obj
	attrs = {}
	for slot in obj.__dict__:
		if slot.startswith('__') and slot.endswith('__'):
			continue
		attr = getattr(obj, slot)
		if isinstance(attr, (BuiltinMethodType, MethodType, FunctionType, TypeType)):
			continue
		if isinstance(attr, (int, float, long, bool, NoneType)):
			attrs[slot] = attr
		elif isinstance(attr, basestring):
			if attr in ('0', 'FALSE'):
				attr = False
			elif attr in ('1', 'TRUE'):
				attr = True
			attrs[slot] = attr
		elif isinstance(attr, (list, tuple)):
			attrs[slot] = [object2dict(_) for _ in attr]
		elif isinstance(attr, dict):
			attrs[slot] = dict([
				(key, object2dict(value))
				for key, value in attr.items()
				])
		else:
			attrs[slot] = object2dict(attr)

	return attrs


class MemorySize(object):
	"""
	Parse and convert size with optional prefix from and to numbers.
	"""
	UNITS = ('', 'K', 'M', 'G', 'T', 'P')
	SIZE_REGEX = re.compile(
			r'''
			^\s*
			(?P<size>[0-9]+(?:[,.][0-9]+)?)
			\s*
			(?:(?P<unit>[%s])(?:I?B)?|B)?
			\s*$
			''' % (''.join(UNITS),),
			re.IGNORECASE | re.VERBOSE
			)

	@staticmethod
	def num2str(size, unit='B'):
		"""
		Pretty-print number to string consisting of size and optional prefix.
		>>> MemorySize.num2str(512)
		'512 B'
		>>> MemorySize.num2str(512, unit='MB')
		'512.0 MB'
		"""
		unit = unit.rstrip('IiBb')
		block_size = 1
		for item in MemorySize.UNITS:
			if item == unit:
				break
			else:
				block_size <<= 10
		size = long(size) * float(block_size)
		unit = 0
		while size > 1024.0 and unit < (len(MemorySize.UNITS) - 1):
			size /= 1024.0
			unit += 1

		if unit > 0:
			return '%.1f %sB' % (size, MemorySize.UNITS[unit])
		else:
			return '%.0f %sB' % (size, MemorySize.UNITS[unit])

	@staticmethod
	def str2num(size, block_size=1, unit='B'):
		"""
		Parse string consisting of size and prefix into number.
		>>> MemorySize.str2num('512')
		512L
		>>> MemorySize.str2num('512 B')
		512L
		>>> MemorySize.str2num('512 M')
		536870912L
		>>> MemorySize.str2num('512 MB')
		536870912L
		>>> MemorySize.str2num('512 MiB')
		536870912L
		>>> MemorySize.str2num('512,0 MB')
		536870912L
		>>> MemorySize.str2num('2.0 GB')
		2147483648L
		>>> MemorySize.str2num('8GB')
		8589934592L
		>>> MemorySize.str2num('2.,0 GB')
		-1
		>>> MemorySize.str2num('2 XB')
		-1
		>>> MemorySize.str2num('2', unit='XB')
		-1
		>>> MemorySize.str2num('2', unit='XX')
		-1
		>>> MemorySize.str2num('2', unit='BI')
		-1
		"""
		match = MemorySize.SIZE_REGEX.match(size)
		if not match:
			return -1 # raise ValueError(size)

		m_size, m_unit = match.groups()
		m_size = m_size.replace(',', '.')
		size = float(m_size)
		if m_unit:
			unit = m_unit.upper()
		unit = unit.rstrip('Bb').rstrip('Ii')
		for _ in MemorySize.UNITS:
			if _ == unit:
				break
			else:
				size *= 1024.0
		else:
			return -1 # raise ValueError(unit)

		return long(size / float(block_size))

	@staticmethod
	def str2str(size, unit='B'):
		"""
		Normalize string consisting of size and prefix.
		>>> MemorySize.str2str('0.5 MB')
		'512.0 KB'
		"""
		num = MemorySize.str2num(size, unit=unit)
		if num == -1:
			return ''
		return MemorySize.num2str(num)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
