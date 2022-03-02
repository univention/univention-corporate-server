# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 Univention GmbH
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

from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.localization
import univention.admin.handlers

translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

module = 'portals/entry'
default_containers = ['cn=entry,cn=portals,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search']
short_description = _('Portal: Entry')
object_name = _('Portal entry')
object_name_plural = _('Portal entries')
long_description = _('One link in https://fqdn/univention/portal. Belongs to one or more portals/category objects, which belong to one or more portals/portal objects')
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionNewPortalEntry'],
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
		short_description=_('Display name'),
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
	'link': univention.admin.property(
		short_description=_('Links (best pick based on locale / protocol / hostname)'),
		long_description='',
		syntax=univention.admin.syntax.LocalizedLink,
		multivalue=True,
		required=True,
	),
	'allowedGroups': univention.admin.property(
		short_description=_('Restrict visibility to groups'),
		long_description=_('If one or more groups are selected then the portal entry will only be visible to logged in users that are in any of the selected groups. If no groups are selected then the portal entry is always visible.'),
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
	),
	'activated': univention.admin.property(
		short_description=_('Activated'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
	),
	'anonymous': univention.admin.property(
		short_description=_('Only visible if not logged in'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
	),
	'icon': univention.admin.property(
		short_description=_('Icon'),
		long_description='',
		syntax=univention.admin.syntax.Base64BaseUpload,
		dontsearch=True,
	),
	'linkTarget': univention.admin.property(
		short_description=_('Browser tab when opening link'),
		syntax=univention.admin.syntax.NewPortalEntryLinkTarget,
		default='useportaldefault',
		dontsearch=True,
	),
	'backgroundColor': univention.admin.property(
		short_description=_('Background color'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
	)
}

layout = [
	Tab(_('General'), _('Entry options'), layout=[
		Group(_('General'), layout=[
			["name"],
			["icon"],
			["backgroundColor"],
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
			["activated", "anonymous"],
			["allowedGroups"],
		]),
	]),
]


def mapTranslationValue(vals, encoding=()):
	return [u' '.join(val).encode(*encoding) for val in vals]


def unmapTranslationValue(vals, encoding=()):
	return [val.decode(*encoding).split(u' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionNewPortalEntryDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('description', 'univentionNewPortalEntryDescription', mapTranslationValue, unmapTranslationValue)
mapping.register('link', 'univentionNewPortalEntryLink', mapTranslationValue, unmapTranslationValue)
mapping.register('linkTarget', 'univentionNewPortalEntryLinkTarget', None, univention.admin.mapping.ListToString)
mapping.register('activated', 'univentionNewPortalEntryActivate', None, univention.admin.mapping.ListToString)
mapping.register('anonymous', 'univentionNewPortalEntryOnlyAnonymous', None, univention.admin.mapping.ListToString)
mapping.register('allowedGroups', 'univentionNewPortalEntryAllowedUserGroup')
mapping.register('icon', 'univentionNewPortalEntryIcon', None, univention.admin.mapping.ListToString)
mapping.register('backgroundColor', 'univentionNewPortalEntryBackgroundColor', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_post_remove(self):
		for portal_obj in univention.admin.modules.lookup('portals/portal', None, self.lo, filter=filter_format('menuLinks=%s', [self.dn]), scope='sub'):
			portal_obj.open()
			portal_obj['menuLinks'].remove(self.dn)
			portal_obj.modify()
		for portal_obj in univention.admin.modules.lookup('portals/portal', None, self.lo, filter=filter_format('userLinks=%s', [self.dn]), scope='sub'):
			portal_obj.open()
			portal_obj['userLinks'].remove(self.dn)
			portal_obj.modify()
		for category_obj in univention.admin.modules.lookup('portals/category', None, self.lo, filter=filter_format('entries=%s', [self.dn]), scope='sub'):
			category_obj.open()
			category_obj['entries'].remove(self.dn)
			category_obj.modify()
		for folder_obj in univention.admin.modules.lookup('portals/folder', None, self.lo, filter=filter_format('entries=%s', [self.dn]), scope='sub'):
			folder_obj.open()
			folder_obj['entries'].remove(self.dn)
			folder_obj.modify()


lookup = object.lookup
identify = object.identify
