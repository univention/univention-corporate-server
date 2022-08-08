# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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

import re

from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.localization
import univention.admin.handlers

translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

module = 'portals/folder'
default_containers = ['cn=folder,cn=portals,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search']
short_description = _('Portal: Folder')
object_name = _('Portal folder')
object_name_plural = _('Portal folders')
long_description = _('One folder in https://fqdn/univention/portal which holds one or more portals/entry objects. Belongs to one or more portals/category objects, which belong to one or more portals/portal objects')
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionNewPortalFolder'],
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
		long_description=_('Headline of the folder. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		required=True,
	),
	'entries': univention.admin.property(
		short_description=_('Entry'),
		long_description=_('List of portal entries and/or portal folders shown in this folder'),
		syntax=univention.admin.syntax.NewPortalEntries,
		multivalue=True,
	),
}

layout = [
	Tab(_('General'), _('Entry options'), layout=[
		Group(_('General'), layout=[
			["name"],
		]),
		Group(_('Display name'), layout=[
			["displayName"],
		]),
		Group(_('Entries'), layout=[
			["entries"],
		]),
	]),
]


def mapTranslationValue(vals, encoding=()):
	return [u' '.join(val).encode(*encoding) for val in vals]


def unmapTranslationValue(vals, encoding=()):
	return [val.decode(*encoding).split(u' ', 1) for val in vals]


def mapOrdered(ldap_values, encoding=()):
	# ldap stores multi value fields unordered by default
	# you can change this by putting X-ORDERED 'VALUES' in your schema file
	# but then you literally get [b'{0}foo', b'{1}bar']
	return [u'{{{}}}{}'.format(i, value).encode(*encoding) for i, value in enumerate(ldap_values)]


def unmapOrdered(udm_values, encoding=()):
	return [_[1] for _ in sorted((re.match(u'^{(\\d+)}(.*)', value.decode(*encoding)).groups() for value in udm_values), key=lambda n: int(n[0]))]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionNewPortalFolderDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('entries', 'univentionNewPortalFolderEntries', mapOrdered, unmapOrdered)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_post_remove(self):
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
