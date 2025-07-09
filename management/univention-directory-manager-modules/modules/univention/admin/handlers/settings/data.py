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
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
