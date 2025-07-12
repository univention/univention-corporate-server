# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |UDM| hooks"""

from __future__ import annotations

import apt

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/udm_hook'
superordinate = 'settings/cn'
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Settings: UDM Hook')
object_name = _('UDM Hook')
object_name_plural = _('UDM Hooks')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
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
        identifies=True,
        ldap_attribute='cn',
    ),
    'filename': univention.admin.property(
        short_description=_('UDM hook file name'),
        long_description='',
        syntax=univention.admin.syntax.BaseFilename,
        required=True,
        default='',
        ldap_attribute='univentionUDMHookFilename',
    ),
    'data': univention.admin.property(
        short_description=_('UDM hook data'),
        long_description='',
        syntax=univention.admin.syntax.Base64Bzip2Text,
        required=True,
        ldap_attribute='univentionUDMHookData',
        map=mapBase64,
        unmap=unmapBase64,
    ),
    'active': univention.admin.property(
        short_description=_('Active'),
        long_description='',
        syntax=univention.admin.syntax.TrueFalseUp,
        default='FALSE',
        ldap_attribute='univentionUDMHookActive',
    ),
    'appidentifier': univention.admin.property(
        short_description=_('App identifier'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        multivalue=True,
        ldap_attribute='univentionAppIdentifier',
    ),
    'package': univention.admin.property(
        short_description=_('Software package'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='univentionOwnedByPackage',
    ),
    'packageversion': univention.admin.property(
        short_description=_('Software package version'),
        long_description='',
        syntax=univention.admin.syntax.DebianPackageVersion,
        ldap_attribute='univentionOwnedByPackageVersion',
    ),
    'ucsversionstart': univention.admin.property(
        short_description=_('Minimal UCS version'),
        long_description='',
        syntax=univention.admin.syntax.UCSVersion,
        ldap_attribute='univentionUCSVersionStart',
    ),
    'ucsversionend': univention.admin.property(
        short_description=_('Maximal UCS version'),
        long_description='',
        syntax=univention.admin.syntax.UCSVersion,
        ldap_attribute='univentionUCSVersionEnd',
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
mapping.from_properties(property_descriptions)
# messagecatalog is handled via object._post_map and object._post_unmap defined below
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        super()._ldap_pre_modify()
        diff_keys = [key for key in self.info.keys() if self.info.get(key) != self.oldinfo.get(key) and key not in ('active', 'appidentifier')]
        if not diff_keys:  # check for trivial change
            return
        if not self.hasChanged('package'):
            old_version = self.oldinfo.get('packageversion', '0')
            if not apt.apt_pkg.version_compare(self['packageversion'], old_version) > -1:
                raise univention.admin.uexceptions.valueInvalidSyntax(_('packageversion: Version must not be lower than the current one.'), property='packageversion')

    def _post_unmap(self, info: univention.admin.handlers._Properties, values: univention.admin.handlers._Attributes) -> univention.admin.handlers._Properties:
        info['messagecatalog'] = []
        messagecatalog_ldap_attribute = 'univentionMessageCatalog'
        messagecatalog_ldap_attribute_and_tag_prefix = '%s;entry-lang-' % (messagecatalog_ldap_attribute,)
        for ldap_attribute, value_list in values.items():
            if ldap_attribute.startswith(messagecatalog_ldap_attribute_and_tag_prefix):
                language_tag = ldap_attribute.split(messagecatalog_ldap_attribute_and_tag_prefix, 1)[1]
                mo_data_base64 = univention.admin.mapping.unmapBase64(value_list)
                info['messagecatalog'].append((language_tag, mo_data_base64))
        return info

    def _post_map(self, modlist, diff):
        messagecatalog_ldap_attribute = 'univentionMessageCatalog'
        messagecatalog_ldap_attribute_and_tag_prefix = '%s;entry-lang-' % (messagecatalog_ldap_attribute,)
        for property_name, old_value, new_value in diff:
            if property_name == 'messagecatalog':
                old_dict = dict(old_value)
                new_dict = dict(new_value)
                for language_tag, old_mo_data_base64 in old_dict.items():
                    ldap_attribute = f'{messagecatalog_ldap_attribute_and_tag_prefix}{language_tag}'
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
                    ldap_attribute = f'{messagecatalog_ldap_attribute_and_tag_prefix}{language_tag}'
                    if not old_dict.get(language_tag):  # property value has been added
                        new_mo_data_binary = univention.admin.mapping.mapBase64(new_mo_data_base64)
                        modlist.append((ldap_attribute, None, new_mo_data_binary))
                break
        return modlist


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
