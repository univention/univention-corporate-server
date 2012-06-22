# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2012 Univention GmbH
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

from types import BuiltinMethodType, MethodType, FunctionType, TypeType, NoneType, InstanceType

from univention.lib.i18n import Translation

import re
import math

_ = Translation('univention-management-console-modules-uvmm').translate

BASE_TYPES = ( int, float, long, bool, basestring, NoneType, list, tuple )

def object2dict( obj ):
	"""Converts the attributes of an object to a dictionary."""
	if isinstance( obj, BASE_TYPES ):
		return obj
	attrs = {}
	for slot in obj.__dict__:
		if slot.startswith( '__' ) and slot.endswith( '__' ):
			continue
		attr = getattr( obj, slot )
		if not isinstance( attr, ( BuiltinMethodType, MethodType, FunctionType, TypeType ) ):
			if isinstance( attr, ( int, float, long, bool, NoneType ) ):
				attrs[ slot ] = attr
			elif isinstance( attr, basestring ):
				if attr in ( '0', 'FALSE' ):
					attr = False
				elif attr in ( '1', 'TRUE' ):
					attr = True
				attrs[ slot ] = attr
			elif isinstance( attr, ( list, tuple ) ):
				attrs[ slot ] = map( lambda x: object2dict( x ), attr )
			elif isinstance( attr, dict ):
				attrs[ slot ] = dict( map( lambda item: ( item[ 0 ], object2dict( item[ 1 ] ) ), attr.items() ) )
			else:
				attrs[ slot ] = object2dict( attr )

	return attrs

def str2pat( string ):
	if not string:
		return '*'
	if not string[ -1 ] == '*':
		string += '*'
	if not string[ 0 ] == '*':
		string = '*' + string

	return string

class MemorySize( object ):
	"""Parse and convert size with optional prefix from and to numbers."""
	UNITS = ( 'B', 'KB', 'MB', 'GB', 'TB' )
	SIZE_REGEX = re.compile( '^ *(?P<size>[0-9]+(?:[,.][0-9]+)?)[ \t]*(?P<unit>(%s))? *$' % '|'.join( UNITS ) )

	@staticmethod
	def num2str( size, unit = 'B' ):
		"""Pretty-print number to string consisting of size and optional prefix.
		>>> MemorySize.num2str(512)
		'512 B'
		>>> MemorySize.num2str(512, unit='MB')
		'512.0 MB'
		"""
		block_size = 1
		for item in MemorySize.UNITS:
			if item == unit:
				break
			else:
				block_size <<= 10
		size = long( size ) * float( block_size )
		unit = 0
		while size > 1024.0 and unit < ( len( MemorySize.UNITS ) - 1 ):
			size /= 1024.0
			unit += 1

		if unit > 0:
			return '%.1f %s' % ( size, MemorySize.UNITS[ unit ] )
		else:
			return '%.0f %s' % ( size, MemorySize.UNITS[ unit ] )

	@staticmethod
	def str2num( size, block_size = 1, unit = 'B' ):
		"""Parse string consisting of size and prefix into number.
		>>> MemorySize.str2num('512')
		512L
		>>> MemorySize.str2num('512 MB')
		536870912L
		>>> MemorySize.str2num('512,0 MB')
		536870912L
		>>> MemorySize.str2num('2.0 GB')
		2147483648L
		>>> MemorySize.str2num('8GB')
		8589934592L
		>>> MemorySize.str2num('2.,0 GB')
		-1
		"""
		match = MemorySize.SIZE_REGEX.match( size )
		if not match:
			return -1

		grp = match.groupdict()
		grp[ 'size' ] = grp[ 'size' ].replace( ',', '.' )
		size = float( grp[ 'size' ] )
		factor = 0
		if 'unit' in grp and grp[ 'unit' ] in MemorySize.UNITS:
			unit = grp[ 'unit' ]
		while MemorySize.UNITS[ factor ] != unit:
				factor +=1
		size = size * math.pow( 1024, factor )

		return long( size / float( block_size ) )

	@staticmethod
	def str2str( size, unit = 'B' ):
		"""Normalize string consisting of size and prefix.
		>>> MemorySize.str2str('0.5 MB')
		'512.0 KB'
		"""
		num = MemorySize.str2num( size, unit = unit )
		if num == -1:
			return ''
		return MemorySize.num2str( num )

if __name__ == '__main__':
	import doctest
	doctest.testmod()
