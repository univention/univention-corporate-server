#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Copyright 2011-2012 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter as udm_filter
import univention.admin.syntax as udm_syntax
import univention.admin.mapping as udm_mapping

from univention.admin.localization import translation
from univention.admin.handlers import simpleLdap

import univention.debug

_ = translation( 'univention.admin.handlers.settings' ).translate

module = 'settings/umc_operationset'
operations = ( 'add', 'edit', 'remove', 'search', 'move' )
superordinate = 'settings/cn'

childs = 0
short_description = _( 'Settings: UMC operation set')
long_description = _( 'List of Operations for UMC' )
options = {}

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description=_('Name'),
			syntax=udm_syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1,
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description=_('Description'),
			syntax=udm_syntax.string,
			multivalue=0,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'operation': univention.admin.property(
			short_description = _( 'UMC commands' ),
			long_description=_('List of UMC command names or patterns'),
			syntax=udm_syntax.UMC_CommandPattern,
			multivalue=1,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'flavor': univention.admin.property(
			short_description = _( 'Flavor' ),
			long_description = _( 'Defines a specific flavor of the UMC module. If given the operations are permitted only if the flavor matches.' ),
			syntax = udm_syntax.string,
			multivalue = False,
			options = [],
			dontsearch = True,
			required = False,
			may_change = True,
			identifies = False
		),
}

layout = [
	Tab(_('General'),_('Package List'), layout = [
		Group( _( 'General' ), layout = [
			[ 'name', 'description' ],
			'operation',
			'flavor'
		] ),
	] ),
]

def mapUMC_CommandPattern( value ):
	return map( lambda x: ':'.join( x ), value )

def unmapUMC_CommandPattern( value ):
	unmapped = []
	for item in value:
		if item.find( ':' ) >= 0:
			unmapped.append( item.split( ':', 1 ) )
		else:
			unmapped.append( ( item, '' ) )
	return unmapped

mapping=udm_mapping.mapping()
mapping.register( 'name', 'cn', None, udm_mapping.ListToString )
mapping.register( 'description', 'description', None, udm_mapping.ListToString )
mapping.register( 'operation', 'umcOperationSetCommand', mapUMC_CommandPattern, unmapUMC_CommandPattern )
mapping.register( 'flavor', 'umcOperationSetFlavor', None, udm_mapping.ListToString )

class object( simpleLdap ):
	module = module

	def __init__( self, co, lo, position, dn = '', superordinate = None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping = mapping
		self.descriptions = property_descriptions

		simpleLdap.__init__( self, co, lo, position, dn, superordinate, attributes = attributes )

	def _ldap_pre_create( self ):
		self.dn='%s=%s,%s' % ( mapping.mapName( 'name' ), mapping.mapValue( 'name', self.info[ 'name' ] ), self.position.getDn() )

	def _ldap_addlist( self ):
		return [ ( 'objectClass', [ 'top', 'umcOperationSet' ] ) ]

def lookup( co, lo, filter_s, base = '', superordinate = None, scope = 'sub', unique = 0, required = 0, timeout = -1, sizelimit = 0 ):

	filter=udm_filter.conjunction('&', [
		udm_filter.expression('objectClass', 'umcOperationSet')
		])

	if filter_s:
		filter_p=udm_filter.parse(filter_s)
		udm_filter.walk( filter_p, udm_mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
			res.append(object(co, lo, None, dn))
	except:
		pass
	return res

def identify(dn, attr, canonical=0):
	return 'umcOperationSet' in attr.get( 'objectClass', [] )
