# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for package lists"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/packages'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Package List')
object_name = _('Package List')
object_name_plural = _('Package Lists')
long_description = _('List of Packages for UCS Systems')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPackageList'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
        ldap_attribute='cn',
    ),
    'packageList': univention.admin.property(
        short_description=_('Package List'),
        long_description=_('Package List'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        dontsearch=True,
        ldap_attribute='univentionPackageDefinition',
    ),
}

layout = [
    Tab(_('General'), _('Package List'), layout=[
        Group(_('General package list settings'), layout=[
            'name',
            'packageList',
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
