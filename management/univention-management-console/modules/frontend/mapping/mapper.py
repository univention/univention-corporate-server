#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  dynamic dialog elements that may change
#
# Copyright (C) 2007 Univention GmbH
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

import univention.debug as ud

_mappers = {}

class IMapper( object ):
	def layout( self, storage, umcp_part ):
		ud.debug(ud.ADMIN, ud.ERROR, 'mapper.py: no layout function defined!')
		pass

	def apply( self, storage, umcp_part, params, *args ):
		ud.debug(ud.ADMIN, ud.ERROR, 'mapper.py: no apply function defined!')
		return False

	def parse( self, storage, umcp_part, params ):
		ud.debug(ud.ADMIN, ud.ERROR, 'mapper.py: no parse function defined!')
		return  None

def add( type, mapper ):
	global _mappers
	_mappers[ type ] = mapper

def exists( type ):
	global _mappers
	return _mappers.has_key( type )

def layout( type, storage, umcp_part ):
	global _mappers
	if _mappers.has_key( type ):
		if isinstance( _mappers[ type ], IMapper ):
			return _mappers[ type ].layout( storage, umcp_part )
		else:
			return _mappers[ type ]( storage, umcp_part )

	ud.debug(ud.ADMIN, ud.ERROR, 'mapper.py: type "%s" in _mappers not found' % type)
	return  None

def apply( type, storage, umcp_part, parameters, *args ):
	global _mappers

	if _mappers.has_key( type ):
		if isinstance( _mappers[ type ], IMapper ):
			return _mappers[ type ].apply( storage, umcp_part, parameters, *args )
	return False

def parse( type, storage, umcp_part, parameters ):
	global _mappers

	if _mappers.has_key( type ):
		if isinstance( _mappers[ type ], IMapper ):
			return _mappers[ type ].parse( storage, umcp_part, parameters )

	return None
