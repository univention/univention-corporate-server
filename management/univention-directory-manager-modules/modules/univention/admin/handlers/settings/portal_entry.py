# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  directory manager module for Portal entries
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

from ldap.dn import escape_dn_chars

from univention.admin.layout import Tab, Group
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/portal_entry'
superordinate = 'settings/cn'
default_containers = ['cn=portal,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Portal: Entry')
object_name = _('Portal entry')
object_name_plural = _('Portal entries')
long_description = _('One link in https://fqdn/univention/portal. Belongs to one (or more) settings/portal')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPortalEntry'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Internal name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'displayName': univention.admin.property(
		short_description=_('Display Name'),
		long_description=_('Headline of the entry. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		required=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('Description of the entry. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDescription,
		multivalue=True,
		required=True,
	),
	'favorite': univention.admin.property(
		short_description=_('Favorite'),
		long_description=_('Shown in the favorite section'),
		syntax=univention.admin.syntax.TrueFalseUp,
	),
	# 'category' - deprecated in favor of 'content' of settings/portal
	'category': univention.admin.property(
		short_description=_('Category'),
		long_description='',
		syntax=univention.admin.syntax.PortalCategory,
		default='service',
		dontsearch=True,
	),
	'link': univention.admin.property(
		short_description=_('Link'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		required=True,
	),
	# 'portal' - deprecated in favor of 'content' of settings/portal
	'portal': univention.admin.property(
		short_description=_('Portals'),
		long_description=_('Shown on portals'),
		syntax=univention.admin.syntax.Portals,
		multivalue=True,
	),
	'authRestriction': univention.admin.property(
		short_description=_('Authorization'),
		long_description=_('Deprecated by allowedGroups'),
		syntax=univention.admin.syntax.AuthRestriction,
		default='anonymous',
	),
	'allowedGroups': univention.admin.property(
		short_description=_('Restrict visibility to groups'),
		long_description=_('If one or more groups are selected then the portal entry will only be visible to logged in users that are in any of the selected groups. If no groups are selected then the portal entry is always visible.'),
		syntax=univention.admin.syntax.GroupDNOrEmpty,
		multivalue=True,
	),
	'activated': univention.admin.property(
		short_description=_('Activated'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'icon': univention.admin.property(
		short_description=_('Icon'),
		long_description='',
		syntax=univention.admin.syntax.Base64BaseUpload,
		dontsearch=True,
	),
	'linkTarget': univention.admin.property(
		short_description=_('Browser tab when opening link'),
		syntax=univention.admin.syntax.PortalEntryLinkTarget,
		default='useportaldefault',
		dontsearch=True,
	),
}

layout = [
	Tab(_('General'), _('Entry options'), layout=[
		Group(_('General'), layout=[
			["name"],
			["icon"],
		]),
		Group(_('Display name'), layout=[
			["displayName"],
		]),
		Group(_('Description'), layout=[
			["description"],
		]),
		Group(_('Link'), layout=[
			["linkTarget"],
			["link"],
		]),
		Group(_('Advanced'), layout=[
			["activated"],
			["allowedGroups"],
			#["authRestriction"],
			#["favorite"],
		]),
	]),
]


def mapTranslationValue(vals):
	return [' '.join(val) for val in vals]


def unmapTranslationValue(vals):
	return [val.split(' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionPortalEntryDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('description', 'univentionPortalEntryDescription', mapTranslationValue, unmapTranslationValue)
mapping.register('favorite', 'univentionPortalEntryFavorite', None, univention.admin.mapping.ListToString)
mapping.register('category', 'univentionPortalEntryCategory', None, univention.admin.mapping.ListToString)
mapping.register('link', 'univentionPortalEntryLink')
mapping.register('linkTarget', 'univentionPortalEntryLinkTarget', None, univention.admin.mapping.ListToString)
mapping.register('portal', 'univentionPortalEntryPortal')
mapping.register('activated', 'univentionPortalEntryActivate', None, univention.admin.mapping.ListToString)
mapping.register('allowedGroups', 'univentionPortalEntryAllowedUserGroup')
mapping.register('authRestriction', 'univentionPortalEntryAuthRestriction', None, univention.admin.mapping.ListToString)
mapping.register('icon', 'univentionPortalEntryIcon', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_post_create(self):
		self._update_portals_after_portal_change()

	def _ldap_post_modify(self):
		if self.hasChanged('name'):
			self._update_portals_after_name_change()
		if self.hasChanged('portal'):
			self._update_portals_after_portal_change()

	def _ldap_post_move(self, olddn):
		self._update_portals_after_name_change()

	def _ldap_post_remove(self):
		for portal_obj in univention.admin.modules.lookup('settings/portal', None, self.lo, scope='sub'):
			self._remove_self_from_portal(portal_obj)

	def _update_portals_after_portal_change(self):
		old_portal = self.oldinfo.get('portal', [])
		new_portal = self.info.get('portal', [])

		removed_portals = [portal for portal in old_portal if portal not in new_portal]
		for portal_dn in removed_portals:
			self._remove_self_from_portal(portal_dn)

		added_portals = [portal for portal in new_portal if portal not in old_portal]
		for portal_dn in added_portals:
			self._add_self_to_portal(portal_dn)

	def _remove_self_from_portal(self, portal_obj):
		if isinstance(portal_obj, basestring):
			try:
				portal_mod = univention.admin.modules.get('settings/portal')
				portal_obj = univention.admin.objects.get(portal_mod, None, self.lo, position='', dn=portal_obj)
			except univention.admin.uexceptions.noObject:
				# If a settings/portal objects gets removed it removes itself from the 'portal' property of all
				# settings/portal_entry objects.
				# And in reverse this function is called when the 'portal' property of settings/portal_entry
				# changes so the settings/portal object might already be deleted, if this is triggered by
				# the removal of said settings/portal object.
				return

		portal_obj.open()
		old_content = portal_obj.info.get('content', [])
		new_content = []
		for category, entries in old_content:
			entries_with_self_removed = [entry for entry in entries if not self.lo.compare_dn(entry, self.dn)]
			if len(entries_with_self_removed) > 0:
				new_content.append([category, entries_with_self_removed])
		if new_content != old_content:
			portal_obj['content'] = new_content
			portal_obj.modify()

	def _add_self_to_portal(self, portal_obj):
		if isinstance(portal_obj, basestring):
			portal_mod = univention.admin.modules.get('settings/portal')
			portal_obj = univention.admin.objects.get(portal_mod, None, self.lo, position='', dn=portal_obj)

		portal_obj.open()
		old_content = portal_obj.info.get('content', [])
		if self.dn in [entry for category, entries in old_content for entry in entries]:
			return
		new_content = None
		portal_category_dn = 'cn=%s,cn=categories,cn=portal,cn=univention,%s' % (escape_dn_chars(self['category']), self.lo.base,)
		category_already_in_old_content = any(self.lo.compare_dn(portal_category_dn, category) for category, entries in old_content)
		if category_already_in_old_content:
			new_content = [[category, entries + ([self.dn] if self.lo.compare_dn(category, portal_category_dn) else [])] for category, entries in old_content]
		else:
			new_content = [[portal_category_dn, [self.dn]]] + old_content
		if new_content != old_content:
			try:
				portal_category_mod = univention.admin.modules.get('settings/portal_category')
				univention.admin.objects.get(portal_category_mod, None, self.lo, position='', dn=portal_category_dn)
			except univention.admin.uexceptions.noObject:
				# if the settings/portal_category object for the category string does not exist anymore create it
				portal_category_pos = univention.admin.uldap.position(self.lo.parentDn(portal_category_dn))
				portal_category_obj = portal_category_mod.object(None, self.lo, portal_category_pos)
				portal_category_obj['name'] = self['category']
				portal_category_obj['displayName'] = {
					'admin': [
						('en_US', 'Administration'),
						('de_DE', 'Verwaltung')
					],
					'service': [
						('en_US', 'Applications'),
						('de_DE', 'Applikationen')
					]
				}.get(self['category'], [])
				portal_category_obj.create()
			portal_obj['content'] = new_content
			portal_obj.modify()

	def _update_portals_after_name_change(self):
		for portal_obj in univention.admin.modules.lookup('settings/portal', None, self.lo, scope='sub'):
			portal_obj.open()
			old_content = portal_obj.info.get('content', [])
			new_content = [[category, [self.dn if self.lo.compare_dn(entry, self.old_dn) else entry for entry in entries]] for category, entries in old_content]
			if new_content != old_content:
				portal_obj['content'] = new_content
				portal_obj.modify()


lookup = object.lookup
identify = object.identify
