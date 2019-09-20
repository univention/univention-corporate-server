# -*- coding: utf-8 -*-
#
# Univention Directory Manager Hooks
#  directory manager module for UDM hooks
#
# Copyright 2013-2019 Univention GmbH
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
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import apt

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/udm_hook'
superordinate = 'settings/cn'
childs = 0
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Settings: UDM Hook')
object_name = _('UDM Hook')
object_name_plural = _('UDM Hooks')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionObjectMetadata', 'univentionUDMHook'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('UDM hook name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'filename': univention.admin.property(
		short_description=_('UDM hook file name'),
		long_description='',
		syntax=univention.admin.syntax.BaseFilename,
		required=True,
		default='',
	),
	'data': univention.admin.property(
		short_description=_('UDM hook data'),
		long_description='',
		syntax=univention.admin.syntax.Base64Bzip2Text,
		required=True,
	),
	'active': univention.admin.property(
		short_description=_('Active'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
	),
	'appidentifier': univention.admin.property(
		short_description=_('App identifier'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
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
	'messagecatalog': univention.admin.property(
		short_description=_('GNU message catalog for translations'),
		long_description='GNU message catalog (syntax: <language tag> <Base64 encoded GNU message catalog>)',
		syntax=univention.admin.syntax.Localesubdirname_and_GNUMessageCatalog,
		multivalue=True,
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General UDM hook settings'), layout=[
			["name"],
			["filename"],
			["data"],
			["messagecatalog"],
		]),
		Group(_('Metadata'), layout=[
			["package"],
			["packageversion"],
			["appidentifier"],
		]),
		Group(_('UCS Version Dependencies'), layout=[
			["ucsversionstart"],
			["ucsversionend"],
		]),
		Group(_('Activated'), layout=[
			["active"],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('filename', 'univentionUDMHookFilename', None, univention.admin.mapping.ListToString)
mapping.register('data', 'univentionUDMHookData', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('active', 'univentionUDMHookActive', None, univention.admin.mapping.ListToString)
mapping.register('appidentifier', 'univentionAppIdentifier')
mapping.register('package', 'univentionOwnedByPackage', None, univention.admin.mapping.ListToString)
mapping.register('packageversion', 'univentionOwnedByPackageVersion', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionstart', 'univentionUCSVersionStart', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionend', 'univentionUCSVersionEnd', None, univention.admin.mapping.ListToString)
# messagecatalog is handled via object._post_map and object._post_unmap defined below


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		diff_keys = [key for key in self.info.keys() if self.info.get(key) != self.oldinfo.get(key) and key not in ('active', 'appidentifier')]
		if not diff_keys:  # check for trivial change
			return
		if not self.hasChanged('package'):
			old_version = self.oldinfo.get('packageversion', '0')
			if not apt.apt_pkg.version_compare(self['packageversion'], old_version) > -1:
				raise univention.admin.uexceptions.valueInvalidSyntax(_('packageversion: Version must not be lower than the current one.'), property='packageversion')

	def _post_unmap(self, info, values):
		info['messagecatalog'] = []
		messagecatalog_ldap_attribute = "univentionMessageCatalog"
		messagecatalog_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (messagecatalog_ldap_attribute,)
		for ldap_attribute, value_list in values.items():
			if ldap_attribute.startswith(messagecatalog_ldap_attribute_and_tag_prefix):
				language_tag = ldap_attribute.split(messagecatalog_ldap_attribute_and_tag_prefix, 1)[1]
				mo_data_base64 = univention.admin.mapping.unmapBase64(value_list)
				info['messagecatalog'].append((language_tag, mo_data_base64))
		return info

	def _post_map(self, modlist, diff):
		messagecatalog_ldap_attribute = "univentionMessageCatalog"
		messagecatalog_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (messagecatalog_ldap_attribute,)
		for property_name, old_value, new_value in diff:
			if property_name == 'messagecatalog':
				old_dict = dict(old_value)
				new_dict = dict(new_value)
				for language_tag, old_mo_data_base64 in old_dict.items():
					ldap_attribute = ''.join((messagecatalog_ldap_attribute_and_tag_prefix, language_tag))
					new_mo_data_base64 = new_dict.get(language_tag)
					if not new_mo_data_base64:  # property value has been removed
						old_mo_data_binary = univention.admin.mapping.mapBase64(old_mo_data_base64)
						modlist.append((ldap_attribute, old_mo_data_binary, None))
					else:
						if new_mo_data_base64 != old_mo_data_base64:
							old_mo_data_binary = univention.admin.mapping.mapBase64(old_mo_data_base64)
							new_mo_data_binary = univention.admin.mapping.mapBase64(new_mo_data_base64)
							modlist.append((ldap_attribute, old_mo_data_binary, new_mo_data_binary))
				for language_tag, new_mo_data_base64 in new_dict.items():
					ldap_attribute = ''.join((messagecatalog_ldap_attribute_and_tag_prefix, language_tag))
					if not old_dict.get(language_tag):  # property value has been added
						new_mo_data_binary = univention.admin.mapping.mapBase64(new_mo_data_base64)
						modlist.append((ldap_attribute, None, new_mo_data_binary))
				break
		return modlist


lookup = object.lookup
identify = object.identify
