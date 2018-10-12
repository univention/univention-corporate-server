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

OC = "univentionCode"

module = 'settings/code'
superordinate = 'settings/cn'
default_containers = ['cn=code,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Code')
long_description = _('Arbitrary code files')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', OC],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('name'),
		long_description=_('The name of the Code file'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('The code files description'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'code': univention.admin.property(
		short_description=_('Code file'),
		long_description=_('The actual code, bzipped and base64 encoded'),
		syntax=univention.admin.syntax.Base64Bzip2Text,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'code_type': univention.admin.property(
		short_description=_('Code Type'),
		long_description=_('The type of the code'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'ucsversionstart': univention.admin.property(
		short_description=_('Minimal UCS version'),
		long_description='',
		syntax=univention.admin.syntax.UCSVersion,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'ucsversionend': univention.admin.property(
		short_description=_('Maximal UCS version'),
		long_description='',
		syntax=univention.admin.syntax.UCSVersion,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'meta': univention.admin.property(
		short_description=_('Meta information'),
		long_description='The code objects meta information',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'package': univention.admin.property(
		short_description=_('Software package'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'packageversion': univention.admin.property(
		short_description=_('Software package version'),
		long_description='',
		syntax=univention.admin.syntax.DebianPackageVersion,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Category options'), layout=[
		Group(_('General settings'), layout=[
			["name"],
			["description"],
			["code_type"],
			["code"],
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
mapping.register('code_type', 'univentionCodeType', None, univention.admin.mapping.ListToString)
mapping.register('code', 'univentionCode', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('ucsversionstart', 'univentionUCSVersionStart', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionend', 'univentionUCSVersionEnd', None, univention.admin.mapping.ListToString)
mapping.register('meta', 'univentionCodeMeta', None)
mapping.register('package', 'univentionOwnedByPackage', None, univention.admin.mapping.ListToString)
mapping.register('packageversion', 'univentionOwnedByPackageVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', OC),
		])


lookup = object.lookup


def identify(dn, attr, canonical=0):
	return OC in attr.get('objectClass', [])
