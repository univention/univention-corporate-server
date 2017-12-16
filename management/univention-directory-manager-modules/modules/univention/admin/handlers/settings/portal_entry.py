# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager module for Portal entries
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

OC = "univentionPortalEntry"

module = 'settings/portal_entry'
superordinate = 'settings/cn'
default_containers = ['cn=portal,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Portal: Entry')
long_description = _('One link in https://fqdn/univention/portal. Belongs to one (or more) settings/portal')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', OC],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Internal name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'displayName': univention.admin.property(
		short_description=_('Display Name'),
		long_description=_('Headline of the entry. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('Description of the entry. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDescription,
		multivalue=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'favorite': univention.admin.property(
		short_description=_('Favorite'),
		long_description=_('Shown in the favorite section'),
		syntax=univention.admin.syntax.TrueFalseUp,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'category': univention.admin.property(
		short_description=_('Category'),
		long_description='',
		syntax=univention.admin.syntax.PortalCategory,
		default='service',
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'link': univention.admin.property(
		short_description=_('Link'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'portal': univention.admin.property(
		short_description=_('Portals'),
		long_description=_('Shown on portals'),
		syntax=univention.admin.syntax.Portals,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'authRestriction': univention.admin.property(
		short_description=_('Authorization'),
		long_description='',
		syntax=univention.admin.syntax.AuthRestriction,
		default='anonymous',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'activated': univention.admin.property(
		short_description=_('Activated'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'icon': univention.admin.property(
		short_description=_('Icon'),
		long_description='',
		syntax=univention.admin.syntax.Base64BaseUpload,
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Entry options'), layout=[
		Group(_('General'), layout=[
			["name", "category"],
			["portal"],
			["icon"],
		]),
		Group(_('Display name'), layout=[
			["displayName"],
		]),
		Group(_('Description'), layout=[
			["description"],
		]),
		Group(_('Link'), layout=[
			["link"],
		]),
		Group(_('Advanced'), layout=[
			["activated"],
			#["authRestriction"],
			#["favorite"],
		]),
	]),
]


def mapTranslationValue(vals):
	ret = []
	for val in vals:
		ret.append('%s %s' % (val[0], val[1]))
	return ret


def unmapTranslationValue(vals):
	ret = []
	for val in vals:
		ret.append(val.split(' ', 1))
	return ret


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionPortalEntryDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('description', 'univentionPortalEntryDescription', mapTranslationValue, unmapTranslationValue)
mapping.register('favorite', 'univentionPortalEntryFavorite', None, univention.admin.mapping.ListToString)
mapping.register('category', 'univentionPortalEntryCategory', None, univention.admin.mapping.ListToString)
mapping.register('link', 'univentionPortalEntryLink')
mapping.register('portal', 'univentionPortalEntryPortal')
mapping.register('activated', 'univentionPortalEntryActivate', None, univention.admin.mapping.ListToString)
mapping.register('authRestriction', 'univentionPortalEntryAuthRestriction', None, univention.admin.mapping.ListToString)
mapping.register('icon', 'univentionPortalEntryIcon', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', OC),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return OC in attr.get('objectClass', [])
