# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  admin policy for the user settings
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

import sys, string
sys.path=['.']+sys.path
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class adminFixedAttributes(univention.admin.syntax.select):
        name='adminFixedAttributes'
	choices=[
	('univentionAdminListWizards',_('List of  Univention Directory Manager wizards')),
	('univentionAdminListWebModules',_('List of Univention Directory Manager modules')),
	('univentionAdminListAttributes', _( 'Show these attributes in search results' )),
	('univentionAdminListBrowseAttributes', _( 'Show these attributes in the navigation' )),
	('univentionAdminBaseDN',_('LDAP Base DN')),
	('univentionAdminMayOverrideSettings',_('User may override policy')),
	('policy',_('Default policy containers')),
	('dns',_('Default DNS containers')),
	('dhcp',_('Default DHCP containers')),
	('users',_('Default users container')),
	('groups',_('Default groups container')),
	('computers',_('Default computers container')),
	('networks',_('Default networks container')),
	('shares',_('Default shares container')),
	('printers',_('Default printers container')),
	]


module='policies/admin_user'
operations=['add','edit','remove','search']

policy_oc='univentionPolicyAdminSettings'
policy_apply_to=["users/user"]
policy_position_dn_prefix="cn=user,cn=admin"
usewizard=1
childs=0
short_description=_('Policy: Univention Directory Manager View')
policy_short_description=_('Univention Directory Manager View')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'listWizards': univention.admin.property(
			short_description=_('Visible Univention Directory Manager wizards'),
			long_description='',
			syntax=univention.admin.syntax.univentionAdminWizards,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'listWebModules': univention.admin.property(
			short_description=_('Visible Univention Directory Manager modules'),
			long_description='',
			syntax=univention.admin.syntax.univentionAdminWebModules,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'baseDN': univention.admin.property(
			short_description=_('LDAP base DN'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'mayOverrideSettings': univention.admin.property(
			short_description=_('Allow personal Univention Directory Manager settings'),
			long_description=_('If this option is set users can be provided with the possibility to create their own personal Univention Directory Manager Settings'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'selfAttributes': univention.admin.property(
			short_description = _( 'Visible user attributes' ),
			long_description=_('Define user attributes that may be altered by user'),
			syntax=univention.admin.syntax.userAttributeList,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
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
	'policy': univention.admin.property(
			short_description=_('policy link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dns': univention.admin.property(
			short_description=_('DNS link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dhcp': univention.admin.property(
			short_description=_('DHCP link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'users': univention.admin.property(
			short_description=_('users link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'groups': univention.admin.property(
			short_description=_('groups link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'computers': univention.admin.property(
			short_description=_('computers link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'networks': univention.admin.property(
			short_description=_('networks link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'shares': univention.admin.property(
			short_description=_('shares link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'printers': univention.admin.property(
			short_description=_('printers link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),

	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attributes'),
			long_description='',
			syntax=adminFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty attributes'),
			long_description='',
			syntax=adminFixedAttributes,
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
	univention.admin.tab(_('General'),_('Univention Directory Manager settings'), [
		[univention.admin.field('name', hide_in_resultmode=1), univention.admin.field('baseDN')],
		[univention.admin.field('listWizards'), univention.admin.field('listWebModules')],
		[univention.admin.field('selfAttributes'), univention.admin.field('listAttributes')],
		[univention.admin.field('listNavigationAttributes')],
		[univention.admin.field('mayOverrideSettings'), univention.admin.field("filler")]],
	),
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
	univention.admin.tab(_('Object'),_('Object'), [
		[univention.admin.field('requiredObjectClasses') , univention.admin.field('prohibitedObjectClasses') ],
		[univention.admin.field('fixedAttributes'), univention.admin.field('emptyAttributes')]
	], advanced = True),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('listDNs', 'univentionAdminListDNs')
mapping.register('listWizards', 'univentionAdminListWizards')
mapping.register('listWebModules', 'univentionAdminListWebModules')
mapping.register('selfAttributes', 'univentionAdminSelfAttributes')
mapping.register('listAttributes', 'univentionAdminListAttributes')
mapping.register('listNavigationAttributes', 'univentionAdminListBrowseAttributes')
mapping.register('baseDN', 'univentionAdminBaseDN', None, univention.admin.mapping.ListToString)
mapping.register('mayOverrideSettings', 'univentionAdminMayOverrideSettings', None, univention.admin.mapping.ListToString)
mapping.register('policy', 'univentionPolicyObject')
mapping.register('dns', 'univentionDnsObject')
mapping.register('dhcp', 'univentionDhcpObject')
mapping.register('users', 'univentionUsersObject')
mapping.register('groups', 'univentionGroupsObject')
mapping.register('computers', 'univentionComputersObject')
mapping.register('networks', 'univentionNetworksObject')
mapping.register('shares', 'univentionSharesObject')
mapping.register('printers', 'univentionPrintersObject')
mapping.register('requiredObjectClasses', 'requiredObjectClasses')
mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
mapping.register('fixedAttributes', 'fixedAttributes')
mapping.register('emptyAttributes', 'emptyAttributes')

class object(univention.admin.handlers.simplePolicy):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionPolicy', 'univentionPolicyAdminSettings']) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyAdminSettings')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
			res.append(object(co, lo, None, dn))
	except:
		pass
	return res

def identify(dn, attr, canonical=0):
	return 'univentionPolicyAdminSettings' in attr.get('objectClass', [])
