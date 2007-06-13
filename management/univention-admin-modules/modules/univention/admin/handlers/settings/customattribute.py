# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the custom attributes
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
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

module='settings/customattribute'
operations=['add','edit','remove','search','move']
superordinate='settings/cn'
childs=0
short_description=_('Settings: Attribute')
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
			identifies=1
		),
	'shortDescription': univention.admin.property(
			short_description=_('Short Description'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'longDescription': univention.admin.property(
			short_description=_('Long Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'syntax': univention.admin.property(
			short_description=_('Syntax'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'multivalue': univention.admin.property(
			short_description=_('Multivalue'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			default=0,
			identifies=0
		),
	'default': univention.admin.property(
			short_description=_('Default Value'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'tabName': univention.admin.property(
			short_description=_('Tab Name'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'tabPosition': univention.admin.property(
			short_description=_('Number on Tab'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ldapMapping': univention.admin.property(
			short_description=_('LDAP Mapping'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'objectClass': univention.admin.property(
			short_description=_('Object Class'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'deleteObjectClass': univention.admin.property(
			short_description=_('Delete Object Class'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'module': univention.admin.property(
			short_description=_('Needed Module'),
			long_description=_('"users/user" or "computer/thinclient"'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		)
}
layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
			[univention.admin.field("name"), univention.admin.field("module")],
			[univention.admin.field("tabName"), univention.admin.field("tabPosition")]]),
	univention.admin.tab(_('Description'),_('Description'),[
			[univention.admin.field("shortDescription"),univention.admin.field("longDescription")]]),
	univention.admin.tab(_('Object Classes'),_('Object classes needed for this Attribute'),[
			[univention.admin.field("objectClass"),
			 univention.admin.field("deleteObjectClass")]]),
	univention.admin.tab(_('LDAP Mapping'),_('Corresponding LDAP Attributes'),[
			[univention.admin.field("syntax"), univention.admin.field("ldapMapping")],
			[univention.admin.field("multivalue"), univention.admin.field("default")]])
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionAdminPropertyModule')
mapping.register('shortDescription', 'univentionAdminPropertyShortDescription', None, univention.admin.mapping.ListToString)
mapping.register('longDescription', 'univentionAdminPropertyLongDescription', None, univention.admin.mapping.ListToString)
mapping.register('objectClass', 'univentionAdminPropertyObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('deleteObjectClass', 'univentionAdminPropertyDeleteObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('default', 'univentionAdminPropertyDefault', None, univention.admin.mapping.ListToString)
mapping.register('syntax', 'univentionAdminPropertySyntax', None, univention.admin.mapping.ListToString)
mapping.register('ldapMapping', 'univentionAdminPropertyLdapMapping', None, univention.admin.mapping.ListToString)
mapping.register('multivalue', 'univentionAdminPropertyMultivalue', None, univention.admin.mapping.ListToString)
mapping.register('tabName', 'univentionAdminPropertyLayoutTabName', None, univention.admin.mapping.ListToString)
mapping.register('tabPosition', 'univentionAdminPropertyLayoutPosition', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
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

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [('objectClass', ['top', 'univentionAdminProperty'] ) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionAdminProperty'),
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

	return 'univentionAdminProperty' in attr.get('objectClass', [])
