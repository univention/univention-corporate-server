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

import univention.admin.modules as udm_modules
import univention.admin.uldap as udm_uldap
import univention.admin.syntax as udm_syntax

from ...config import ucr

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
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			if key == property_name:
				if isinstance( prop.syntax, udm_syntax.boolean ):
					return False
				elif isinstance( prop.syntax, udm_syntax.simple ):
					return '*'
				elif isinstance( prop.syntax, udm_syntax.select ):
					return prop.syntax.choices

	@property
	def child_modules( self ):
		if self.module is None:
			return None
		children = getattr( self.module, 'childmodules', None )
		if children is None:
			return []
		modules = []
		for child in children:
			mod = udm_modules.get( child )
			if not mod:
				continue
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
	def properties( self ):
		props = []
		for key, prop in getattr( self.module, 'property_descriptions', {} ).items():
			props.append( { 'id' : key, 'label' : prop.short_description } )
		props.sort( key = operator.itemgetter( 'id' ) )
		return props

	@property
	def operations( self ):
		return self.module is not None and getattr( self.module, 'operations', None )


class UDM_DefaultContainers( object ):
	def __init__( self ):
		lo, po = get_ldap_connection()
		objects = udm_modules.lookup( 'settings/directory', None, lo, scope = 'sub' )

		if not objects:
			self.object = None
		else:
			self.object = objects[ 0 ]

	def get( self, module_name ):
		if module_name.find( '/' ) < 0:
			return []
		base, name = module_name.split( '/', 1 )

		return self.object[ base ]
