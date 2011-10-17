# -*- coding: utf-8 -*-
#
# Univention Management Console
#  admin module: policy defining access restriction for UMC
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax as udm_syntax
import univention.admin.filter as udm_filter
import univention.admin.mapping as udm_mapping

from univention.admin.handlers import simplePolicy
from  univention.admin.localization import translation

import univention.debug

_ = translation('univention.admin.handlers.policies').translate

class umcFixedAttributes( udm_syntax.select ):
	choices = (
		( 'umcPolicyGrantedOperationSet', _( 'Allowed UMC operation sets' ) ),
		)

module = 'policies/umc'
operations = ( 'add', 'edit', 'remove', 'search' )

policy_oc = 'umcPolicy'
policy_apply_to = [ 'users/user', 'groups/group' ]
policy_position_dn_prefix = 'cn=UMC'

childs = 0
short_description = _( 'Policy: UMC' )
policy_short_description = _( 'Defines a set of allowed UMC operations' )
long_description = ''

options = {}

property_descriptions = {
	'name': univention.admin.property(
			short_description = _( 'Name' ),
			long_description = '',
			syntax = udm_syntax.string,
			multivalue = False,
			options=[],
			required = True,
			may_change = False,
			identifies = True,
		),
	'allow': univention.admin.property(
			short_description = _( 'List of allowed UMC operation sets' ),
			long_description = '',
			syntax = udm_syntax.UMC_OperationSet,
			multivalue = True,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
	'requiredObjectClasses': univention.admin.property(
			short_description = _( 'Required object classes' ),
			long_description = '',
			syntax = udm_syntax.string,
			multivalue = True,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
	'prohibitedObjectClasses': univention.admin.property(
			short_description = _( 'Excluded object classes' ),
			long_description = '',
			syntax = udm_syntax.string,
			multivalue = True,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
	'fixedAttributes': univention.admin.property(
			short_description = _( 'Fixed attributes' ),
			long_description = '',
			syntax = umcFixedAttributes,
			multivalue = True,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
	'emptyAttributes': univention.admin.property(
			short_description = _( 'Empty attributes' ),
			long_description = '',
			syntax = umcFixedAttributes,
			multivalue = True,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'General' ), layout = [
			'name',
			'allow',
		] ),
	] ),
	Tab( _( 'Object' ), _( 'Object' ), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	] ),
]

mapping = udm_mapping.mapping()
mapping.register( 'name', 'cn', None, udm_mapping.ListToString )
mapping.register( 'allow', 'umcPolicyGrantedOperationSet' )
mapping.register( 'requiredObjectClasses', 'requiredObjectClasses' )
mapping.register( 'prohibitedObjectClasses', 'prohibitedObjectClasses' )
mapping.register( 'fixedAttributes', 'fixedAttributes' )
mapping.register( 'emptyAttributes', 'emptyAttributes' )

class object( simplePolicy ):
	module = module

	def __init__( self, co, lo, position, dn = '', superordinate = None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping = mapping
		self.descriptions = property_descriptions

		simplePolicy.__init__( self, co, lo, position, dn, superordinate, attributes )

	def _ldap_pre_create( self ):
		self.dn = '%s=%s,%s' % (mapping.mapName( 'name' ), mapping.mapValue( 'name', self.info[ 'name' ] ), self.position.getDn() )

	def _ldap_addlist( self ):
		return [ ( 'objectClass', [ 'top', 'univentionPolicy', 'umcPolicy' ] ) ]

def lookup( co, lo, filter_s, base = '', superordinate = None, scope = 'sub', unique = 0, required = 0, timeout = -1, sizelimit= 0 ):

	filter = udm_filter.conjunction( '&', [
		udm_filter.expression( 'objectClass', 'umcPolicy' )
		] )

	if filter_s:
		filter_p = udm_filter.parse( filter_s )
		udm_filter.walk( filter_p, udm_mapping.mapRewrite, arg = mapping )
		filter.expressions.append( filter_p )

	res=[]
	try:
		for dn, attrs in lo.search( unicode( filter ), base, scope, [], unique, required, timeout, sizelimit ):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	except:
		pass
	return res

def identify( dn, attr, canonical = 0 ):
	return 'umcPolicy' in attr.get( 'objectClass', [] )
