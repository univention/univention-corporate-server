# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  UDM module for Software Installation Group Policy
#
# Copyright 2019 Univention GmbH
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

from univention.admin.layout import Tab, Group

import univention.admin.syntax
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/gpsi-category-registration'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS Software Installation Group Policy: Category Registration')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['categoryRegistration', 'leaf']
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
		identifies=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'managedBy': univention.admin.property(
		short_description=_('managed by'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'localizedDescription': univention.admin.property(
		short_description=_('localized description'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'localeID': univention.admin.property(
		short_description=_('locale ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.integer,
	),
	'categoryId': univention.admin.property(
		short_description=_('category ID'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General'), layout=[
			["name", "description"],
			'managedBy',
			'localizedDescription',
			'localeID',
			'categoryId',
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('managedBy', 'managedBy', None, univention.admin.mapping.ListToString)
mapping.register('localizedDescription', 'localizedDescription')
mapping.register('localeID', 'localeID')
mapping.register('categoryId', 'categoryId', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
