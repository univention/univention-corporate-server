#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011 Univention GmbH
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

import univention.admin.syntax as udm_syntax

from ...log import MODULE

class Widget( object ):
	'''Describes a widget for the new web frontend'''

	def __init__( self, name, syntax_classes, default_value, static_values_func = None ):
		self._name = name
		self._syntax_classes = syntax_classes
		self._default_value = default_value
		self._static_values_func = static_values_func

	def __contains__( self, syntax ):
		return isinstance( syntax, self._syntax_classes )

	def values( self, udm_property ):
		if self._static_values_func is None:
			return ()
		return self._static_values_func( self, udm_property )

	@property
	def name( self ):
		return self._name

	@property
	def default_value( self ):
		return self._default_value

__widgets = (
	Widget( 'CheckBox', ( udm_syntax.OkOrNot, udm_syntax.TrueFalseUp ), False ),
	Widget( 'PasswordInputBox', ( udm_syntax.passwd, udm_syntax.userPasswd ), '' ),
	Widget( 'DateBox', udm_syntax.iso8601Date, '1970-01-01' ),
	Widget( 'TextBox', udm_syntax.simple, '*' ),
	Widget( 'ComboxBox', udm_syntax.select, '', lambda self, udm_property: map( lambda x: { 'id' : x[ 0 ], 'label' : x[ 1 ] }, udm_property.syntax.choices ) )
	)

def widget( udm_property ):
	'''Returns a widget description'''
	global __widgets

	for widget in __widgets:
		if udm_property.syntax in widget:
			return { 'type' : widget.name, 'staticValues' : widget.values( udm_property ) }

	if hasattr( udm_property.syntax, '__name__' ):
		name = udm_property.syntax.__name__
	elif hasattr( udm_property.syntax, '__class__' ):
		name = udm_property.syntax.__class__.__name__
	else:
		name = "Unknown class (name attribute :%s)" % udm_property.name
	MODULE.error( 'Could not convert UDM syntax %s' % name )

	return {}

def default_value( udm_property ):
	'''Returns a widget description'''
	global __widgets

	for widget in __widgets:
		if udm_property.syntax in widget:
			return widget.default_value

	return '*'
