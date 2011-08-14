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

import notifier
import notifier.threads

from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
from univention.management.console.log import MODULE

import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_errors

from .ldap import UDM_Error, UDM_Module, UDM_Settings, ldap_dn2path, get_module, read_syntax_choices, list_objects

_ = Translation( 'univention-management-console-modules-udm' ).translate

class Instance( Base ):
	def __init__( self ):
		Base.__init__( self )
		self.settings = None

	def init( self ):
		'''Initialize the module. Invoked when ACLs, commands and
		credentials are available'''
		if self._username is not None:
			self.settings = UDM_Settings( self._username )

	def _get_module( self, request, object_type = None ):
		"""Tries to determine to UDM module to use. If no specific
		object type is given the request option 'objectType' is used. In
		case none if this leads to a valid object type the request
		flavor is chosen. Failing all this will raise in
		UMC_OptionMissing exception. On success a UMC_Module object is
		returned."""
		if object_type is None:
			module_name = request.options.get( 'objectType' )
		else:
			module_name = object_type
		if not module_name or 'all' == module_name:
			module_name = request.flavor

		if not module_name:
			raise UMC_OptionMissing( _( 'No flavor or valid UDM module name specified' ) )

		return UDM_Module( module_name )

	def _thread_finished( self, thread, result, request ):
		if not isinstance( result, BaseException ):
			self.finished( request.id, result )
		else:
			self.finished( request.id, None, str( result ), False )

	def add( self, request ):
		"""Creates LDAP objects.

		requests.options = [ { 'options' : {}, 'object' : {} }, ... ]

		return: [ { 'ldap-dn' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread( request ):
			result = []
			for obj in request.options:
				if not isinstance( obj, dict ):
					raise UMC_OptionTypeError( _( 'Invalid object definition' ) )

				options = obj.get( 'options', {} )
				properties = obj.get( 'object', {} )

				module = self._get_module( request, object_type = options.get( 'objectType' ) )
				try:
					dn = module.create( properties, container = options.get( 'container' ), superordinate = options.get( 'superordinate' ) )
					result.append( { 'ldap-dn' : dn, 'success' : True } )
				except UDM_Error, e:
					result.append( { 'ldap-dn' : e.args[ 1 ], 'success' : False, 'details' : str( e.args[ 0 ] ) } )

			return result

		thread = notifier.threads.Simple( 'Get', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def put( self, request ):
		"""Modifies the given list of LDAP objects.

		requests.options = [ { 'options' : {}, 'object' : {} }, ... ]

		return: [ { 'ldap-dn' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread( request ):
			result = []
			for obj in request.options:
				if not isinstance( obj, dict ):
					raise UMC_OptionTypeError( _( 'Invalid object definition' ) )
				options = obj.get( 'options', {} )
				if options is None:
					options = {}
				properties = obj.get( 'object', {} )
				if not properties.get( 'ldap-dn' ):
					raise UMC_OptionMissing( _( 'LDAP DN of object missing' ) )
				ldap_dn = properties[ 'ldap-dn' ]
				module = get_module( request.flavor, ldap_dn )
				if module is None:
					raise UMC_OptionTypeError( _( 'Could not find a matching UDM module for the LDAP object %s' ) % ldap_dn )
				MODULE.info( 'Modifying LDAP object %s' % ldap_dn )
				try:
					module.modify( properties )
					result.append( { 'ldap-dn' : ldap_dn, 'success' : True } )
				except UDM_Error, e:
					result.append( { 'ldap-dn' : ldap_dn, 'success' : False, 'details' : str( e ) } )

			return result

		thread = notifier.threads.Simple( 'Get', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def remove( self, request ):
		"""Removes the given list of LDAP objects.

		requests.options = [ <LDAP DN>, ... ]

		return: [ { 'ldap-dn' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread( request ):
			result = []
			for ldap_dn in request.options:
				module = get_module( request.flavor, ldap_dn )
				if module is None:
					result.append( { 'ldap-dn' : ldap_dn, 'success' : False, 'details' : _( 'LDAP object could not be identified' ) } )
					continue
				try:
					module.remove( ldap_dn )
					result.append( { 'ldap-dn' : ldap_dn, 'success' : True } )
				except UDM_Error, e:
					result.append( { 'ldap-dn' : ldap_dn, 'success' : False, 'details' : str( e ) } )

		thread = notifier.threads.Simple( 'Get', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def get( self, request ):
		"""Retrieves the given list of LDAP objects. Password property will be removed.

		requests.options = [ <LDAP DN>, ... ]

		return: [ { 'ldap-dn' : <LDAP DN>, <object properties> }, ... ]
		"""

		def _thread( request ):
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
			return result

		thread = notifier.threads.Simple( 'Get', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def query( self, request ):
		"""Searches for LDAP objects and returns a few properties of the found objects

		requests.options = {}
		  'objectProperty' -- the object property that should be scaned
		  'objectPropertyValue' -- the filter that should b found in the property
		  'container' -- the base container where the search should be started (default: LDAP base)
		  'superordinate' -- the superordinate object for the search (default: None)

		return: [ { 'ldap-dn' : <LDAP DN>, 'objectType' : <UDM module name>, 'path' : <location of object> }, ... ]
		"""

		def _thread( request ):
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
				entries.append( {
					'ldap-dn' : obj.dn,
					'objectType' : module.name,
					'name' : obj[ module.identifies ],
					'path' : ldap_dn2path( obj.dn ),
					request.options[ 'objectProperty' ] : obj[ request.options[ 'objectProperty' ] ]
				} )
			return entries

		thread = notifier.threads.Simple( 'Query', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def values( self, request ):
		"""Returns the default search pattern/value for the given object property

		requests.options = {}
		  'objectProperty' -- the object property that should be scaned

		return: <value>
		"""
		module = self._get_module( request )
		property_name = request.options.get( 'objectProperty' )

		self.finished( request.id, module.get_default_values( property_name ) )

	def containers( self, request ):
		"""Returns the list of default containers for the given object
		type. Therefor the python module and the default object in the
		LDAP directory are searched.

		requests.options = {}
		  'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container>, 'label' : <name> }, ... ]
		"""
		module = self._get_module( request )

		if self.settings is not None:
			self.finished( request.id, module.containers + self.settings.containers( request.flavor ) )
		else:
			self.finished( request.id, module.containers )

	def superordinates( self, request ):
		"""Returns the list of superordinate containers for the given
		object type.

		requests.options = {}
		  'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		module = self._get_module( request )
		self.finished( request.id, module.superordinates )

	def templates( self, request ):
		"""Returns the list of template objects for the given object
		type.

		requests.options = {}
		  'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
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
		"""Returns the list of object types matching the given flavor.

		requests.options = {}
		  'superordinate' -- if available only types for the given superordinate are returned

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		if request.flavor != 'navigation':
			module = UDM_Module( request.flavor )
			superordinate = request.options.get( 'superordinate' )
			if superordinate:
				self.finished( request.id, module.types4superordinate( request.flavor, superordinate ) )
			else:
				self.finished( request.id, module.child_modules )
		else:
			self.finished( request.id, map( lambda module: { 'id' : module[ 0 ], 'label' : getattr( module[ 1 ], 'short_description', module[ 0 ] ) }, udm_modules.modules.items() ) )

	def layout( self, request ):
		"""Returns the layout information for the given object type.

		requests.options = {}
		  'objectType' -- The UDM module name. If not available the flavor is used

		return: <layout data structure (see UDM python modules)>
		"""
		module = self._get_module( request )
		self.finished( request.id, module.layout )

	def properties( self, request ):
		"""Returns the properties of the given object type.

		requests.options = {}
		  'searchable' -- If given only properties that might be used for search filters are returned

		return: [ {}, ... ]
		"""
		module = self._get_module( request )
		properties = module.properties
		if request.options.get( 'searchable', False ):
			properties = filter( lambda prop: prop[ 'searchable' ], properties )
		self.finished( request.id, properties )

	def options( self, request ):
		"""Returns the options specified for the given object type

		requests.options = {}
		  'objectType' -- The UDM module name. If not available the flavor is used

		return: [ {}, ... ]
		"""
		module = self._get_module( request )
		self.finished( request.id, module.options )

	def policies( self, request ):
		"""Returns a list of policy types that apply to the given object type"""
		module = self._get_module( request )
		self.finished( request.id, module.policies )

	def validate( self, request ):
		"""Validates the correctness of values for properties of the
		given object type. Therefor the syntax definition of the properties is used.

		requests.options = {}
		  'objectType' -- The UDM module name. If not available the flavor is used

		return: [ { 'property' : <name>, 'valid' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread( request ):
			module = self._get_module( request )

			result = []
			for property_name, value in request.options.get( 'properties' ).items():
				property_obj = module.get_property( property_name )

				if property_obj is None:
					raise UMC_OptionMissing( _( 'Property %s not found' ) % property_name )

				# check each element if 'value' is a list
				if isinstance(value, (tuple, list)):
					subResults = []
					subDetails = []
					for ival in value:
						try:
							property_obj.syntax.parse( ival )
							subResults.append( True )
							subDetails.append('')
						except ( udm_errors.valueInvalidSyntax, udm_errors.valueError, TypeError ), e:
							subResults.append( False )
							subDetails.append( str(e) )
					result.append( { 'property' : property_name, 'valid' : subResults, 'details' : subDetails } )
				# otherwise we have a single value
				else:
					try:
						property_obj.syntax.parse( value )
						result.append( { 'property' : property_name, 'valid' : True } )
					except ( udm_errors.valueInvalidSyntax, udm_errors.valueError ), e:
						result.append( { 'property' : property_name, 'valid' : False, 'details' : str( e ) } )

			return result

		thread = notifier.threads.Simple( 'Validate', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def syntax_choices( self, request ):
		"""Dynamically determine valid values for a given syntax class

		requests.options = {}
		  'syntax' -- The UDM syntax class

		return: [ { 'id' : <name>, 'label' : <text }, ... ]
		"""

		if not 'syntax' in request.options:
			raise UMC_OptionMissing( "The option 'syntax' is required" )

		def _thread( request ):
			return read_syntax_choices( request.options[ 'syntax' ], request.options.get( 'options', {} ) )

		thread = notifier.threads.Simple( 'SyntaxChoice', notifier.Callback( _thread, request ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def nav_container_query( self, request ):
		"""Returns a list of LDAP containers located under the given
		LDAP base (option 'container'). If no base container is
		spiecified the LDAP base object is returned."""

		if not request.options.get( 'container' ):
			ldap_base = ucr.get( 'ldap/base' )
			self.finished( request.id, [ { 'id' : ldap_base, 'label' : ldap_dn2path( ldap_base ), 'icon' : 'udm-container-dc' } ] )
			return

		def _thread( container ):
			success = True
			message = None
			superordinate = None
			result = []
			for base, typ in ( ( 'container', 'cn' ), ( 'container', 'ou' ), ( 'settings', 'cn' ), ( 'dhcp', 'service' ), ( 'dhcp', 'subnet' ), ( 'dhcp', 'sharedsubnet' ), ( 'dns', 'forward_zone' ), ( 'dns', 'reverse_zone' ) ):
				module = UDM_Module( '%s/%s' % ( base, typ ) )
				if module.superordinate:
					if superordinate is None:
						so_module = UDM_Module( module.superordinate )
						so_obj = so_module.get( request.options.get( 'container' ) )
						superordinate = so_obj
					else:
						so_obj = superordinate
				else:
					so_obj = None
				try:
					for item in module.search( container, scope = 'one', superordinate = so_obj ):
						result.append( { 'id' : item.dn, 'label' : item[ module.identifies ], 'icon' : 'udm-%s-%s' % ( base, typ ), 'path': ldap_dn2path( item.dn ), 'objectType': '%s/%s' % (base, typ) } )
				except UDM_Error, e:
					success = False
					result = None
					message = str( e )

			return result, message, success

		def _finish( thread, result, request ):
			if not isinstance( result, BaseException ):
				result, message, success = result
				self.finished( request.id, result, message, success )
			else:
				self.finished( request.id, None, str( result ), False )

		thread = notifier.threads.Simple( 'NavObjectQuery', notifier.Callback( _thread, request.options[ 'container' ] ),
										  notifier.Callback( _finish, request ) )
		thread.run()

	def nav_object_query( self, request ):
		"""Returns a list of objects in a LDAP container (scope: one)

		requests.options = {}
		  'container' -- the base container where the search should be started (default: LDAP base)

		return: [ { 'ldap-dn' : <LDAP DN>, 'objectType' : <UDM module name>, 'path' : <location of object> }, ... ]
		"""
		if not 'container' in request.options:
			raise UMC_OptionMissing( "The option 'container' is required" )

		def _thread( container ):
			entries = []
			for module, obj in list_objects( container ):
				if obj is None or module.childs:
					continue
				entries.append( { 'ldap-dn' : obj.dn, 'objectType' : module.name, 'name' : obj[ module.identifies ], 'path' : ldap_dn2path( obj.dn ) } )

			return entries

		thread = notifier.threads.Simple( 'NavObjectQuery', notifier.Callback( _thread, request.options[ 'container' ] ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def object_policies( self, request ):
		object_type = request.options.get( 'objectType' )
		if not object_type:
			raise UMC_OptionMissing( 'The object type is missing' )
		object_dn = request.options.get( 'objectDN' )
		if not object_dn:
			raise UMC_OptionMissing( 'The object LDAP DN is missing' )
		policy_type = request.options.get( 'policyType' )
		if not object_dn:
			raise UMC_OptionMissing( 'The policy type is missing' )

		def _thread( object_type, object_dn, policy_type ):
			module = UDM_Module( object_type )
			if module.module is None:
				raise UMC_OptionTypeError( 'The given object type is not valid' )

			obj = module.get( object_dn )
			if obj is None:
				raise UMC_OptionTypeError( 'The object could not be found' )

			policy_module = UDM_Module( policy_type )
			if policy_module.module is None:
				raise UMC_OptionTypeError( 'The given policy type is not valid' )

			policy_obj = policy_module.get()
			policy_obj.clone( obj )
			policy_obj.policy_result()

			infos = copy.copy( policy_obj.polinfo_more )
			for key, value in infos.items():
				if key in policy_obj.polinfo:
					infos[ key ][ 'value' ] = policy_obj.polinfo[ key ]

			return infos

		thread = notifier.threads.Simple( 'ObjectPolicies', notifier.Callback( _thread, object_type, object_dn, policy_type ),
										  notifier.Callback( self._thread_finished, request ) )
		thread.run()


