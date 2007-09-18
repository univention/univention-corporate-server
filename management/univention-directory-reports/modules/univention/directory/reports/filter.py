# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
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

import univention.admin.syntax as ua_syntax

from locales import *

__all__ = [ 'filter_add', 'filter_get' ]

_filters = []

def filter_add( types, func ):
	_filters.append( ( types, func ) )

def filter_get( prop_type ):
	for types, func in _filters:
		if isinstance( prop_type, types ):
			return func
	return None

def _boolean_filter( prop, key, value ):
	if value and value.lower() in ( '1', 'yes', 'true' ):
		return ( key, _( 'Yes' ) )
	else:
		return ( key, _( 'No' ) )

filter_add( ( ua_syntax.boolean, ua_syntax.TrueFalseUp, ua_syntax.TrueFalse,
			  ua_syntax.TrueFalseUpper, ua_syntax.OkOrNot ), _boolean_filter )

def _email_address( prop, key, value ):
	if prop.multivalue:
		value = [ '\mbox{%s}' % val for val in value ]
	else:
		value = '\mbox{%s}' % value
	return ( key, value )

filter_add( ( ua_syntax.emailAddress, ), _email_address )

def _samba_group_type( prop, key, value ):
	types = { '2' : _( 'Domain Group' ),
			  '3' : _( 'Local Group' ),
			  '5' : _( 'Well-Known Group' ) }
	if value in types.keys():
		value = types[ value ]
	return ( key, value )

filter_add( ( ua_syntax.sambaGroupType, ), _samba_group_type )
