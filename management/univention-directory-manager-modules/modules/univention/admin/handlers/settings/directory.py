# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for default directories
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
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

def plusBase(object, arg):
	return [arg+','+object.position.getDomain()]

module='settings/directory'
superordinate='settings/cn'
childs=0
operations=['search', 'edit']
short_description=_('Preferences: Default Container')
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
			default=('directory', [])
		),
	'policies': univention.admin.property(
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
	'mail': univention.admin.property(
			short_description=_('Mail Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'license': univention.admin.property(
			short_description=_('License Link'),
			long_description='',
			syntax=univention.admin.syntax.ldapDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		)
}
layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[[univention.admin.field("name")]]),
	univention.admin.tab(_('Users'),_('User Links'),[[univention.admin.field("users")]]),
	univention.admin.tab(_('Groups'),_('Group Links'),[[univention.admin.field("groups")]]),
	univention.admin.tab(_('Computers'),_('Computer Links'),[[univention.admin.field("computers")]]),
	univention.admin.tab(_('Policy'),_('Policy Links'),[[univention.admin.field("policies")]]),
	univention.admin.tab(_('DNS'),_('DNS Links'),[[univention.admin.field("dns")]]),
	univention.admin.tab(_('DHCP'),_('DHCP Links'),[[univention.admin.field("dhcp")]]),
	univention.admin.tab(_('Network'),_('Network Links'),[[univention.admin.field("networks")]]),
	univention.admin.tab(_('Shares'),_('Shares Links'),[[univention.admin.field("shares")]]),
	univention.admin.tab(_('Printers'),_('Printers Links'),[[univention.admin.field("printers")]]),
	univention.admin.tab(_('Mail'),_('Mail Links'),[[univention.admin.field("mail")]]),
	univention.admin.tab(_('License'),_('License Links'),[[univention.admin.field("license")]])
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('policies', 'univentionPolicyObject')
mapping.register('dns', 'univentionDnsObject')
mapping.register('dhcp', 'univentionDhcpObject')
mapping.register('users', 'univentionUsersObject')
mapping.register('groups', 'univentionGroupsObject')
mapping.register('computers', 'univentionComputersObject')
mapping.register('networks', 'univentionNetworksObject')
mapping.register('shares', 'univentionSharesObject')
mapping.register('printers', 'univentionPrintersObject')
mapping.register('mail', 'univentionMailObject')
mapping.register('license', 'univentionLicenseObject')

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

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='cn=%s,cn=univention,%s' % (self['name'], self.position.getDomain())

	def _ldap_addlist(self):
		return [('objectClass', ['top', 'univentionDirectory'] ) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionDirectory')
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

	return 'univentionDirectory' in attr.get('objectClass', [])
