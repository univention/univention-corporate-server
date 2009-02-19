# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the xfree configuration
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
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class xfreeFixedAttributes(univention.admin.syntax.select):
	name='xfreeFixedAttributes'
	choices=[
		('univentionXResolution',_('Resolution')),
		('univentionXColorDepth',_('Color depth')),
		('univentionXMouseProtocol',_('Mouse protocol')),
		('univentionXMouseDevice',_('Mouse device')),
		('univentionXKeyboardDevice',_('Keyboard layout')),
		('univentionXKeyboardVariant',_('Keyboard variant')),
		('univentionXHsync',_('Horizontal sync')),
		('univentionXVRefresh',_('Vertical refresh')),
		('univentionXModule',_('Graphics adapter driver')),
		('univentionXDisplaySize',_('Display size')),
		('univentionXVNCExportType',_('Enable VNC export')),
		('univentionXVNCExportViewonly',_('Viewonly VNC export')),
		('univentionXVideoRam',_('Amount of RAM on the graphics adapter')),
		]

module='policies/xfree'
operations=['add','edit','remove','search']

policy_oc='univentionPolicyXConfiguration'
policy_apply_to=["computers/thinclient", "computers/managedclient", "computers/mobileclient"]
policy_position_dn_prefix="cn=xfree"
usewizard=1
childs=0
short_description=_('Policy: Display')
policy_short_description=_('Display settings')
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
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXResolutionChoices'
		),
	'colorDepth': univention.admin.property(
			short_description=_('Color depth'),
			long_description='',
			syntax=univention.admin.syntax.XColorDepth,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXColorDepthChoices'
		),
	'mouseProtocol': univention.admin.property(
			short_description=_('Mouse protocol'),
			long_description='',
			syntax=univention.admin.syntax.XMouseProtocol,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXMouseProtocolChoices'
		),
	'mouseDevice': univention.admin.property(
			short_description=_('Mouse device'),
			long_description='',
			syntax=univention.admin.syntax.XMouseDevice,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXMouseDeviceChoices'
		),
	'keyboardLayout': univention.admin.property(
			short_description=_('Keyboard layout'),
			long_description='',
			syntax=univention.admin.syntax.XKeyboardLayout,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXKeyboardLayoutChoices'
		),
	'keyboardVariant': univention.admin.property(
			short_description=_('Keyboard variant'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXKeyboardVariantChoices'
		),
	'hSync': univention.admin.property(
			short_description=_('Horizontal sync'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXHSyncChoices'
		),
	'vRefresh': univention.admin.property(
			short_description=_('Vertical refresh'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXVRefreshChoices'
		),
	'xModule': univention.admin.property(
			short_description=_('Graphics adapter driver'),
			long_description='',
			syntax=univention.admin.syntax.XModule,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXModuleChoices'
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
			syntax=xfreeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty Attributes'),
			long_description='',
			syntax=xfreeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'displaySize': univention.admin.property(
			short_description=_('Display size (mm)'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXDisplaySizeChoices'
		),
	'vncExport': univention.admin.property(
			short_description=_('Enable VNC export'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('0', [])
		),
	'vncExportViewonly': univention.admin.property(
			short_description=_('Viewonly VNC export'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('1', [])
		),
	'videoRam': univention.admin.property(
			short_description=_('RAM on the graphics adapter in kB'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
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
	univention.admin.tab(_('General'),_('Display settings'), [
		[univention.admin.field('name', hide_in_resultmode=1), univention.admin.field('xModule'), univention.admin.field('filler', hide_in_normalmode=1) ],
		[univention.admin.field('resolution'), univention.admin.field('colorDepth')],
		[univention.admin.field('mouseProtocol'), univention.admin.field('mouseDevice')],
		[univention.admin.field('keyboardLayout'), univention.admin.field('keyboardVariant')],
		[univention.admin.field('hSync'), univention.admin.field('vRefresh')],
		[univention.admin.field('displaySize'), univention.admin.field('filler')],
		[univention.admin.field('videoRam')],
		[univention.admin.field('vncExport'), univention.admin.field('vncExportViewonly')],
	]),
	univention.admin.tab(_('Object'),_('Object'), [
		[univention.admin.field('requiredObjectClasses') , univention.admin.field('prohibitedObjectClasses') ],
		[univention.admin.field('fixedAttributes'), univention.admin.field('emptyAttributes')]
	], advanced = True),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('xModule', 'univentionXModule', None, univention.admin.mapping.ListToString)
mapping.register('resolution', 'univentionXResolution', None, univention.admin.mapping.ListToString)
mapping.register('colorDepth', 'univentionXColorDepth', None, univention.admin.mapping.ListToString)
mapping.register('mouseProtocol', 'univentionXMouseProtocol', None, univention.admin.mapping.ListToString)
mapping.register('mouseDevice', 'univentionXMouseDevice', None, univention.admin.mapping.ListToString)
mapping.register('keyboardLayout', 'univentionXKeyboardLayout', None, univention.admin.mapping.ListToString)
mapping.register('keyboardVariant', 'univentionXKeyboardVariant', None, univention.admin.mapping.ListToString)
mapping.register('hSync', 'univentionXHSync', None, univention.admin.mapping.ListToString)
mapping.register('vRefresh', 'univentionXVRefresh', None, univention.admin.mapping.ListToString)
mapping.register('displaySize', 'univentionXDisplaySize', None, univention.admin.mapping.ListToString)
mapping.register('vncExport', 'univentionXVNCExportType', None, univention.admin.mapping.ListToString)
mapping.register('videoRam', 'univentionXVideoRam', None, univention.admin.mapping.ListToString)
mapping.register('vncExportViewonly', 'univentionXVNCExportViewonly', None, univention.admin.mapping.ListToString)
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
		return [
			('objectClass', ['top', 'univentionPolicy', 'univentionPolicyXConfiguration'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyXConfiguration'),
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

	return 'univentionPolicyXConfiguration' in attr.get('objectClass', [])
