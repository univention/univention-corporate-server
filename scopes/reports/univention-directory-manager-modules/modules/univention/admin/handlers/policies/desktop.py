# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the desktop settings
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
sys.path=['.']+sys.path
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class desktopFixedAttributes(univention.admin.syntax.select):
	name='desktopFixedAttributes'
	choices=[(('univentionDesktopLanguage'),_('Desktop Language')),
			 (('univentionDesktopProfile'),_('Desktop Profile'))
			 ]
			

module='policies/desktop'
operations=['add','edit','remove','search']

policy_oc='univentionPolicyDesktop'
policy_apply_to=["users/user"]
policy_position_dn_prefix="cn=desktop"
usewizard=1
childs=0
short_description=_('Policy: Desktop')
policy_short_description=_('Desktop Settings')
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
	'language': univention.admin.property(
			short_description=_('Desktop Language'),
			long_description='',
			syntax=univention.admin.syntax.language,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'profile': univention.admin.property(
			short_description=_('Desktop Profile'),
			long_description='',
			syntax=univention.admin.syntax.kdeProfiles,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'logonScripts': univention.admin.property(
			short_description=_('Logon Scripts'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'logoutScripts': univention.admin.property(
			short_description=_('Logout Scripts'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required Object Classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Prohibited Object Classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed Attributes'),
			long_description='',
			syntax=desktopFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty Attributes'),
			long_description='',
			syntax=desktopFixedAttributes,
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
	univention.admin.tab(_('General'),_('Desktop Settings'), [
		[univention.admin.field('name', hide_in_resultmode=1), univention.admin.field('language'), univention.admin.field("filler", hide_in_normalmode=1) ],
		[univention.admin.field('profile'), univention.admin.field("filler")],
		[univention.admin.field('logonScripts'), univention.admin.field("filler")],
		[univention.admin.field("logoutScripts"), univention.admin.field("filler")],
	]),
	univention.admin.tab(_('Object'),_('Object'), [
		[univention.admin.field('requiredObjectClasses') , univention.admin.field('prohibitedObjectClasses') ],
		[univention.admin.field('fixedAttributes'), univention.admin.field("emptyAttributes")]
	]),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('language', 'univentionDesktopLanguage', None, univention.admin.mapping.ListToString)
mapping.register('profile', 'univentionDesktopProfile')
mapping.register('logonScripts', 'univentionDesktopLogonScripts')
mapping.register('logoutScripts', 'univentionDesktopLogoutScripts')
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
		return [ ('objectClass', ['top', 'univentionPolicy', 'univentionPolicyDesktop']) ]
	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyDesktop')
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
	return 'univentionPolicyDesktop' in attr.get('objectClass', [])
