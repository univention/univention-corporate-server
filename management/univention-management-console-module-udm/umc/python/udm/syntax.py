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

import copy
import inspect

import univention.admin.syntax as udm_syntax

from ...log import MODULE

class Widget( object ):
	'''Describes a widget for the new web frontend'''

	def __init__( self, name, syntax_classes, default_value, subclasses = True, widget_func = None ):
		self._name = name
		self._syntax_classes = syntax_classes
		self._default_value = default_value
		self._subclasses = subclasses
		self._widget_func = widget_func

	def __contains__( self, syntax ):
		'''Checks if the syntax is represented by this widget'''
		if self._subclasses:
			return isinstance( syntax, self._syntax_classes ) or type( syntax ) in ( type, ) and issubclass( syntax, self._syntax_classes )
		else:
			return inspect.isclass( syntax ) and syntax in self._syntax_classes or type( syntax ) in self._syntax_classes

	def name( self, syntax, udm_property ):
		if self._name is None and callable( self._widget_func ):
			MODULE.info( 'The widget name for syntax %s is %s' % ( syntax.name, self._widget_func( syntax, udm_property ) ) )
			return self._widget_func( syntax, udm_property )
		return self._name

	@property
	def default_value( self ):
		return self._default_value

__widgets = (
	Widget( 'CheckBox', ( udm_syntax.OkOrNot, udm_syntax.TrueFalseUp, udm_syntax.boolean ), False ),
	Widget( 'PasswordInputBox', ( udm_syntax.passwd, udm_syntax.userPasswd ), '' ),
	Widget( 'DateBox', udm_syntax.iso8601Date, '1970-01-01' ),
	Widget( None, ( udm_syntax.LDAP_Search, ), [], subclasses = False, widget_func = lambda syn, prop: syn.viewonly and 'LinkList' or 'ComboBox' ),
	Widget( 'ComboBox', udm_syntax.select, [] ),
	Widget( 'TextBox', ( udm_syntax.ldapDnOrNone, udm_syntax.ldapDn ), '', subclasses = False ),
	Widget( None, udm_syntax.UDM_Modules, '', widget_func = lambda syn, prop: prop[ 'multivalue' ] and 'umc.modules._udm.MultiObjectSelect' or 'ComboBox' ),
	Widget( None, ( udm_syntax.ldapDnOrNone, udm_syntax.ldapDn, udm_syntax.module ), '', widget_func = lambda syn, prop: prop[ 'multivalue' ] and 'umc.modules._udm.MultiObjectSelect' or 'ComboBox' ),
	Widget( 'TextBox', udm_syntax.simple, '*' ),
	Widget( 'MultiInput', udm_syntax.complex, None ),
	)

def choices( syntax, udm_property ):
	"""Returns the choices attribute of the property's syntax as a list
	of dictionaries with id and label keys. If the attribute is not
	available an empty list is returned."""
	MODULE.info( 'Find choices for syntax %s' % syntax )
	if inspect.isclass( syntax ) and issubclass( syntax, ( udm_syntax.ldapDnOrNone, udm_syntax.ldapDn, udm_syntax.UDM_Modules ) ):
		if not udm_property[ 'multivalue' ]:
			return { 'dynamicValues' : 'udm/syntax/choices', 'dynamicOptions' : { 'syntax' : syntax.__name__ } }
		else:
			if syntax not in ( udm_syntax.ldapDnOrNone, udm_syntax.ldapDn ):
				return { 'objectType' : syntax.udm_modules[ 0 ] }
			return {}
	if isinstance( syntax, ( udm_syntax.ldapDnOrNone, udm_syntax.ldapDn ) ):
		return { 'dynamicValues' : 'udm/syntax/choices', 'dynamicOptions' : { 'syntax' : syntax.__class__.__name__ } }

	if isinstance( syntax, udm_syntax.module ):
		return { 'dynamicValues' : 'udm/syntax/choices', 'dynamicOptions' : { 'syntax' : syntax.__class__.__name__, 'options' : { 'module' : syntax.module_type, 'filter' : str( syntax.filter ) } } }

	if inspect.isclass( syntax ) and issubclass( syntax, udm_syntax.select ) and hasattr( syntax, 'udm_modules' ):
		return { 'dynamicValues' : 'udm/syntax/choices', 'dynamicOptions' : { 'syntax' : syntax.name } }

	if isinstance( syntax, udm_syntax.LDAP_Search ):
		return { 'dynamicValues' : 'udm/syntax/choices', 'dynamicOptions' : { 'syntax' : syntax.__class__.__name__, 'options' : { 'syntax' : syntax.name, 'filter' : syntax.filter, 'viewonly' : syntax.viewonly, 'base' : syntax.base, 'value' : syntax.value, 'attributes' : syntax.attributes, 'empty' : syntax.addEmptyValue } } }

	if inspect.isclass( syntax ) and issubclass( syntax, udm_syntax.select ) and hasattr( syntax, 'depends' ):
		return { 'dynamicValues' : 'javascript:umc.modules._udm.setDynamicValues', 'depends': syntax.depends }

	return { 'staticValues' : map( lambda x: { 'id' : x[ 0 ], 'label' : x[ 1 ] }, getattr( syntax, 'choices', [] ) ) }

def subsyntaxes( syntax, udm_property ):
	"""Returns a list of dictionaries describing the the sub types of a
	complex syntax"""
	udm_prop = copy.copy( udm_property )
	udm_prop[ 'multivalue' ] = False
	def subtypes_dict( item ):
		elem = widget( item[ 1 ], udm_prop )
		elem[ 'label' ] = item[ 0 ]
		return elem

	return map( subtypes_dict, getattr( syntax, 'subsyntaxes', [] ) )

def widget( syntax, udm_property ):
	"""Returns a widget description as a dictionary"""
	global __widgets

	for widget in __widgets:
		if syntax in widget:
			descr = { 'type' : widget.name( syntax, udm_property ) }
			values = choices( syntax, udm_property )
			subtypes = subsyntaxes( syntax, udm_property )
			if values:
				MODULE.info( "Syntax %s has the following choices: %s" % ( syntax.name, values ) )
				descr.update( values )
			if subtypes:
				MODULE.info( "Syntax %s has the following sub-types: %s" % ( syntax.name, subtypes ) )
				descr[ 'subtypes' ] = subtypes
			return descr

	if hasattr( syntax, '__name__' ):
		name = syntax.__name__
	elif hasattr( syntax, '__class__' ):
		name = syntax.__class__.__name__
	else:
		name = "Unknown class (name attribute :%s)" % syntax.name
	MODULE.error( 'Could not convert UDM syntax %s' % name )

	return {}

def default_value( syntax ):
	"""Returns a default search pattern/value for the given widget"""
	global __widgets

	for widget in __widgets:
		if syntax in widget:
			return widget.default_value

	return '*'
