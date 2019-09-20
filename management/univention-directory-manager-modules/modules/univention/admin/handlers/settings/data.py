# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  directory manager module for Portal entries
#
# Copyright 2018-2019 Univention GmbH
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
import univention.admin.filter
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/data'
superordinate = 'settings/cn'
default_containers = ['cn=data,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Data')
object_name = _('Data')
object_name_plural = _('Data')
long_description = _('Arbitrary data files')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionData'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('name'),
		long_description=_('The name of the data object'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('The description'),
		syntax=univention.admin.syntax.string,
	),
	'filename': univention.admin.property(
		short_description=_('File name of file to store data in.'),
		long_description='',
		syntax=univention.admin.syntax.string,
		default='',
	),
	'data': univention.admin.property(
		short_description=_('The data'),
		long_description=_('The actual data, bzipped and base64 encoded'),
		syntax=univention.admin.syntax.Base64Bzip2Text,
	),
	'data_type': univention.admin.property(
		short_description=_('Data Type'),
		long_description=_('The type of the data'),
		syntax=univention.admin.syntax.string,
		required=True,
	),
	'ucsversionstart': univention.admin.property(
		short_description=_('Minimal UCS version'),
		long_description='',
		syntax=univention.admin.syntax.UCSVersion,
	),
	'ucsversionend': univention.admin.property(
		short_description=_('Maximal UCS version'),
		long_description='',
		syntax=univention.admin.syntax.UCSVersion,
	),
	'meta': univention.admin.property(
		short_description=_('Meta information'),
		long_description='The data objects meta information',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'package': univention.admin.property(
		short_description=_('Software package'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'packageversion': univention.admin.property(
		short_description=_('Software package version'),
		long_description='',
		syntax=univention.admin.syntax.DebianPackageVersion,
	),
}

layout = [
	Tab(_('General'), _('Category options'), layout=[
		Group(_('General settings'), layout=[
			["name"],
			["description"],
			["filename"],
			["data_type"],
			["data"],
		]),
		Group(_('Metadata'), layout=[
			["ucsversionstart"],
			["ucsversionend"],
			["meta"],
			["package"],
			["packageversion"],
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('filename', 'univentionDataFilename', None, univention.admin.mapping.ListToString)
mapping.register('data_type', 'univentionDataType', None, univention.admin.mapping.ListToString)
mapping.register('data', 'univentionData', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('ucsversionstart', 'univentionUCSVersionStart', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionend', 'univentionUCSVersionEnd', None, univention.admin.mapping.ListToString)
mapping.register('meta', 'univentionDataMeta', None)
mapping.register('package', 'univentionOwnedByPackage', None, univention.admin.mapping.ListToString)
mapping.register('packageversion', 'univentionOwnedByPackageVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


lookup = object.lookup
identify = object.identify
