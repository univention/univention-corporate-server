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

from univention.management.console import Translation

import univention.admin as udm
import univention.admin.modules as udm_modules
import univention.admin.uldap as udm_uldap
import univention.admin.syntax as udm_syntax

from ...config import ucr
from ...log import MODULE

from .syntax import widget, default_value

_ = Translation( 'univention-management-console-modules-udm' ).translate

# global LDAP connection
_ldap_connection = None
_ldap_position = udm_uldap.position( ucr.get( 'ldap/base' ) )

udm_modules.update()

# module cache
_modules = {}

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
	UCR_SEARCH_DEFAULT = 'directory/manager/web/modules/%(module)s/search/default'

	def __init__( self, module ):
		self.load( module )

	def load( self, module, template_object = None ):
		global _modules
		if module in _modules:
			self.module = _modules[ module ]
		else:
			_modules[ module ] = udm_modules.get( module )
			if _modules[ module ] is None:
				return None

			lo, po = get_ldap_connection()

			udm_modules.init( lo, po, _modules[ module ], template_object )
			self.module = _modules[ module ]

	def get_default_values( self, property_name ):
		MODULE.info( 'Searching for property %s' % property_name )
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == property_name:
				return default_value( prop.syntax )

	def search( self, container = None, attribute = None, value = None, superordinate = None ):
		lo, po = get_ldap_connection()
		if container == 'all':
			container = po.getBase()
		elif container is None:
			container = ''
		if attribute is None:
			filter_s = ''
		else:
			filter_s = '%s=%s' % ( attribute, value )

		MODULE.info( 'Searching for LDAP objects: container = %s, filter = %s, superordinate = %s' % ( container, filter_s, superordinate ) )
		return self.module.lookup( None, lo, filter_s, base = container, superordinate = superordinate )

	def get( self, ldap_dn ):
		lo, po = get_ldap_connection()
		obj = self.module.object( None, lo, None, ldap_dn )
		obj.open()

		return obj

	@property
	def name( self ):
		return self.module is not None and self.module.module

	@property
	def title( self ):
		return getattr( self.module, 'short_description', self.module.module )

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
		layout = getattr( self.module, 'layout', [] )
		if not layout:
			return layout

		if isinstance( layout[ 0 ], udm.tab ):
			return self._parse_old_layout( layout )

		return self._parse_new_layout( layout )

	def _parse_old_layout( self, layout ):
		tabs = []
		for tab in layout:
			data = { 'name' : tab.short_description, 'description' : tab.long_description, 'advanced' : tab.advanced, 'layout' : [ { 'name' : 'General', 'description' : 'General settings', 'layout' : [] } ] }
			for item in tab.fields:
				line = []
				for field in item:
					if isinstance( field, ( list, tuple ) ):
						elem = [ x.property for x in field ]
					else:
						elem = field.property
					line.append( elem )
				data[ 'layout' ][ 0 ][ 'layout' ].append( line )
			tabs.append( data )
		return tabs

	def _parse_new_layout( self, layout ):
		return layout

	@property
	def password_properties( self ):
		passwords = []
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if prop.syntax in ( udm_syntax.passwd, udm_syntax.userPasswd ):
				passwords.append( key )

		return passwords

	@property
	def properties( self ):
		props = [ { 'id' : 'ldap-dn', 'type' : 'HiddenInput', 'label' : '', 'searchable' : False } ]
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == 'filler': continue
			if hasattr( prop.syntax, '__name__' ):
				syntax_name = prop.syntax.__name__
			elif hasattr( prop.syntax, '__class__' ):
				syntax_name = prop.syntax.__class__.__name__
			else:
				syntax_name = getattr( 'name', prop, None )
			item = { 'id' : key, 'label' : prop.short_description, 'description' : prop.long_description, 'syntax' : syntax_name,
					 'required' : prop.required in ( 1, True ), 'editable' : prop.may_change in ( 1, True ),
					 'options' : prop.options, 'searchable' : not prop.dontsearch, 'multivalue' : prop.multivalue in ( 1, True ) }

			# read UCR configuration
			if ucr.get( UDM_Module.UCR_SEARCH_DEFAULT % { 'module' : self.module.module } ) == key:
				item[ 'preselected' ] = True

			item.update( widget( prop.syntax ) )
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

	@property
	def template( self ):
		return getattr( self.module, 'template', None )

	@property
	def containers( self ):
		containers = getattr( self.module, 'default_containers', [] )
		ldap_base = ucr.get( 'ldap/base' )

		return map( lambda x: { 'id' : x + ldap_base, 'label' : ldap_dn2path( x + ldap_base ) }, containers )

	@property
	def superordinates( self ):
		modules = getattr( self.module, 'wizardsuperordinates', [] )
		superordinates = []
		for mod in modules:
			if mod == 'None':
				superordinates.append( { 'id' : mod, 'label' : _( 'None' ) } )
			else:
				module = UDM_Module( mod )
				if module:
					for obj in module.search():
						superordinates.append( { 'id' : obj.dn, 'label' : '%s: %s' % ( module.title, obj[ module.identifies ] ) } )

		return superordinates

	def types4superordinate( self, flavor, superordinate ):
		types = getattr( self.module, 'wizardtypesforsuper' )
		typelist = []

		if superordinate == 'None':
			module_name = superordinate
		else:
			module = get_module( flavor, superordinate )
			if not module:
				return typelist
			module_name = module.name

		if isinstance( types, dict ) and module_name in types:
			for mod in types[ module_name ]:
				module = UDM_Module( mod )
				if module:
					typelist.append( { 'id' : mod, 'label' : module.title } )

		return typelist

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
		base, name = split_module_name( module_name )

		return map( lambda x: { 'id' : x, 'label' : ldap_dn2path( x ) }, self.directory.info.get( base, [] ) )

	def resultColumns( self, module_name ):
		pass

def split_module_name( module_name ):
	if module_name.find( '/' ) < 0:
		return []
	parts = module_name.split( '/', 1 )
	if len( parts ) == 2:
		return parts

	return ( None, None )

def ldap_dn2path( ldap_dn ):
	ldap_base = ucr.get( 'ldap/base' )
	if ldap_base is None or not ldap_dn.endswith( ldap_base ):
		return ldap_dn
	rdn = ldap_dn[ : -1 * len( ldap_base ) ]
	path = []
	for item in ldap_base.split( ',' ):
		if not item: continue
		dummy, value = item.split( '=', 1 )
		path.append( value )
	path = [ '.'.join( path ) + ':', ]
	if rdn:
		for item in rdn.split( ',' )[ 1 : ]:
			if not item: continue
			dummy, value = item.split( '=', 1 )
			path.insert( 1, value )

	return '/'.join( path )

def get_module( flavor, ldap_dn ):
	if flavor is None:
		base = None
	else:
		base, name = split_module_name( flavor )
	lo, po = get_ldap_connection()
	modules = udm_modules.objectType( None, lo, ldap_dn, module_base = base )

	if not modules:
		return None

	return UDM_Module( modules[ 0 ] )

def init_syntax():
	MODULE.info( 'Scanning syntax classes ...' )
	for name, syn in udm_syntax.__dict__.items():
		if type( syn ) is not type:
			continue
		if not hasattr( syn, 'udm_module' ):
			continue
		MODULE.info( 'Found syntax class %s with udm_module attribute (= %s)' % ( name, syn.udm_module ) )
		module = UDM_Module( syn.udm_module )
		if module is None:
			syn.choices = ()
			continue
		MODULE.info( 'Found syntax %s with udm_module property' % name )
		syn.choices = map( lambda obj: ( obj.dn, obj[ module.identifies ] ), module.search() )
		MODULE.info( 'Set choices to %s' % syn.choices )


