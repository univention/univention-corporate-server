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

import operator

import univention.admin.modules as udm_modules
import univention.admin.uldap as udm_uldap
import univention.admin.syntax as udm_syntax

from ...config import ucr
from ...log import MODULE

# global LDAP connection
_ldap_connection = None
_ldap_position = udm_uldap.position( ucr.get( 'ldap/base' ) )

udm_modules.update()

def get_ldap_connection():
	global _ldap_connection, _ldap_position

	if _ldap_connection is not None:
		return _ldap_connection, _ldap_position

	if ucr.get( 'server/role' ) in ( 'domaincontroller_master', 'domaincontroller_backup' ):
		_ldap_connection, _ldap_position = udm_uldap.getAdminConnection()
	else:
		_ldap_connection, _ldap_position = udm_uldap.getMachineConnection()

	return _ldap_connection, _ldap_position

class UDM_Module( object ):
	def __init__( self, module ):
		self.load( module )

	def load( self, module, template_object = None ):
		self.module = udm_modules.get( module )
		if self.module is None:
			return self.module

		lo, po = get_ldap_connection()

		udm_modules.init( lo, po, self.module, template_object )

	def get_default_values( self, property_name ):
		MODULE.info( 'Searching for property %s' % property_name )
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == property_name:
				MODULE.info( 'Found property with syntax %s' % str( type( prop.syntax ) ) )
				if isinstance( prop.syntax, ( udm_syntax.boolean, udm_syntax.TrueFalseUp ) ):
					return False
				elif isinstance( prop.syntax, udm_syntax.simple ):
					return '*'
				elif isinstance( prop.syntax, udm_syntax.select ):
					return prop.syntax.choices
				else:
					return '*'

	def search( self, container, attribute, value ):
		lo, po = get_ldap_connection()
		if container == 'all':
			container = po.getBase()
		return self.module.lookup( None, lo, '%s=%s' % ( attribute, value ), base = container )

	@property
	def identifies( self ):
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if prop.identifies:
				return key
		return None

	@property
	def child_modules( self ):
		if self.module is None:
			return None
		MODULE.info( 'Collecting child modules ...' )
		children = getattr( self.module, 'childmodules', None )
		if children is None:
			MODULE.info( 'No child modules were found' )
			return []
		modules = []
		for child in children:
			mod = udm_modules.get( child )
			if not mod:
				continue
			MODULE.info( 'Found module %s' % str( mod ) )
			modules.append( { 'id' : child, 'label' : getattr( mod, 'short_description', child ) } )
		return modules

	@property
	def layout( self ):
		tabs = []
		for tab in getattr( self.module, 'layout', [] ):
			data = { 'name' : tab.short_description, 'description' : tab.long_description, 'layout' : [] }
			for item in tab.fields:
				data[ 'layout' ].append( [ field.property for field in item ] )
			tabs.append( data )
		return tabs

	@property
	def property_names( self ):
		props = []
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == 'filler' or prop.dontsearch: continue
			props.append( { 'id' : key, 'label' : prop.short_description } )
		props.sort( key = operator.itemgetter( 'id' ) )
		return props

	@property
	def properties( self ):
		props = []
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			item = { 'id' : key, 'label' : prop.short_description, 'description' : prop.long_description,
					 'required' : prop.required in ( 1, True ), 'editable' : prop.may_change in ( 1, True ),
					 'options' : prop.options }
			if isinstance( prop.syntax, ( udm_syntax.boolean, udm_syntax.TrueFalseUp ) ):
				item[ 'type' ] = 'CheckBox'
			elif isinstance( prop.syntax, ( udm_syntax.passwd, udm_syntax.userPasswd ) ):
				item[ 'type' ] = 'PasswordBox'
			if isinstance( prop.syntax, udm_syntax.simple ):
				item[ 'type' ] = 'TextBox'
			elif isinstance( prop.syntax, udm_syntax.select ):
				item[ 'type' ] = 'ComboBox'
				item[ 'staticValues' ] = map( lambda x: { 'id' : x[ 0 ], 'label' : x[ 1 ] }, prop.syntax.choices )
			else:
				if hasattr( prop.syntax, '__name__' ):
					name = prop.syntax.__name__
				elif hasattr( prop.syntax, '__class__' ):
					name = prop.syntax.__class__.__name__
				else:
					name = "Unknown class (name attribute :%s)" % prop.name
				MODULE.error( 'Could not convert UDM syntax %s' % name )
				item[ 'type' ] = None
			props.append( item )
		props.sort( key = operator.itemgetter( 'label' ) )
		return props

	@property
	def options( self ):
		opts = []
		for key, option in getattr( self.module, 'options', {} ).items():
			item = { 'id' : key, 'label' : option.short_description, 'default' : option.default }
			opts.append( item )
		opts.sort( key = operator.itemgetter( 'label' ) )
		return opts

	@property
	def operations( self ):
		return self.module is not None and getattr( self.module, 'operations', None )


class UDM_Settings( object ):
	def __init__( self, username ):
		lo, po = get_ldap_connection()
		self.user_dn = lo.searchDn( 'uid=%s' % username, unique = True )
		self.policies = lo.getPolicies( self.user_dn )

		directories = udm_modules.lookup( 'settings/directory', None, lo, scope = 'sub' )
		if not directories:
			self.directory = None
		else:
			self.directory = directories[ 0 ]

	def containers( self, module_name ):
		if module_name.find( '/' ) < 0:
			return []
		base, name = module_name.split( '/', 1 )

		return self.directory[ base ]

	def resultColumns( self, module_name ):
		pass
