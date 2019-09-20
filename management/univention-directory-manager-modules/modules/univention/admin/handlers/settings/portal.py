# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  directory manager module for Univention Portal
#
# Copyright 2017-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import json
from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/portal'
superordinate = 'settings/cn'
default_containers = ['cn=portal,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Portal: Portal')
object_name = _('Portal')
object_name_plural = _('Portals')
long_description = _('Object that feeds everything in https://fqdn/univention/portal')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPortal'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Internal name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'displayName': univention.admin.property(
		short_description=_('Display Name'),
		long_description=_('Headline of the portal. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		required=True,
	),
	'showMenu': univention.admin.property(
		short_description=_('Show menu'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'showSearch': univention.admin.property(
		short_description=_('Show search'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'showLogin': univention.admin.property(
		short_description=_('Show login'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'showApps': univention.admin.property(
		short_description=_('Show apps'),
		long_description=_('Shows links to locally installed Apps'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'showServers': univention.admin.property(
		short_description=_('Show servers'),
		long_description=_('Shows links to all UCS servers'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'background': univention.admin.property(
		short_description=_('Background'),
		long_description=_('Background image of the Portal'),
		syntax=univention.admin.syntax.Base64BaseUpload,
		dontsearch=True,
	),
	'logo': univention.admin.property(
		short_description=_('Portal logo'),
		long_description=_('Logo image for the portal.'),
		syntax=univention.admin.syntax.Base64BaseUpload,
		dontsearch=True,
	),
	'cssBackground': univention.admin.property(
		short_description=_('CSS background'),
		long_description=_("Style definition for the CSS 'background' property which will be applied to the portal page, e.g. linear-gradient(black, white)"),
		syntax=univention.admin.syntax.TwoString,
		dontsearch=True,
	),
	'fontColor': univention.admin.property(
		short_description=_('Font color'),
		long_description=_('Defines the color which is used for the fonts on the portal page as well as the icons in the header.'),
		syntax=univention.admin.syntax.PortalFontColor,
		default='black',
		dontsearch=True,
	),
	'portalComputers': univention.admin.property(
		short_description=_('Show on server'),
		long_description=_('This portal will be used as start site for the given server'),
		syntax=univention.admin.syntax.PortalComputer,
		multivalue=True,
		dontsearch=True,
	),
	'ensureLogin': univention.admin.property(
		short_description=_('Redirect anonymous visitors to the login'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
		dontsearch=True,
	),
	'anonymousEmpty': univention.admin.property(
		syntax=univention.admin.syntax.LocalizedAnonymousEmpty,
		multivalue=True,
		dontsearch=True,
	),
	'autoLayoutCategories': univention.admin.property(
		short_description=_('The categories are displayed side by side if there is enough space'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
		dontsearch=True,
	),
	# 'portalEntriesOrder' - deprecated by 'content' of settings/portal
	'portalEntriesOrder': univention.admin.property(
		short_description=_('Portal entries order'),
		long_description=_('The order in which the portal entries are shown on this portal'),
		syntax=univention.admin.syntax.PortalEntries,
		multivalue=True,
	),
	'links': univention.admin.property(
		short_description=_('Portal links'),
		long_description=_('List of static links shown on this portal. Only those links for the selected locale are shown (e.g.,: en_US, de_DE).'),
		syntax=univention.admin.syntax.PortalLinks,
		multivalue=True,
	),
	'content': univention.admin.property(
		short_description=_('Portal content'),
		syntax=univention.admin.syntax.PortalCategorySelection,
	),
	'defaultLinkTarget': univention.admin.property(
		short_description=_('Default browser tab for portal entries'),
		syntax=univention.admin.syntax.PortalDefaultLinkTarget,
		default='samewindow',
		dontsearch=True,
	),
}

layout = [
	Tab(_('General'), _('Portal options'), layout=[
		Group(_('Name'), layout=[
			['name'],
			['displayName'],
		]),
		Group(_('Visibility'), layout=[
			['portalComputers'],
		]),
		Group(_('Appearance'), layout=[
			['logo'],
			['background'],
			['cssBackground'],
			['fontColor'],
			['autoLayoutCategories'],
		]),
		Group(_('General Content'), layout=[
			# ["showMenu"],
			# ["showSearch"],
			# ["showLogin"],
			['defaultLinkTarget'],
			['showApps'],
			# ["showServers"],
			['links'],
		]),
	]),
	Tab(_('Portal categories and entries'), _('The categories and entries that are shown on this portal'), layout=[
		['content'],
	]),
	Tab(_('Manage anonymous visitors'), _('Manage anonymous visitors'), layout=[
		Group(_('Login'), layout=[
			['ensureLogin'],
		]),
		Group(_('Message when the portal is empty'), layout=[
			['anonymousEmpty'],
		]),
	]),
]


def mapLinkValue(vals):
	return ['$$'.join(val) for val in vals]


def unmapLinkValue(vals):
	return [val.split('$$', 3) for val in vals]


def mapTranslationValue(vals):
	return [' '.join(val) for val in vals]


def unmapTranslationValue(vals):
	return [val.split(' ', 1) for val in vals]


def mapContent(vals):
	return json.dumps(vals)


def unmapContent(vals):
	return json.loads(vals[0])


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionPortalDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('showMenu', 'univentionPortalShowMenu', None, univention.admin.mapping.ListToString)
mapping.register('showSearch', 'univentionPortalShowSearch', None, univention.admin.mapping.ListToString)
mapping.register('showLogin', 'univentionPortalShowLogin', None, univention.admin.mapping.ListToString)
mapping.register('showApps', 'univentionPortalShowApps', None, univention.admin.mapping.ListToString)
mapping.register('showServers', 'univentionPortalShowServers', None, univention.admin.mapping.ListToString)
mapping.register('ensureLogin', 'univentionPortalEnsureLogin', None, univention.admin.mapping.ListToString)
mapping.register('anonymousEmpty', 'univentionPortalAnonymousEmpty', mapTranslationValue, unmapTranslationValue)
mapping.register('autoLayoutCategories', 'univentionPortalAutoLayoutCategories', None, univention.admin.mapping.ListToString)
mapping.register('background', 'univentionPortalBackground', None, univention.admin.mapping.ListToString)
mapping.register('cssBackground', 'univentionPortalCSSBackground', None, univention.admin.mapping.ListToString)
mapping.register('fontColor', 'univentionPortalFontColor', None, univention.admin.mapping.ListToString)
mapping.register('logo', 'univentionPortalLogo', None, univention.admin.mapping.ListToString)
mapping.register('portalEntriesOrder', 'univentionPortalEntriesOrder')
mapping.register('links', 'univentionPortalLinks', mapLinkValue, unmapLinkValue)
mapping.register('content', 'univentionPortalContent', mapContent, unmapContent)
mapping.register('defaultLinkTarget', 'univentionPortalDefaultLinkTarget', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		super(object, self).open()
		self['portalComputers'] = self.lo.searchDn(filter=filter_format('(&(objectClass=univentionPortalComputer)(univentionComputerPortal=%s))', [self.dn]))
		self.save()

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		self.__update_deprecated_property__portal_entries_order__of__self()

	def _ldap_pre_modify(self):
		self.__update_deprecated_property__portal_entries_order__of__self()

	def _ldap_post_create(self):
		self.__update_portal_computers()
		self.__update_deprecated_property__portal__of__portal_entry()

	def _ldap_post_modify(self):
		self.__update_portal_computers()
		self.__update_deprecated_property__portal__of__portal_entry()

	def __update_deprecated_property__portal_entries_order__of__self(self):
		# Use the order of the settings/portal_entry objects in the 'content' property
		# for the deprecated 'portalEntriesOrder' property.
		# Be aware that 'portalEntriesOrder' will not get updated if
		# the settings/portal_entry objects are the same but only ordering changes.
		# ['A', 'B', 'C']
		# ['B', 'A', 'C'] # this will be ignored, since only ordering changed
		# This was previously bypassed by unsetting 'portalEntriesOrder' and then resetting with the new order
		if self.hasChanged('content'):
			content = self.info.get('content', [])

			# Workaround for Bug #47872 - Comment #1
			if (len(content) == 1 and len(content[0][1]) == 1 and content[0][0].startswith('cn=admin,') and content[0][1][0].startswith('cn=univentionblog,')):
				return

			new_order = [entry for category, entries in content for entry in entries]
			new_order_no_duplicates = []
			for entry in new_order:
				if entry not in new_order_no_duplicates:
					new_order_no_duplicates.append(entry)
			self['portalEntriesOrder'] = new_order_no_duplicates

	def __update_portal_computers(self):
		if self.exists():
			# case coming from _ldap_post_modify
			old_portal_computers = self.oldinfo.get('portalComputers', [])
		else:
			# case coming from _ldap_post_create
			old_portal_computers = []
		new_portal_computers = self.info.get('portalComputers', [])

		# set portal attribute of old computers to blank
		for computer in old_portal_computers:
			if computer not in new_portal_computers:
				try:
					compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
					# initialize module of the computer obj for extended attributes
					compmod = univention.admin.modules.get(compobj.module)
					if not compmod.initialized:
						univention.admin.modules.init(self.lo, self.position, compmod)
						compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
				except univention.admin.uexceptions.noObject:
					continue
				compobj.open()
				compobj['portal'] = ''
				compobj.modify()

		# set portal attribute of new computers to this portal
		for computer in new_portal_computers:
			if computer not in old_portal_computers:
				try:
					compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
					# initialize module of the computer obj for extended attributes
					compmod = univention.admin.modules.get(compobj.module)
					if not compmod.initialized:
						univention.admin.modules.init(self.lo, self.position, compmod)
						compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
				except univention.admin.uexceptions.noObject:
					continue
				compobj.open()
				compobj['portal'] = self.dn
				compobj.modify()

	def __update_deprecated_property__portal__of__portal_entry(self):
		# Remove this portal from the 'portal' property of settings/portal_entry objects
		# if they were removed from the 'content' property.
		# Add this portal if they were added to 'content'.

		if not self.hasChanged('content'):
			return

		portal_entry_mod = univention.admin.modules.get('settings/portal_entry')

		old_content = self.oldinfo.get('content', [])
		old_entries = [entry for category, entries in old_content for entry in entries]
		new_content = self.info.get('content', [])
		new_entries = [entry for category, entries in new_content for entry in entries]

		# remove this portal from removed entries
		removed_entries = [entry for entry in old_entries if entry not in new_entries]
		for entry_dn in removed_entries:
			try:
				entry_obj = univention.admin.objects.get(portal_entry_mod, None, self.lo, position='', dn=entry_dn)
			except univention.admin.uexceptions.noObject:
				continue
			else:
				entry_obj.open()
				old_portal = entry_obj.info.get('portal', [])
				new_portal = [portal for portal in old_portal if not self.lo.compare_dn(portal, self.dn)]
				if new_portal != old_portal:
					entry_obj['portal'] = new_portal
					entry_obj.modify()

		# add this portal to added entries
		added_entries = [entry for entry in new_entries if entry not in old_entries]
		for entry_dn in added_entries:
			try:
				entry_obj = univention.admin.objects.get(portal_entry_mod, None, self.lo, position='', dn=entry_dn)
			except univention.admin.uexceptions.noObject:
				continue
			else:
				entry_obj.open()
				old_portal = entry_obj.info.get('portal', [])
				new_portal = old_portal + ([self.dn] if self.dn not in old_portal else [])
				if old_portal != new_portal:
					entry_obj['portal'] = new_portal
					entry_obj.modify()

	def _ldap_post_remove(self):
		for obj in univention.admin.modules.lookup('settings/portal_entry', None, self.lo, scope='sub', filter=filter_format('portal=%s', [self.dn])):
			obj.open()
			obj['portal'] = [x for x in obj.info.get('portal', []) if not self.lo.compare_dn(x, self.dn)]
			obj.modify()

	def _ldap_post_move(self, olddn):
		for obj in univention.admin.modules.lookup('settings/portal_entry', None, self.lo, scope='sub', filter=filter_format('portal=%s', [olddn])):
			obj.open()
			obj['portal'] = [x for x in obj.info.get('portal', []) + [self.dn] if not self.lo.compare_dn(x, olddn)]
			obj.modify()


lookup = object.lookup
identify = object.identify
