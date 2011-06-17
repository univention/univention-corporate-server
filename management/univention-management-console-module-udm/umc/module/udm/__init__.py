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

import univention.management.console as umc
import univention.management.console.modules as umcm

from .ldap import UDM_Module, UDM_DefaultContainers

_ = umc.Translation( 'univention-management-console-modules-udm' ).translate

class Instance( umcm.Base ):
	def __init__( self ):
		umcm.Base.__init__( self )
		self.defaults = UDM_DefaultContainers()

	def put( self, request ):
		self.finished( request.id )

	def remove( self, request ):

		self.finished( request.id )

	def get( self, request ):

		self.finished( request.id )

	def query( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		result = module.search( request.options( 'container' ), request.options( 'objectProperty' ), request.options( 'objectPropertyValue' ) )

		self.finished( request.id, map( lambda obj: { 'ldap-dn' : obj.dn, 'name' : obj[ 'name' ], 'path' : obj.dn } ) )

	def query_properties( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		self.finished( request.id, module.property_names )

	def query_values( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		property_name = request.options.get( 'objectProperty' )
		module = UDM_Module( module_name )

		self.finished( request.id, module.get_default_values( property_name ) )

	def query_layout( self, request ):
		module = UDM_Module( request.flavor )
		widgets = []
		containers = self.defaults.get( request.flavor )
		if containers:
			containers.sort()
			containers = map( lambda x: { 'id' : x, 'label' : x }, containers )
			containers.insert( 0, { 'id' : 'all', 'label' : _( 'All' ) } )
			widgets.append( {
				'type' : 'ComboBox',
				'name' : 'container',
				'value' : 'all',
				'description' : _( 'The base container for the search' ),
				'label' : _( 'Container' ),
				'staticValues' : containers
				} )

		children = module.child_modules
		if children:
			widgets.append( {
				'type' : 'ComboBox',
				'name' : 'objectType',
				'value' : 'all',
				'description' : _( 'The type of the object to search for' ),
				'label' : _( 'Container' ),
				'staticValues' : children
				} )
			property_depends = [ 'objectType', ]
			property_value_depends = [ 'objectType', 'objectProperty' ]
		else:
			property_depends = []
			property_value_depends = [ 'objectProperty' ]
			widgets.append( None )

		widgets.extend( [
			{
				'type' : 'ComboBox',
				'name' : 'objectProperty',
				'depends' : property_depends,
				'description' : _( 'The attribute that should be compared to the given keyword' ),
				'label' : _( 'Keyword' ),
				'dynamicValues' : 'udm/query/properties'
			},
			{
				'type' : 'MixedInput',
				'name' : 'objectPropertyValue',
				'depends' : property_value_depends,
				'description' : _( 'The keyword that should be searched for in the selected attribute' ),
				'label' : '',
				'dynamicValues' : 'udm/query/values'
			}, ] )

		self.finished( request.id, widgets )

	def put_layout( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.layout )

	def properties( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.properties )

	def options( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.options )
