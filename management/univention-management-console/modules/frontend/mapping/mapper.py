#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  dynamic dialog elements that may change
#
# Copyright 2007-2010 Univention GmbH
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

