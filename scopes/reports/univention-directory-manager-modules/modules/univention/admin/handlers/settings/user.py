# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for user settings
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import sys, string
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization
import univention.admin.uldap

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

def plusBase(object, arg):
	return [arg+','+object.position.getDomain()]

module='settings/user'
superordinate='settings/admin'
childs=0
operations=['search', 'edit', 'remove']
short_description=_('Preferences: Univention Admin User Settings')
long_description=''
options={
}
property_descriptions={
	'username': univention.admin.property(
			short_description=_('Username'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'listWizards': univention.admin.property(
			short_description=_('Visible Univention Admin Wizards'),
			long_description='',
			syntax=univention.admin.syntax.univentionAdminWizards,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'selfAttributes': univention.admin.property(
			short_description=_('Accessible User Attributes'),
			long_description='',
			syntax=univention.admin.syntax.userAttributeList,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'listAttributes': univention.admin.property(
			short_description = _( 'Show these attributes in search results' ),
			long_description= '' '',
			syntax=univention.admin.syntax.listAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'listNavigationAttributes': univention.admin.property(
			short_description = _( 'Show these attributes in the navigation' ),
			long_description= '' '',
			syntax=univention.admin.syntax.listAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'listWebModules': univention.admin.property(
			short_description=_('Visible Univention Admin Modules'),
			long_description='',
			syntax=univention.admin.syntax.univentionAdminWebModules,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'baseDN': univention.admin.property(
			short_description=_('LDAP Base DN'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'policy': univention.admin.property(
			short_description=_('Policy Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dns': univention.admin.property(
			short_description=_('DNS Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dhcp': univention.admin.property(
			short_description=_('DHCP Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'users': univention.admin.property(
			short_description=_('User Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'groups': univention.admin.property(
			short_description=_('Group Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'computers': univention.admin.property(
			short_description=_('Computer Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'networks': univention.admin.property(
			short_description=_('Network Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'shares': univention.admin.property(
			short_description=_('Share Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'printers': univention.admin.property(
			short_description=_('Printer Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'filler': univention.admin.property(
			short_description='',
			long_description='',
			syntax=univention.admin.syntax.none,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1
		)
}
layout=[
	univention.admin.tab(_('Univention Admin'),_('Univention Admin User Settings'),[
		[univention.admin.field("username"), univention.admin.field('baseDN')],
		[univention.admin.field('listWizards'), univention.admin.field('listWebModules')],
		[ univention.admin.field( 'selfAttributes' ), univention.admin.field( 'listAttributes' )],
		[ univention.admin.field( 'listNavigationAttributes' ), univention.admin.field( 'filler' )],
	]),
# TODO: default container
#	univention.admin.tab(_('Users'),_('User Links'),[[univention.admin.field("users")]]),
#	univention.admin.tab(_('Groups'),_('Group Links'),[[univention.admin.field("groups")]]),
#	univention.admin.tab(_('Computers'),_('Computer Links'),[[univention.admin.field("computers")]]),
#	univention.admin.tab(_('Policy'),_('Policy Links'),[[univention.admin.field("policy")]]),
#	univention.admin.tab(_('DNS'),_('DNS Links'),[[univention.admin.field("dns")]]),
#	univention.admin.tab(_('DHCP'),_('DHCP Links'),[[univention.admin.field("dhcp")]]),
#	univention.admin.tab(_('Network'),_('Network Links'),[[univention.admin.field("networks")]]),
#	univention.admin.tab(_('Shares'),_('Shares Links'),[[univention.admin.field("shares")]]),
#	univention.admin.tab(_('Printers'),_('Printers Links'),[[univention.admin.field("printers")]]),
]

mapping=univention.admin.mapping.mapping()
mapping.register('username', 'uid', None, univention.admin.mapping.ListToString)
mapping.register('listDNs', 'univentionAdminListDNs')
mapping.register('listWizards', 'univentionAdminListWizards')
mapping.register('selfAttributes', 'univentionAdminSelfAttributes')
mapping.register('listAttributes', 'univentionAdminListAttributes')
mapping.register('listNavigationAttributes', 'univentionAdminListBrowseAttributes')
mapping.register('listWebModules', 'univentionAdminListWebModules')
mapping.register('baseDN', 'univentionAdminBaseDN', None, univention.admin.mapping.ListToString)
mapping.register('policy', 'univentionPolicyObject')
mapping.register('dns', 'univentionDnsObject')
mapping.register('dhcp', 'univentionDhcpObject')
mapping.register('users', 'univentionUsersObject')
mapping.register('groups', 'univentionGroupsObject')
mapping.register('computers', 'univentionComputersObject')
mapping.register('networks', 'univentionNetworksObject')
mapping.register('shares', 'univentionSharesObject')
mapping.register('printers', 'univentionPrintersObject')

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self.superordinate=superordinate
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

		self._really_exists = self._exists
		# object does not exist
		if not self.exists():
			self.__read_policy()
			# required: otherwise _ldap_pre_modify is not invoked
			self._exists = True

	def __read_policy( self ):
		self[ 'username' ] = univention.admin.uldap.explodeDn( self.dn, notypes = True )[ 0 ]
		filter = univention.admin.filter.conjunction( '&', [
			univention.admin.filter.expression( 'uid', self[ 'username' ] ),
			univention.admin.filter.expression( 'objectClass', 'person' )
			])
		result = self.lo.searchDn( unicode( filter ), '', 'sub', 1, 0, -1, 0 )
		if result:
			policy = self.lo.getPolicies( result[ 0 ] )
			if policy.has_key( 'univentionPolicyAdminSettings' ):
				settings = policy[ 'univentionPolicyAdminSettings' ]
				if settings.has_key( 'univentionAdminListWizards' ):
					self[ 'listWizards' ] = settings[ 'univentionAdminListWizards' ][ 'value' ]
				if settings.has_key( 'univentionAdminListWebModules' ):
					self[ 'listWebModules' ] = settings[ 'univentionAdminListWebModules' ][ 'value' ]
				if settings.has_key( 'univentionAdminSelfAttributes' ):
					self[ 'selfAttributes' ] = settings[ 'univentionAdminSelfAttributes' ][ 'value' ]
				# this is currently not in use
				if settings.has_key( 'univentionAdminListDNs' ):
					self[ 'listDNS' ] = settings[ 'univentionAdminListDNs' ][ 'value' ]
				if settings.has_key( 'univentionAdminBaseDN' ):
					self[ 'baseDN' ] = settings[ 'univentionAdminBaseDN' ][ 'value' ][ 0 ]

	def exists(self):
		return self._exists

	def _modify( self, modify_childs = 1, ignore_license = 0 ):
		if not self._really_exists:
			self._exists = False
			# if anything has changed, the object must be created
			for key in self.info.keys():
				if self.hasChanged( key ):
					self.oldinfo = {}
					self.create()
					self._really_exists = True
					break
		if self._really_exists:
			univention.admin.handlers.simpleLdap._modify( self, modify_childs, ignore_license )

	def _ldap_pre_create(self):
		self.dn='%s=%s,cn=admin-settings,cn=univention,%s' % \
				( mapping.mapName( 'username' ), mapping.mapValue( 'username', self.info[ 'username' ] ), self.position.getDn() )

	def _ldap_addlist(self):
		return [('objectClass', ['top', 'univentionAdminUserSettings'] ) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionAdminUserSettings')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):

	return 'univentionAdminUserSettings' in attr.get('objectClass', [])
