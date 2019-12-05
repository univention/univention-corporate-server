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

module = 'ms/gpsi-package-registration'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Software Installation Group Policy: Package Registration')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['packageRegistration', 'top']
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
	'versionNumberLo': univention.admin.property(
		short_description=_('Version number low'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'versionNumberHi': univention.admin.property(
		short_description=_('Version number high'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'vendor': univention.admin.property(
		short_description=_('Vendor'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'url': univention.admin.property(
		short_description=_('URL'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'revision': univention.admin.property(
		short_description=_('Revision'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'upgradeProductCode': univention.admin.property(
		short_description=_('Upgrade product code'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.TextArea,
	),
	'setupCommand': univention.admin.property(
		short_description=_('Setup command'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'productCode': univention.admin.property(
		short_description=_('product code'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
	),
	'packageType': univention.admin.property(
		short_description=_('package type'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'packageName': univention.admin.property(
		short_description=_('package name'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'packageFlags': univention.admin.property(
		short_description=_('package flags'),
		long_description='',
		syntax=univention.admin.syntax.SignedInteger,
	),
	'msiScriptSize': univention.admin.property(
		short_description=_('MSI script size'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'msiScriptPath': univention.admin.property(
		short_description=_('MSI script path'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msiScriptName': univention.admin.property(
		short_description=_('MSI script name'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'msiScript': univention.admin.property(
		short_description=_('MSI script'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
	),
	'msiFileList': univention.admin.property(
		short_description=_('MSI file list'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'managedBy': univention.admin.property(
		short_description=_('managed by'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'machineArchitecture': univention.admin.property(
		short_description=_('machine architecture'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.integer,
	),
	'localeID': univention.admin.property(
		short_description=_('Locale ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.integer,
	),
	'lastUpdateSequence': univention.admin.property(
		short_description=_('Last update sequence'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'installUiLevel': univention.admin.property(
		short_description=_('install UI level'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'iconPath': univention.admin.property(
		short_description=_('icon path'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'fileExtPriority': univention.admin.property(
		short_description=_('file ext priority'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'cOMTypelibId': univention.admin.property(
		short_description=_('COM type lib ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'cOMProgID': univention.admin.property(
		short_description=_('COM prog ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'cOMInterfaceID': univention.admin.property(
		short_description=_('COM interface ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'cOMClassID': univention.admin.property(
		short_description=_('COM class ID'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'categories': univention.admin.property(
		short_description=_('Category'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
	'canUpgradeScript': univention.admin.property(
		short_description=_('Can upgrade script'),
		long_description='',
		multivalue=True,
		syntax=univention.admin.syntax.string,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General'), layout=[
			["name", "displayName"],
			["description"],
			['versionNumberLo', 'versionNumberHi'],
			'vendor',
			'url',
			'revision',
			'upgradeProductCode',
			'setupCommand',
			'productCode',
			'packageType',
			'packageName',
			'packageFlags',
			'managedBy',
			'machineArchitecture',
			'localeID',
			'lastUpdateSequence',
			'installUiLevel',
			'iconPath',
			'fileExtPriority',
			'categories',
			'canUpgradeScript',
		]),
		Group(_('MSI'), layout=[
			'msiScriptSize',
			'msiScriptPath',
			'msiScriptName',
			'msiScript',
			'msiFileList',
		]),
		Group(_('COM'), layout=[
			'cOMTypelibId',
			'cOMProgID',
			'cOMInterfaceID',
			'cOMClassID',
		]),
	]),
]


def multivalueMapBase64(data):
	if data:
		return [univention.admin.mapping.mapBase64(d) for d in data]
	return []


def multivalueUnmapBase64(data):
	if data:
		return [univention.admin.mapping.unmapBase64(data)]  # stupid broken function in UDM
	return []


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('versionNumberLo', 'versionNumberLo', None, univention.admin.mapping.ListToString)
mapping.register('versionNumberHi', 'versionNumberHi', None, univention.admin.mapping.ListToString)
mapping.register('vendor', 'vendor', None, univention.admin.mapping.ListToString)
mapping.register('url', 'url', None, univention.admin.mapping.ListToString)
mapping.register('revision', 'revision', None, univention.admin.mapping.ListToString)
mapping.register('upgradeProductCode', 'upgradeProductCode', multivalueMapBase64, multivalueUnmapBase64)
mapping.register('setupCommand', 'setupCommand', None, univention.admin.mapping.ListToString)
mapping.register('productCode', 'productCode', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('packageType', 'packageType', None, univention.admin.mapping.ListToString)
mapping.register('packageName', 'packageName', None, univention.admin.mapping.ListToString)
mapping.register('packageFlags', 'packageFlags', None, univention.admin.mapping.ListToString)
mapping.register('msiScriptSize', 'msiScriptSize', None, univention.admin.mapping.ListToString)
mapping.register('msiScriptPath', 'msiScriptPath', None, univention.admin.mapping.ListToString)
mapping.register('msiScriptName', 'msiScriptName', None, univention.admin.mapping.ListToString)
mapping.register('msiScript', 'msiScript', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('msiFileList', 'msiFileList')
mapping.register('managedBy', 'managedBy', None, univention.admin.mapping.ListToString)
mapping.register('machineArchitecture', 'machineArchitecture')
mapping.register('localeID', 'localeID')
mapping.register('lastUpdateSequence', 'lastUpdateSequence', None, univention.admin.mapping.ListToString)
mapping.register('installUiLevel', 'installUiLevel', None, univention.admin.mapping.ListToString)
mapping.register('iconPath', 'iconPath')
mapping.register('fileExtPriority', 'fileExtPriority')
mapping.register('cOMTypelibId', 'cOMTypelibId')
mapping.register('cOMProgID', 'cOMProgID')
mapping.register('cOMInterfaceID', 'cOMInterfaceID')
mapping.register('cOMClassID', 'cOMClassID')
mapping.register('categories', 'categories')
mapping.register('canUpgradeScript', 'canUpgradeScript')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
