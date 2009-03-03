# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for license handling
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

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

module='settings/license'
superordinate='settings/cn'
operations=['remove','search']

childs=0
short_description=_('Settings: License')
long_description=_('Univention License')
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description=_('Name'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'expires': univention.admin.property(
			short_description=_('Expiry date'),
			long_description=_('License Expiration Date'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=0,
		),
	'module': univention.admin.property(
			short_description=_('Module'),
			long_description=_('Module the license is valid for'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=0,
		),
	'base': univention.admin.property(
			short_description=_('Base DN'),
			long_description=_('Base DN the license is valid for'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=0,
		),
	'signature': univention.admin.property(
			short_description=_('Signature'),
			long_description=_('This Signature is used to verify the authenticity of the license.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=0,
		),
	'filler': univention.admin.property(
			short_description=_('None'),
			long_description='',
			syntax=univention.admin.syntax.none,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			dontsearch=1
		),
	'accounts': univention.admin.property(
			short_description=_('Max. user accounts'),
			long_description=_('Maximum number of user accounts managed with the Univention infrastructure'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			identifies=0,
		),
	'clients': univention.admin.property(
			short_description=_('Max. clients'),
			long_description=_('Maximum number of client hosts managed with the Univention infrastructure'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			identifies=0,
		),
	'groupwareaccounts': univention.admin.property(
			short_description=_('Max. groupware accounts'),
			long_description=_('Maximum number of groupware accounts managed with the Univention infrastructure'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			identifies=0,
		),
	'desktops': univention.admin.property(
			short_description=_('Max. desktops'),
			long_description=_('Maximum number of Univention desktop accounts managed with the Univention infrastructure'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			identifies=0,
		),
	'productTypes': univention.admin.property(
			short_description=_('Valid product types'),
			long_description=_('Product types this license allows.'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=0,
			identifies=0,
		),
}
layout=[
	univention.admin.tab(_('License'),_('Licensing Information'), [
		[univention.admin.field('name'), univention.admin.field('module')],
		[univention.admin.field('expires'), univention.admin.field('base')],
		[univention.admin.field('accounts'), univention.admin.field('groupwareaccounts')],
		[univention.admin.field('clients'), univention.admin.field('desktops')],
		[univention.admin.field('productTypes'), univention.admin.field('filler')],
		[univention.admin.field('signature'), univention.admin.field('filler')],
	]),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('expires', 'univentionLicenseEndDate', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionLicenseModule', None, univention.admin.mapping.ListToString)
mapping.register('base', 'univentionLicenseBaseDN', None, univention.admin.mapping.ListToString)
mapping.register('signature', 'univentionLicenseSignature', None, univention.admin.mapping.ListToString)
mapping.register('accounts', 'univentionLicenseAccounts', None, univention.admin.mapping.ListToString)
mapping.register('groupwareaccounts', 'univentionLicenseGroupwareAccounts', None, univention.admin.mapping.ListToString)
mapping.register('clients', 'univentionLicenseClients', None, univention.admin.mapping.ListToString)
mapping.register('desktops', 'univentionLicenseuniventionDesktops', None, univention.admin.mapping.ListToString)
mapping.register('productTypes', 'univentionLicenseType')

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
		return [ ('objectClass', ['top', 'univentionLicense']) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionLicense')
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
	return 'univentionLicense' in attr.get('objectClass', [])
