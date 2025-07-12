# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for arbitrary data entries"""

import univention.admin.filter
import univention.admin.localization
from univention.admin.layout import Group, Tab


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
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
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
        identifies=True,
        ldap_attribute='cn',
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description=_('The description'),
        syntax=univention.admin.syntax.string,
        ldap_attribute='description',
    ),
    'filename': univention.admin.property(
        short_description=_('File name of file to store data in.'),
        long_description='',
        syntax=univention.admin.syntax.string,
        default='',
        ldap_attribute='univentionDataFilename',
    ),
    'data': univention.admin.property(
        short_description=_('The data'),
        long_description=_('The actual data, bzipped and base64 encoded'),
        syntax=univention.admin.syntax.Base64Bzip2Text,
        ldap_attribute='univentionData',
        map=mapBase64,
        unmap=unmapBase64,
    ),
    'data_type': univention.admin.property(
        short_description=_('Data Type'),
        long_description=_('The type of the data'),
        syntax=univention.admin.syntax.string,
        required=True,
        ldap_attribute='univentionDataType',
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
    'meta': univention.admin.property(
        short_description=_('Meta information'),
        long_description='The data objects meta information',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        ldap_attribute='univentionDataMeta',
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
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
