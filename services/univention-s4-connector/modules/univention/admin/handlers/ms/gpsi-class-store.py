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

module = 'ms/gpsi-class-store'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Software Installation Group Policy: Class Store')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['classStore', 'top']
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
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'versionNumber': univention.admin.property(
		short_description=_('Version number'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'nextLevelStore': univention.admin.property(
		short_description=_('Next level store'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'lastUpdateSequence': univention.admin.property(
		short_description=_('Last update sequence'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'extensionName': univention.admin.property(
		short_description=_('Extension name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'appSchemaVersion': univention.admin.property(
		short_description=_('App schema version'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General'), layout=[
			["name", "displayName"],
			["description"],
			'versionNumber',
			'nextLevelStore',
			'lastUpdateSequence',
			'extensionName',
			'appSchemaVersion',
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('versionNumber', 'versionNumber', None, univention.admin.mapping.ListToString)
mapping.register('nextLevelStore', 'nextLevelStore', None, univention.admin.mapping.ListToString)
mapping.register('lastUpdateSequence', 'lastUpdateSequence', None, univention.admin.mapping.ListToString)
mapping.register('extensionName', 'extensionName')
mapping.register('appSchemaVersion', 'appSchemaVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
