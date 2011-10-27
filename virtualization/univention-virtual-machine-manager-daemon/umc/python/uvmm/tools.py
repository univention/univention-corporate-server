#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010 Univention GmbH
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

def object2dict( obj, convert_attrs = [] ):
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

class VirtTech( object ):
	def __init__( self, virttech = None ):
		self.reset()
		if virttech:
			self.__call__( virttech )

	def reset( self ):
		self.domain = None
		self.os = None

	def __call__( self, virttech ):
		if virttech == None:
			self.reset()
			return
		if virttech.find( '-' ) < 0:
			raise AttributeError( 'wrong format of attribute' )
		self.domain, self.os = virttech.split( '-', 1 )

	def pv( self ):
		return self.os in ( 'xen', 'linux' )

	def hvm( self ):
		return self.os == 'hvm'

class ddict(dict):
	"""Wrapper for dictionary with default value for unset keys."""
	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
	def __getitem__(self, key):
		return self.get(key, '<UNSET>')

if __name__ == '__main__':
	import doctest
	doctest.testmod()
