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

_ = umc.Translation( 'univention-management-console-modules-udm' ).translate

class Instance( umcm.Base ):
	def put( self, request ):

		self.finished( request.id )

	def remove( self, request ):

		self.finished( request.id )

	def get( self, request ):
		
		self.finished( request.id )

	def query( self, request ):

		self.finished( request.id )

	def search_layout( self, request ):
		widgets = [ {
			'type': 'ComboBox',
			'name': 'container',
			'description': 'LDAP container in which objects are searched for.',
			'label': 'Container',
			'dynamicValues': 'udm/search/containers'
		}, {
			'type': 'ComboBox',
			'name': 'type',
			'label': 'Object',
			'description': 'The type of user that is searched for.',
			'dynamicValues': 'udm/search/types'
		}, {
			'depends': 'type',
			'type': 'ComboBox',
			'name': 'property',
			'label': 'Object property',
			'description': 'Type object property that is searched for.',
			'dynamicValues': 'udm/search/properties'
#		}, {
#			'depends': ['property', 'type'],
#			'type': 'MutableInput',
#			'name': 'value',
#			'label': 'Value',
#			'description': 'Value of the selected property',
#			'dynamicValues': 'udm/search/values'
		} ]
		self.finished( request.id, widgets )

	def search_containers( self, request ):
		containers = [
			{ 'id': 'all', 					'label': 'all registered User containers' },
			{ 'id': 'univention.qa/users',	'label': 'only univention.qa:/users/' },
			{ 'id': 'domain', 				'label': 'selected domain' },
			{ 'id': 'domain_rec',			'label': 'selected domain including subdomains' }
		]
		self.finished( request.id, containers )

	def search_types( self, request ):
		types = [
			{ 'id': 'all', 'label': 'All registered users' },
			{ 'id': 'superusers', 'label': 'Superusers' },
			{ 'id': 'admins', 'label': 'Administrators' }
		]
		self.finished( request.id, types )

	def search_properties( self, request ):
		properties = {
			'all': [
				{ 'id': 'name', 'label': 'Name of user' },
				{ 'id': 'description', 'label': 'Description of user' },
				{ 'id': 'uid', 'label': 'UID of user' },
				{ 'id': 'group', 'label': 'Group of user' },
				{ 'id': 'coolguy', 'label': 'User is a cool guy?' },
			],
			'superusers': [
				{ 'id': 'name', 'label': 'Name of superuser' },
				{ 'id': 'description', 'label': 'Description of superuser' },
				{ 'id': 'uid', 'label': 'UID of superuser' },
				{ 'id': 'group', 'label': 'Group of superuser' },
				{ 'id': 'coolguy', 'label': 'Superuser is a cool guy?' },
			],
			'admins': [
				{ 'id': 'name', 'label': 'Name of admin' },
				{ 'id': 'description', 'label': 'Description of admin' },
				{ 'id': 'uid', 'label': 'UID of admin' },
				{ 'id': 'group', 'label': 'Group of admin' },
				{ 'id': 'coolguy', 'label': 'Admin is a cool guy?' },
			]
		}
		thetype = request.options.get('type', 'all')
		self.finished( request.id, properties[thetype] )

	def search_values( self, request ):
		values = {
			'group': [
				{ 'id': 'dau', 'label': 'DAU Group' },
				{ 'id': 'group1', 'label': 'Group #1' },
				{ 'id': 'group2', 'label': 'Group #2' },
				{ 'id': 'group3', 'label': 'Group #3' },
			],
			'coolguy': true,
			'name': '*',
			'description': '*',
			'uid': '1*'
		}
		theproperty = request.options.get('property', 'name')
		self.finished( request.id, values[theproperty] )



