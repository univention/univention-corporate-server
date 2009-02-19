# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for xconfig choices
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

module='settings/xconfig_choices'
superordinate='settings/cn'
childs=0
width="100"
operations=['search','edit']
short_description=_('Preferences: X Configuration Choices')
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
	'resolution': univention.admin.property(
			short_description=_('Resolution'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'colorDepth': univention.admin.property(
			short_description=_('Color Depth'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'mouseProtocol': univention.admin.property(
			short_description=_('Mouse Protocol'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'mouseDevice': univention.admin.property(
			short_description=_('Mouse Device'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'keyboardLayout': univention.admin.property(
			short_description=_('Keyboard Layout'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'keyboardVariant': univention.admin.property(
			short_description=_('Keyboard Variant'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'hSync': univention.admin.property(
			short_description=_('Horizontal Sync'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'vRefresh': univention.admin.property(
			short_description=_('Vertical Refresh'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'xModule': univention.admin.property(
			short_description=_('X Module'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'displaySize': univention.admin.property(
			short_description=_('Display Size (mm)'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
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
	univention.admin.tab(_('General'),_('X Configuration Choices'), [
		[univention.admin.field('name', hide_in_resultmode=1), univention.admin.field('xModule',width=width), univention.admin.field('filler', hide_in_normalmode=1) ],
		[univention.admin.field('resolution',width=width), univention.admin.field('colorDepth',width=width)],
		[univention.admin.field('mouseProtocol',width=width), univention.admin.field('mouseDevice',width=width)],
		[univention.admin.field('keyboardLayout',width=width), univention.admin.field('keyboardVariant',width=width)],
		[univention.admin.field('hSync',width=width), univention.admin.field('vRefresh',width=width)],
		[univention.admin.field('displaySize',width=width), univention.admin.field('filler')]
	])
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('xModule', 'univentionXModuleChoices')
mapping.register('resolution', 'univentionXResolutionChoices')
mapping.register('colorDepth', 'univentionXColorDepthChoices')
mapping.register('mouseProtocol', 'univentionXMouseProtocolChoices')
mapping.register('mouseDevice', 'univentionXMouseDeviceChoices')
mapping.register('keyboardLayout', 'univentionXKeyboardLayoutChoices')
mapping.register('keyboardVariant', 'univentionXKeyboardVariantChoices')
mapping.register('hSync', 'univentionXHSyncChoices')
mapping.register('vRefresh', 'univentionXVRefreshChoices')
mapping.register('displaySize', 'univentionXDisplaySizeChoices')


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
		return [('objectClass', ['top', 'univentionXConfigurationChoices'] ) ]
	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionXConfigurationChoices')
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
	
	return 'univentionXConfigurationChoices' in attr.get('objectClass', [])


