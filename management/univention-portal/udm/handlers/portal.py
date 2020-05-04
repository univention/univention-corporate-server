# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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
import re

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.localization
import univention.admin.handlers

translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

module = 'portals/portal'
default_containers = ['cn=portals,cn=portals,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search']
short_description = _('Portal: Portal')
object_name = _('Portal')
object_name_plural = _('Portals')
long_description = _('Object that feeds everything in https://fqdn/univention/portal')
options = {
	'default': univention.admin.option(
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
	'showApps': univention.admin.property(
		short_description=_('Show apps'),
		long_description=_('Shows links to locally installed Apps'),
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
		syntax=univention.admin.syntax.NewPortalFontColor,
		default='black',
		dontsearch=True,
	),
	'portalComputers': univention.admin.property(
		short_description=_('Show on server'),
		long_description=_('This portal will be used as start site for the given servers'),
		syntax=univention.admin.syntax.NewPortalComputer,
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
	'userLinks': univention.admin.property(
		short_description=_('Entries in the user menu'),
		long_description=_('List of portal entries that are shown when a user is logged in'),
		syntax=univention.admin.syntax.NewPortalEntries,
		multivalue=True,
	),
	'menuLinks': univention.admin.property(
		short_description=_('Entries in the menu'),
		long_description=_('List of portal entries that are shown when opening the menu in the portal'),
		syntax=univention.admin.syntax.NewPortalEntries,
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
			['defaultLinkTarget'],
			['showApps'],
			['userLinks'],
			['menuLinks'],
		]),
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


def mapTranslationValue(vals):
	return [' '.join(val) for val in vals]


def unmapTranslationValue(vals):
	return [val.split(' ', 1) for val in vals]


def mapContent(vals):
	return json.dumps(vals)


def unmapContent(vals):
	return json.loads(vals[0])


def mapOrdered(ldap_values):
	# ldap stores multi value fields unordered by default
	# you can change this by putting X-ORDERED 'VALUES' in your schema file
	# but then you literally get ['{0}foo', '{1}bar']
	return ['{{{}}}{}'.format(i, value) for i, value in enumerate(ldap_values)]


def unmapOrdered(udm_values):
	return [re.sub('^{\d+}', '', value) for value in udm_values]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionNewPortalDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('showApps', 'univentionNewPortalShowApps', None, univention.admin.mapping.ListToString)
mapping.register('portalComputers', 'univentionNewPortalComputers')
mapping.register('ensureLogin', 'univentionNewPortalEnsureLogin', None, univention.admin.mapping.ListToString)
mapping.register('anonymousEmpty', 'univentionNewPortalAnonymousEmpty', mapTranslationValue, unmapTranslationValue)
mapping.register('autoLayoutCategories', 'univentionNewPortalAutoLayoutCategories', None, univention.admin.mapping.ListToString)
mapping.register('background', 'univentionNewPortalBackground', None, univention.admin.mapping.ListToString)
mapping.register('cssBackground', 'univentionNewPortalCSSBackground', None, univention.admin.mapping.ListToString)
mapping.register('fontColor', 'univentionNewPortalFontColor', None, univention.admin.mapping.ListToString)
mapping.register('logo', 'univentionNewPortalLogo', None, univention.admin.mapping.ListToString)
mapping.register('userLinks', 'univentionNewPortalUserLinks', mapOrdered, unmapOrdered)
mapping.register('menuLinks', 'univentionNewPortalMenuLinks', mapOrdered, unmapOrdered)
mapping.register('categories', 'univentionNewPortalCategories', mapOrdered, unmapOrdered)
mapping.register('defaultLinkTarget', 'univentionNewPortalDefaultLinkTarget', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


lookup = object.lookup
identify = object.identify
