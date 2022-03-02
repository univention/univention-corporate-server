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

import re

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.localization
import univention.admin.handlers

translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

module = 'portals/portal'
default_containers = ['cn=portal,cn=portals,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search']
short_description = _('Portal: Portal')
object_name = _('Portal')
object_name_plural = _('Portals')
long_description = _('Object that feeds everything in https://fqdn/univention/portal')
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionNewPortal'],
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
		long_description=_('Headline of the portal. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		required=True,
	),
	'showUmc': univention.admin.property(
		short_description=_('Show UMC categories and modules'),
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
	'ensureLogin': univention.admin.property(
		short_description=_('Redirect anonymous visitors to the login'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
		dontsearch=True,
	),
	'userLinks': univention.admin.property(
		short_description=_('Entries in the user menu'),
		long_description=_('List of portal entries that are shown in the menu for the logged in user'),
		syntax=univention.admin.syntax.NewPortalEntries,
		multivalue=True,
	),
	'menuLinks': univention.admin.property(
		short_description=_('Entries in the menu'),
		long_description=_('List of portal entries that are shown in the menu of the portal'),
		syntax=univention.admin.syntax.NewPortalCategoryEntries,
		multivalue=True,
	),
	'categories': univention.admin.property(
		short_description=_('Categories'),
		syntax=univention.admin.syntax.NewPortalCategories,
		multivalue=True,
	),
	'defaultLinkTarget': univention.admin.property(
		short_description=_('Default browser tab for portal entries'),
		syntax=univention.admin.syntax.NewPortalDefaultLinkTarget,
		default='embedded',
		dontsearch=True,
	),
}

layout = [
	Tab(_('General'), _('Portal options'), layout=[
		Group(_('Name'), layout=[
			['name'],
			['displayName'],
		]),
		Group(_('Categories'), layout=[
			['categories'],
			['showUmc'],
		]),
		Group(_('Link behaviour'), layout=[
			['defaultLinkTarget'],
		]),
		Group(_('User menu'), layout=[
			['userLinks'],
		]),
		Group(_('Menu'), layout=[
			['menuLinks'],
		]),
		Group(_('Appearance'), layout=[
			['logo'],
			['background'],
		]),
		Group(_('Login'), layout=[
			['ensureLogin'],
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
mapping.register('displayName', 'univentionNewPortalDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('showUmc', 'univentionNewPortalShowUMC', None, univention.admin.mapping.ListToString)
mapping.register('ensureLogin', 'univentionNewPortalEnsureLogin', None, univention.admin.mapping.ListToString)
mapping.register('background', 'univentionNewPortalBackground', None, univention.admin.mapping.ListToString)
mapping.register('logo', 'univentionNewPortalLogo', None, univention.admin.mapping.ListToString)
mapping.register('userLinks', 'univentionNewPortalUserLinks', mapOrdered, unmapOrdered)
mapping.register('menuLinks', 'univentionNewPortalMenuLinks', mapOrdered, unmapOrdered)
mapping.register('categories', 'univentionNewPortalCategories', mapOrdered, unmapOrdered)
mapping.register('defaultLinkTarget', 'univentionNewPortalDefaultLinkTarget', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


lookup = object.lookup
identify = object.identify
