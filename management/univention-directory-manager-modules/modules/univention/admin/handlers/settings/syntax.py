# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for syntax objects
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import string, os
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation( 'univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/syntax'
superordinate = 'settings/cn'
childs = 0
operations = [ 'add', 'edit', 'remove', 'search', 'move' ]
short_description=_( 'Settings: Syntax Definition' )
long_description = ''
options = {}
property_descriptions = {
	'name' : univention.admin.property(
				short_description = _('Syntax Name'),
				long_description = '',
				syntax = univention.admin.syntax.string,
				multivalue = 0,
				options = [],
				required = 1,
				may_change = 1,
				identifies = 1
				),
	'description' : univention.admin.property(
				short_description = _( 'Syntax Description' ),
				long_description = '',
				syntax = univention.admin.syntax.string,
				multivalue = 0,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	'filter' : univention.admin.property(
				short_description = _( 'LDAP Search Filter' ),
				long_description = '',
				syntax = univention.admin.syntax.string,
				multivalue = 0,
				options = [],
				required = 1,
				may_change = 1,
				identifies = 0
				),
	'base' : univention.admin.property(
				short_description = _( 'LDAP Base' ),
				long_description = '',
				syntax = univention.admin.syntax.ldapDn,
				multivalue = 0,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	'attribute' : univention.admin.property(
				short_description = _( 'Displayed Attributes' ),
				long_description = '',
				syntax = univention.admin.syntax.listAttributes,
				multivalue = 1,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	'ldapattribute' : univention.admin.property(
				short_description = _( 'Displayed LDAP Attributes' ),
				long_description = '',
				syntax = univention.admin.syntax.string,
				multivalue = 1,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	'viewonly' : univention.admin.property(
				short_description = _( 'Show Only' ),
				long_description = '',
				syntax = univention.admin.syntax.TrueFalseUp,
				multivalue = 0,
				options = [],
				required = 1,
				may_change = 1,
				identifies = 0
				),
	'value' : univention.admin.property(
				short_description = _( 'Stored Attribute' ),
				long_description = '',
				syntax = univention.admin.syntax.listAttributes,
				multivalue = 0,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	'ldapvalue' : univention.admin.property(
				short_description = _( 'Stored LDAP Attribute' ),
				long_description = '',
				syntax = univention.admin.syntax.string,
				multivalue = 0,
				options = [],
				required = 0,
				may_change = 1,
				identifies = 0
				),
	}

layout = [
	univention.admin.tab( _( 'General' ), _( 'Basic Values' ),
						  [ [ univention.admin.field( "name" ), univention.admin.field( "description" ) ],
							[ univention.admin.field( "filter" ), univention.admin.field( "base" ) ],
							[ univention.admin.field( "attribute" ), univention.admin.field( "ldapattribute" ) ],
							[ univention.admin.field( "value" ), univention.admin.field( "ldapvalue" ) ],
							[ univention.admin.field( "viewonly" ) ] ] ) ]


mapping = univention.admin.mapping.mapping()
mapping.register( 'name', 'cn', None, univention.admin.mapping.ListToString )
mapping.register( 'filter', 'univentionSyntaxLDAPFilter', None,
				  univention.admin.mapping.ListToString )
mapping.register( 'base', 'univentionSyntaxLDAPBase', None,
				  univention.admin.mapping.ListToString )
mapping.register( 'viewonly', 'univentionSyntaxViewOnly', None,
				  univention.admin.mapping.ListToString )
mapping.register( 'description', 'univentionSyntaxDescription', None,
				  univention.admin.mapping.ListToString )

class object( univention.admin.handlers.simpleLdap ):
	module = module

	def __init__( self, co, lo, position, dn = '', superordinate = None,
				  arg = None):
		global mapping
		global property_descriptions

		self.co = co
		self.lo = lo
		self.dn = dn
		self.position = position
		self._exists = 0
		self.mapping = mapping
		self.descriptions = property_descriptions
		self.options = []

		self.alloc = []

		univention.admin.handlers.simpleLdap.__init__( self, co, lo, position,
													   dn, superordinate )

	def __check( self ):
		if self[ 'viewonly' ] == 'FALSE' and not self[ 'value' ]:
			raise univention.admin.uexceptions.insufficientInformation( _( 'An LDAP attribute is required that should be used for storing the information' ) )

	def open( self ):
		univention.admin.handlers.simpleLdap.open( self )
		if self.dn:
			# initialize items
			self[ 'attribute' ] = []
			self[ 'ldapattribute' ] = []
			self[ 'value' ] = ''
			self[ 'ldapvalue' ] = ''

			# split ldap attribute value into two parts and add them to separate dir manager widgets
			for item in self.oldattr.get('univentionSyntaxLDAPAttribute', []):
				if ':' in item:
					self[ 'attribute' ].append(item)
				else:
					self[ 'ldapattribute' ].append(item)

			# set attribute name of value that shall be written to LDAP
			# WARNING: drop down box is only used if string is not set
			val = self.oldattr.get('univentionSyntaxLDAPValue', '')
			if isinstance( val, ( list, tuple ) ):
				val = val[ 0 ]
			if val and ':' in val:
				self[ 'value' ] = val
			else:
				self[ 'ldapvalue' ] = val

	def exists( self ):
		return self._exists

	def _ldap_pre_create( self ):
		self.__check()
		self.dn = 'cn=%s,%s' % ( mapping.mapValue( 'name',
												   self.info[ 'name' ] ),
								 self.position.getDn() )

	def _ldap_pre_modify( self ):
		self.__check()

	def _ldap_addlist(self):
		return [ ( 'objectClass', [ 'top', 'univentionSyntax' ] ), ]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		attr = self[ 'attribute' ]
		attr.extend( self['ldapattribute'] )
		ml.append( ('univentionSyntaxLDAPAttribute', self.oldattr.get('univentionSyntaxLDAPAttribute', []), attr) )

		vallist = [ self[ 'value' ] ]
		if self[ 'ldapvalue' ]:
			vallist = [ self[ 'ldapvalue' ] ]
		ml.append( ('univentionSyntaxLDAPValue', self.oldattr.get('univentionSyntaxLDAPValue', []), vallist ) )

		return ml

def lookup( co, lo, filter_s, base = '', superordinate = None, scope = 'sub',
			unique = 0, required = 0, timeout = -1, sizelimit = 0 ):
	filter = univention.admin.filter.expression( 'objectClass',
												 'univentionSyntax' )

	if filter_s:
		filter_p = univention.admin.filter.parse( filter_s )
		univention.admin.filter.walk( filter_p,
									  univention.admin.mapping.mapRewrite,
									  arg = mapping )
		filter.expressions.append( filter_p )

	res = []
	for dn in lo.searchDn( unicode( filter ), base, scope, unique, required,
						   timeout, sizelimit ):
		res.append( object( co, lo, None, dn ) )
	return res

def identify( dn, attr, canonical = 0 ):
	return 'univentionSyntax' in attr.get( 'objectClass', [] )
