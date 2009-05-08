# -*- coding: utf-8 -*-
#
# Univention UDM Module
#  UDM module for UDM properties
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
import univention.admin.localization
import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

module='settings/extended_attribute'
operations=['add','edit','remove','search','move']
superordinate='settings/cn'
childs=0
short_description=_('Settings: extended attribute')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'shortDescription': univention.admin.property(
			short_description=_('Default short description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'longDescription': univention.admin.property(
			short_description=_('Default Long Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'translationShortDescription': univention.admin.property(
			short_description=_('Translation of short description '),
			long_description='',
			syntax=univention.admin.syntax.translationTupleShortDescription,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'translationLongDescription': univention.admin.property(
			short_description=_('Translation of long description '),
			long_description='',
			syntax=univention.admin.syntax.translationTupleLongDescription,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'translationTabName': univention.admin.property(
			short_description=_('Translation of tab name'),
			long_description='',
			syntax=univention.admin.syntax.translationTupleTabName,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'syntax': univention.admin.property(
			short_description=_('Syntax'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'hook': univention.admin.property(
			short_description=_('Hook'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'multivalue': univention.admin.property(
			short_description=_('Multivalue'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
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
			short_description=_('Position number on tab'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'tabAdvanced': univention.admin.property(
			short_description=_('Advanced tab'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'overwriteTab': univention.admin.property(
			short_description=_('Overwrite existing tab'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'overwritePosition': univention.admin.property(
			short_description=_('Overwrite existing widget'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ldapMapping': univention.admin.property(
			short_description=_('LDAP mapping'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'mayChange': univention.admin.property(
			short_description=_('May change'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'valueRequired': univention.admin.property(
			short_description=_('Value required'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
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
		),
	'version': univention.admin.property(
			short_description = _('Version of extended attribute'),
			long_description = '',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default='2',
		),
	'CLIName': univention.admin.property(
			short_description = _('UDM CLI name of extended attribute'),
			long_description = '',
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default='<name>',
		),
	'options': univention.admin.property(
			short_description=_('Options'),
			long_description='',
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'doNotSearch': univention.admin.property(
			short_description=_('Unsearchable'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}

layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
			[ univention.admin.field("name") ],
			[ univention.admin.field("shortDescription"), univention.admin.field("longDescription") ],
			[ univention.admin.field("translationShortDescription"), univention.admin.field("translationLongDescription") ]
			]),
	univention.admin.tab(_('UDM Web'),_('Settings for UDM web interface'),[
			[ univention.admin.field("tabName"), univention.admin.field("tabPosition") ],
			[ univention.admin.field("translationTabName"), [ univention.admin.field("overwritePosition"),
															  univention.admin.field("overwriteTab"),
															  univention.admin.field("tabAdvanced") ]  ]
			]),
	univention.admin.tab(_('UDM General'),_('UDM related settings'),[
			[ univention.admin.field("CLIName"), univention.admin.field("hook") ],
			[ univention.admin.field("options"), univention.admin.field("module") ]
			]),
	univention.admin.tab(_('Data type'),_('Data type definition'),[
			[univention.admin.field("syntax"), univention.admin.field("default") ],
			[univention.admin.field("multivalue"), univention.admin.field("valueRequired") ],
			[univention.admin.field("mayChange"),  univention.admin.field("doNotSearch") ]
			]),
	univention.admin.tab(_('LDAP'),_('LDAP mapping'),[
			[ univention.admin.field("objectClass"), univention.admin.field("ldapMapping") ],
			[ univention.admin.field("deleteObjectClass") ]
			])
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionUDMPropertyModule')
mapping.register('shortDescription', 'univentionUDMPropertyShortDescription', None, univention.admin.mapping.ListToString)
mapping.register('longDescription', 'univentionUDMPropertyLongDescription', None, univention.admin.mapping.ListToString)
mapping.register('objectClass', 'univentionUDMPropertyObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('deleteObjectClass', 'univentionUDMPropertyDeleteObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('default', 'univentionUDMPropertyDefault', None, univention.admin.mapping.ListToString)
mapping.register('syntax', 'univentionUDMPropertySyntax', None, univention.admin.mapping.ListToString)
mapping.register('hook', 'univentionUDMPropertyHook', None, univention.admin.mapping.ListToString)
mapping.register('ldapMapping', 'univentionUDMPropertyLdapMapping', None, univention.admin.mapping.ListToString)
mapping.register('multivalue', 'univentionUDMPropertyMultivalue', None, univention.admin.mapping.ListToString)
mapping.register('tabName', 'univentionUDMPropertyLayoutTabName', None, univention.admin.mapping.ListToString)
mapping.register('tabPosition', 'univentionUDMPropertyLayoutPosition', None, univention.admin.mapping.ListToString)
mapping.register('tabAdvanced', 'univentionUDMPropertyLayoutTabAdvanced', None, univention.admin.mapping.ListToString)
mapping.register('overwriteTab', 'univentionUDMPropertyLayoutOverwriteTab', None, univention.admin.mapping.ListToString)
mapping.register('overwritePosition', 'univentionUDMPropertyLayoutOverwritePosition', None, univention.admin.mapping.ListToString)
mapping.register('mayChange', 'univentionUDMPropertyValueMayChange', None, univention.admin.mapping.ListToString)
mapping.register('valueRequired', 'univentionUDMPropertyValueRequired', None, univention.admin.mapping.ListToString)
mapping.register('doNotSearch', 'univentionUDMPropertyDoNotSearch', None, univention.admin.mapping.ListToString)
mapping.register('version', 'univentionUDMPropertyVersion', None, univention.admin.mapping.ListToString)
mapping.register('CLIName', 'univentionUDMPropertyCLIName', None, univention.admin.mapping.ListToString)
mapping.register('options', 'univentionUDMPropertyOptions')

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
		return [('objectClass', ['top', 'univentionUDMProperty'] ) ]


	def open(self):
		# univentionUDMPropertyTranslation;entry-de-de: Meine Kurzbeschreibung 9
		# univentionUDMPropertyTranslation;entry-en-gb: This is my short description9

		univention.admin.handlers.simpleLdap.open(self)

		for transKey in [ 'ShortDescription', 'LongDescription', 'TabName' ]:
			translations = []
			keys = self.oldattr.keys()
			for key in self.oldattr.keys():
				if key.startswith('univentionUDMPropertyTranslation%s;entry-' % transKey):
					lang = '%s_%s' % (key[-5:-3].lower(), key[-2:].upper())
					txt = self.oldattr.get(key)[0]
					translations.append( (lang, txt) )

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'extended_attribute: added translations for %s: %s' % (transKey, str(translations)))
			self['translation%s' % transKey] = translations

		self.save()


	def _ldap_modlist(self):
		# univentionUDMPropertyShortTranslation;entry-de-de: Meine Kurzbeschreibung 9
		# univentionUDMPropertyShortTranslation;entry-en-gb: This is my short description9

		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		for transKey in [ 'ShortDescription', 'LongDescription', 'TabName' ]:
			if self.hasChanged( 'translation%s' % transKey ):
				oldlist = {}
				newlist = {}

				for lang, txt in self.oldinfo.get('translation%s' % transKey, []):
					lang = lang.replace('_','-')
					oldlist[lang] = txt
					if not lang in newlist:
						newlist[lang] = ''

				# duplicate lang entries will be removed due to use of dictionary
				for lang, txt in self.info.get('translation%s' % transKey, []):
					lang = lang.replace('_','-')
					newlist[lang] = txt
					if not lang in oldlist:
						oldlist[lang] = ''

				# modlist for new items
				for lang, txt in oldlist.items():
					if txt != newlist[lang]:
						ml.append( ('univentionUDMPropertyTranslation%s;entry-%s' % (transKey, lang), oldlist[lang], newlist[lang]) )

		return ml


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionUDMProperty'),
		univention.admin.filter.expression('univentionUDMPropertyVersion', '2'),
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

	return 'univentionUDMProperty' in attr.get('objectClass', []) and attr.get('univentionUDMPropertyVersion', ['0'])[0] == '2'
