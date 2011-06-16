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

	def set( self, request ):
		self.finished( request.id )

	def remove( self, request ):

		self.finished( request.id )

	def get( self, request ):

		self.finished( request.id )

	def query( self, request ):

		self.finished( request.id )

	def search_properties( self, request ):
		module_name = request.options.get( 'objectType' )
		module = UDM_Module( module_name )

		self.finished( request.id, module.properties )

	def search_values( self, request ):
		module_name = request.options.get( 'objectType' )
		property_name = request.options.get( 'objectProperty' )
		module = UDM_Module( module_name )

		self.finished( request.id, module.get_default_values( property_name ) )

	def search_layout( self, request ):
		module = UDM_Module( request.flavor )
		widgets = []
		containers = self.defaults.get( request.flavor )
		if containers:
			containers.sort()
			containers = map( lambda x: { x : x }, containers )
			containers.insert( 0, { 'all' : _( 'All' ) } )
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

		widgets.extend( [
			{
				'type' : 'ComboBox',
				'name' : 'objectProperty',
				'depends' : [ 'objectType', ],
				'description' : _( 'The attribute that should be compared to the given keyword' ),
				'label' : _( 'Keyword' ),
				'dynamicValues' : 'udm/search/properties'
			},
			{
				'type' : 'MixedInput',
				'name' : 'objectPropertyValue',
				'depends' : [ 'objectType', 'objectProperty' ],
				'description' : _( 'The keyword that should be searched for in the selected attribute' ),
				'label' : '',
				'dynamicValues' : 'udm/search/values'
			}, ] )

		self.finished( request.id, widgets )
