# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager module for Portal entries
#
# Copyright 2018 Univention GmbH
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

OC = "univentionPortalCategory"

module = 'settings/portal_category'
superordinate = 'settings/cn'
default_containers = ['cn=categories,cn=portal,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Portal: Category')
long_description = _('Object under which settings/portal_entry objects can be displayed')
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
		long_description=_('Display name of the category. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Category options'), layout=[
		Group(_('Name'), layout=[
			["name"],
		]),
		Group(_('Display name'), layout=[
			["displayName"],
		]),
	]),
]


def mapTranslationValue(vals):
	return [' '.join(val) for val in vals]


def unmapTranslationValue(vals):
	return [val.split(' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionPortalCategoryDisplayName', mapTranslationValue, unmapTranslationValue)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_post_modify(self):
		if self.hasChanged('name'):
			newdn = 'cn=%s,%s' % (self['name'], self.lo.parentDn(self.dn),)								
			self.__update_property__content__of__portal(self.dn, newdn)

	def _ldap_post_move(self, olddn):
		self.__update_property__content__of__portal(olddn, self.dn)

	def __update_property__content__of__portal(self, olddn, newdn):
		for portal_obj in univention.admin.modules.lookup('settings/portal', None, self.lo, scope='sub'):
			portal_obj.open()
			old_content = portal_obj.info.get('content', [])
			new_content = [[newdn if self.lo.compare_dn(category, olddn) else category, entries] for category, entries in old_content]
			if new_content != old_content:
				portal_obj['content'] = new_content
				portal_obj.modify()

	def _ldap_post_remove(self):
		for portal_obj in univention.admin.modules.lookup('settings/portal', None, self.lo, scope='sub'):
			self._remove_self_from_portal(portal_obj)

	def _remove_self_from_portal(self, portal_obj):
		portal_obj.open()
		old_content = portal_obj.info.get('content', [])
		new_content = [[category, entries] for category, entries in old_content if not self.lo.compare_dn(category, self.dn)]
		if new_content != old_content:
			portal_obj['content'] = new_content
			portal_obj.modify()


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
