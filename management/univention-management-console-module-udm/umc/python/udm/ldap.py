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
import univention.admin.objects as udm_objects
import univention.admin.uldap as udm_uldap
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions as udm_errors

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
	"""Tries to open an LDAP connection. On DC master and DC backup
	systems the cn=admin account is used and on all other system roles
	the machine account.

	return: ( <LDAP connection>, <LDAP position> )
	"""
	global _ldap_connection, _ldap_position

	if _ldap_connection is not None:
		return _ldap_connection, _ldap_position

	if ucr.get( 'server/role' ) in ( 'domaincontroller_master', 'domaincontroller_backup' ):
		_ldap_connection, _ldap_position = udm_uldap.getAdminConnection()
	else:
		_ldap_connection, _ldap_position = udm_uldap.getMachineConnection()

	return _ldap_connection, _ldap_position

class UDM_Module( object ):
	"""Wraps UDM modules to provie a simple access to the properties and functions"""

	UCR_SEARCH_DEFAULT = 'directory/manager/web/modules/%(module)s/search/default'

	def __init__( self, module ):
		"""Initializes the object"""
		self.load( module )

	def load( self, module, template_object = None ):
		"""Tries to load an UDM module with the given name. Optional a
		template object is passed to the init function of the module. As
		the initialisation of a module is expensive the function uses a
		cache to ensure that each module is just initialized once."""
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
		"""Depending on the syntax of the given property a default
		search pattern/value is returned"""
		MODULE.info( 'Searching for property %s' % property_name )
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == property_name:
				return default_value( prop.syntax )

	def create( self, ldap_object, container = None, superordinate = None ):
		"""Creates a LDAP object"""
		lo, po = get_ldap_connection()

		if container is not None:
			try:
				po.setDn( container )
			except udm_errors.noObject, e:
				raise UMC_CommandError( str( e ) )

		if superordinate is not None:
			mod = get_module( self.name, superordinate )
			if mod is not None:
				MODULE.info( 'Found UDM module for superordinate' )
				superordinate = mod.get( superordinate )
			else:
				raise UMC_OptionTypeError( _( 'Could not find an UDM module for the superordinate object %s' ) % superordinate )

		obj = self.module.object( None, lo, po, superordinate = superordinate )
		obj.open()
		MODULE.info( 'Creating object with properties: %s' % ldap_object )
		for key, value in ldap_object.items():
			obj[ key ] = value
		obj.create()

	def modify( self, ldap_object ):
		"""Modifies a LDAP object"""
		lo, po = get_ldap_connection()

		obj = self.module.object( None, lo, po, dn = ldap_object.get( 'ldap-dn' ) )
		del ldap_object[ 'ldap-dn' ]
		obj.open()
		MODULE.info( 'Modifying object with properties: %s' % ldap_object )
		for key, value in ldap_object.items():
			obj[ key ] = value
		obj.modify()

	def search( self, container = None, attribute = None, value = None, superordinate = None ):
		"""Searches for LDAP objects based on a search pattern"""
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
		"""Retrieves details for a given LDAP object"""
		lo, po = get_ldap_connection()
		obj = self.module.object( None, lo, None, ldap_dn )
		obj.open()

		return obj

	def get_property( self, property_name ):
		"""Returns details for a given property"""
		return getattr( self.module, 'property_descriptions', {} ).get( property_name, None )

	@property
	def name( self ):
		"""Internal name of the UDM module"""
		return self.module is not None and self.module.module

	@property
	def title( self ):
		"""Descriptive name of the UDM module"""
		return getattr( self.module, 'short_description', self.module.module )

	@property
	def identifies( self ):
		"""Property of the UDM module that identifies objects of this type"""
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if prop.identifies:
				return key
		return None

	@property
	def child_modules( self ):
		"""List of child modules"""
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
		"""Layout information"""
		layout = getattr( self.module, 'layout', [] )
		if not layout:
			return layout

		if isinstance( layout[ 0 ], udm.tab ):
			return self._parse_old_layout( layout )

		return layout

	def _parse_old_layout( self, layout ):
		"""Parses old layout information"""
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

	@property
	def password_properties( self ):
		"""All properties with the syntax class passwd or userPasswd"""
		passwords = []
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if prop.syntax in ( udm_syntax.passwd, udm_syntax.userPasswd ):
				passwords.append( key )

		return passwords

	@property
	def properties( self ):
		"""All properties of the UDM module"""
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
		"""List of defined options"""
		opts = []
		for key, option in getattr( self.module, 'options', {} ).items():
			item = { 'id' : key, 'label' : option.short_description, 'default' : option.default }
			opts.append( item )
		opts.sort( key = operator.itemgetter( 'label' ) )
		return opts

	@property
	def operations( self ):
		"""Allowed operations of the UDM module"""
		return self.module is not None and getattr( self.module, 'operations', None )

	@property
	def template( self ):
		"""List of UMD module names of templates"""
		return getattr( self.module, 'template', None )

	@property
	def containers( self ):
		"""List of LDAP DNs of default containers"""
		containers = getattr( self.module, 'default_containers', [] )
		ldap_base = ucr.get( 'ldap/base' )

		return map( lambda x: { 'id' : x + ldap_base, 'label' : ldap_dn2path( x + ldap_base ) }, containers )

	@property
	def superordinates( self ):
		"""List of superordinates"""
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
		"""List of object types for the given superordinate"""
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
	"""Provides access to different kinds of settings regarding UDM"""

	def __init__( self, username ):
		"""Reads the policies for the current user"""
		lo, po = get_ldap_connection()
		self.user_dn = lo.searchDn( 'uid=%s' % username, unique = True )
		self.policies = lo.getPolicies( self.user_dn )

		directories = udm_modules.lookup( 'settings/directory', None, lo, scope = 'sub' )
		if not directories:
			self.directory = None
		else:
			self.directory = directories[ 0 ]

	def containers( self, module_name ):
		"""Returns list of default containers for a given UDM module"""
		base, name = split_module_name( module_name )

		return map( lambda x: { 'id' : x, 'label' : ldap_dn2path( x ) }, self.directory.info.get( base, [] ) )

	def resultColumns( self, module_name ):
		pass

def split_module_name( module_name ):
	"""Splits a module name into category and internal name"""

	if module_name.find( '/' ) < 0:
		return []
	parts = module_name.split( '/', 1 )
	if len( parts ) == 2:
		return parts

	return ( None, None )

def ldap_dn2path( ldap_dn ):
	"""Returns a path representation of an LDAP DN"""

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
	"""Determines an UDM module handling the LDAP object identified by the given LDAP DN"""
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
	"""Initialize all syntax classes

	Syntax classes based on select: If a property udm_module is
	available the choices attribute of the class is set to a list of all
	available modules of the specified UDM module.
	"""
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


