#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
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

import univention.management.console.tools as umc_tools

import univention.debug as ud

from uniparts import *

img_minus = umc_tools.image_get( 'actions/minus', umc_tools.SIZE_TINY )
img_plus = umc_tools.image_get( 'actions/plus', umc_tools.SIZE_TINY )

def attributes( umcp_part ):
	# check attributes
	if umcp_part.has_attributes():
		return umcp_part.attributes()
	return {}

def default( umcp_part ):
	# default value to use
	if getattr( umcp_part, 'cached', None ):
		return umcp_part.cached
	elif getattr( umcp_part, 'default', None ):
		return umcp_part.default

	return None

def layout_attrs( storage, umcp_part, default_type = None ):
	args = storage.create_tag_attributes( umcp_part, default_type = default_type )
	if not isinstance( umcp_part, basestring ) and umcp_part.has_attributes():
		attrs = umcp_part.attributes()
		for key in ( 'valign', 'colspan', 'rowspan', 'align', 'type', 'width', 'warning', 'onmouseover', 'onmouseout', 'class' ):
			if attrs.has_key( key ):
				args[ key ] = attrs[ key ]
	return args

def check_syntax( umcp, value ):
	if not umcp.syntax:
		return True
	return umcp.syntax.is_valid( value )

def convert( umcp, value ):
	return umcp.syntax.convert( value )

def __icon_button( image, text, size = umc_tools.SIZE_SMALL ):
	icon = { 'icon' : umc_tools.image_get( image, size ) }
	return button( '', icon, { 'helptext' : text } )

def button_add( what = None ):
	if what:
		return __icon_button( 'actions/add', 'Add %s' % what )
	else:
		return __icon_button( 'actions/add', 'Add' )

def button_remove( what = None ):
	if what:
		return __icon_button( 'actions/remove', 'Remove %s' % what )
	else:
		return __icon_button( 'actions/remove', 'Remove' )

def button_up():
	return __icon_button( 'actions/up', 'Up' )

def button_down():
	return __icon_button( 'actions/down', 'Down' )

def button_left( what = None ):
	if what:
		return __icon_button( 'actions/left', what )
	else:
		return __icon_button( 'actions/left', 'Left' )

def button_right( what = None ):
	if what:
		return __icon_button( 'actions/right', what )
	else:
		return __icon_button( 'actions/right', 'Right' )

def button_search( what = None ):
	return __icon_button( 'actions/search', 'Search', umc_tools.SIZE_MEDIUM )
