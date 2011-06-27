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
from univention.management.console.modules import Base
from univention.management.console.log import MODULE

from .ldap import UDM_Module, UDM_Settings, ldap_dn2path, get_module

_ = Translation( 'univention-management-console-modules-udm' ).translate

class Instance( Base ):
	def __init__( self ):
		Base.__init__( self )
		self.settings = None

	def init( self ):
		'''Initialize the module. Invoked when ACLs, commands and
		credentials are available'''
		self.settings = UDM_Settings( self._username )

	def put( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		self.finished( request.id )

	def remove( self, request ):

		self.finished( request.id )

	def get( self, request ):
		result = []
		for ldap_dn in request.options:
			module = get_module( request.flavor, ldap_dn )
			if module is None:
				continue
			obj = module.get( ldap_dn )
			if obj:
				result.append( obj.info )
		self.finished( request.id, result )

	def query( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		superordinate = request.options.get( 'superordinate' )
		if superordinate is not None:
			MODULE.info( 'Query defines a superordinate %s' % superordinate )
			mod = get_module( request.flavor, superordinate )
			if mod is not None:
				MODULE.info( 'Found UDM module for superordinate' )
				superordinate = mod.get( superordinate )

		result = module.search( request.options.get( 'container' ), request.options[ 'objectProperty' ], request.options[ 'objectPropertyValue' ], superordinate )

		entries = []
		for obj in result:
			module = get_module( request.flavor, obj.dn )
			if module is None:
				MODULE.warn( 'Could not identify LDAP object %s (flavor: %s). The object is ignored.' % ( obj.dn, request.flavor ) )
				continue
			entries.append( { 'ldap-dn' : obj.dn, 'objectType' : module.name, 'name' : obj[ module.identifies ], 'path' : ldap_dn2path( obj.dn ) } )
		self.finished( request.id, entries )

	def values( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		property_name = request.options.get( 'objectProperty' )
		module = UDM_Module( module_name )

		self.finished( request.id, module.get_default_values( property_name ) )

	def containers( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		self.finished( request.id, module.containers + self.settings.containers( request.flavor ) )

	def superordinates( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )
		self.finished( request.id, module.superordinates )

	def templates( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

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
			self.finished( request.id, module.types4superordinate( superordinate ) )

		self.finished( request.id, module.child_modules )

	def layout( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )
		self.finished( request.id, module.layout )

	def properties( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( request.flavor )
		properties = module.properties
		if request.options.get( 'searchable', False ):
			properties = filter( lambda prop: prop[ 'searchable' ], properties )
		self.finished( request.id, properties )

	def options( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.options )
