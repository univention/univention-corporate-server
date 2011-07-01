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

from univention.management.console import Translation
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
from univention.management.console.log import MODULE

import univention.admin.uexceptions as udm_errors

from .ldap import UDM_Module, UDM_Settings, ldap_dn2path, get_module, init_syntax

_ = Translation( 'univention-management-console-modules-udm' ).translate

init_syntax()

class Instance( Base ):
	def __init__( self ):
		Base.__init__( self )
		self.settings = None

	def init( self ):
		'''Initialize the module. Invoked when ACLs, commands and
		credentials are available'''
		self.settings = UDM_Settings( self._username )

	def _get_module( self, request, object_type = None ):
		if object_type is None:
			module_name = request.options.get( 'objectType' )
		else:
			module_name = object_type
		if not module_name or 'all' == module_name:
			module_name = request.flavor

		if not module_name:
			raise UMC_OptionMissing( _( 'No flavor or valid UDM module name specified' ) )

		return UDM_Module( module_name )

	def add( self, request ):
		for obj in request.options:
			if not isinstance( obj, dict ):
				raise UMC_OptionTypeError( _( 'Invalid object definition' ) )

			options = obj.get( 'options', {} )
			properties = obj.get( 'object', {} )

			module = self._get_module( request, object_type = options.get( 'objectType' ) )
			module.create( properties, container = options.get( 'container' ), superordinate = options.get( 'superordinate' ) )

		self.finished( request.id, True )

	def put( self, request ):
		for obj in request.options:
			if not isinstance( obj, dict ):
				raise UMC_OptionTypeError( _( 'Invalid object definition' ) )
			options = obj.get( 'options', {} )
			properties = obj.get( 'object', {} )
			if not properties.get( 'ldap-dn' ):
				raise UMC_OptionMissing( _( 'LDAP DN of object missing' ) )
			module = get_module( request.flavor, properties[ 'ldap-dn' ] )
			if module is None:
				raise UMC_OptionTypeError( _( 'Could not find a matching UMD module for the LDAP object %s' ) % properties[ 'ldap-dn' ] )
			MODULE.info( 'Modifying LDAP object %s' % properties[ 'ldap-dn' ] )
			module.modify( properties )
		self.finished( request.id, True )

	def remove( self, request ):
		module = self._get_module( request )

		self.finished( request.id )

	def get( self, request ):
		result = []
		for ldap_dn in request.options:
			module = get_module( request.flavor, ldap_dn )
			if module is None:
				continue
			obj = module.get( ldap_dn )
			if obj:
				props = obj.info
				for passwd in module.password_properties:
					if passwd in props:
						del props[ passwd ]
				props[ 'ldap-dn' ] = obj.dn
				result.append( props )
		self.finished( request.id, result )

	def query( self, request ):
		module = self._get_module( request )

		superordinate = request.options.get( 'superordinate' )
		if superordinate == 'None':
			superordinate = None
		elif superordinate is not None:
			MODULE.info( 'Query defines a superordinate %s' % superordinate )
			mod = get_module( request.flavor, superordinate )
			if mod is not None:
				MODULE.info( 'Found UDM module for superordinate' )
				superordinate = mod.get( superordinate )
			else:
				raise UMC_OptionTypeError( _( 'Could not find an UDM module for the superordinate object %s' ) % superordinate )

		result = module.search( request.options.get( 'container' ), request.options[ 'objectProperty' ], request.options[ 'objectPropertyValue' ], superordinate )

		entries = []
		for obj in result:
			if obj is None:
				continue
			module = get_module( request.flavor, obj.dn )
			if module is None:
				MODULE.warn( 'Could not identify LDAP object %s (flavor: %s). The object is ignored.' % ( obj.dn, request.flavor ) )
				continue
			entries.append( { 'ldap-dn' : obj.dn, 'objectType' : module.name, 'name' : obj[ module.identifies ], 'path' : ldap_dn2path( obj.dn ) } )
		self.finished( request.id, entries )

	def values( self, request ):
		module = self._get_module( request )
		property_name = request.options.get( 'objectProperty' )

		self.finished( request.id, module.get_default_values( property_name ) )

	def containers( self, request ):
		module = self._get_module( request )

		self.finished( request.id, module.containers + self.settings.containers( request.flavor ) )

	def superordinates( self, request ):
		module = self._get_module( request )
		self.finished( request.id, module.superordinates )

	def templates( self, request ):
		module = self._get_module( request )

		result = []
		if module.template:
			template = UDM_Module( module.template )
			objects = template.search( ucr.get( 'ldap/base' ) )
			for obj in objects:
				obj.open()
				result.append( { 'id' : obj.dn, 'label' : obj[ template.identifies ] } )

		self.finished( request.id, result )

	def types( self, request ):
		module = UDM_Module( request.flavor )
		superordinate = request.options.get( 'superordinate' )
		if superordinate:
			self.finished( request.id, module.types4superordinate( request.flavor, superordinate ) )

		self.finished( request.id, module.child_modules )

	def layout( self, request ):
		module = self._get_module( request )
		self.finished( request.id, module.layout )

	def properties( self, request ):
		module = self._get_module( request )
		properties = module.properties
		if request.options.get( 'searchable', False ):
			properties = filter( lambda prop: prop[ 'searchable' ], properties )
		self.finished( request.id, properties )

	def options( self, request ):
		module = self._get_module( request )
		self.finished( request.id, module.options )

	def validate( self, request ):
		module = self._get_module( request )

		result = []
		for property_name, value in request.options.get( 'properties' ).items():
			property_obj = module.get_property( property_name )

			if property_obj is None:
				raise UMC_OptionMissing( _( 'Property %s not found' ) % property_name )

			try:
				property_obj.syntax.parse( value )
				result.append( { 'property' : property_name, 'valid' : True } )
			except ( udm_errors.valueInvalidSyntax, udm_errors.valueError ), e:
				result.append( { 'property' : property_name, 'valid' : False, 'details' : str( e ) } )

		self.finished( request.id, result )
