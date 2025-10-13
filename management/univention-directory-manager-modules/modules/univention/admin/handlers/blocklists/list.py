# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for all blocklist objects"""

from __future__ import annotations

import univention.admin.blocklist
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate

module = 'blocklists/list'
operations = ['add', 'edit', 'remove', 'search']
childs = False
childmodules = ['blocklists/entry']
short_description = _('Blocklist')
object_name = _('Blocklist')
object_name_plural = _('Blocklists')
long_description = _('Blocklist for certain UDM properties')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionBlocklist'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'blockingProperties': univention.admin.property(
        short_description=_('Properties to block'),
        long_description=_('Property values removed from a UDM object can be automatically blocked for future use. This is achieved by adding the properties to a blocklist. The properties must be specified according to the following schema: "udm/module property". An example configuration would be "users/user mailPrimaryAddress". If multiple properties are assigned to the same blocklist, the blocking value applies for multiple properties.'),
        syntax=univention.admin.syntax.UDM_PropertySelect,
        required=True,
        multivalue=True,
    ),
    'retentionTime': univention.admin.property(
        short_description=_('Retention time for objects in this blocklist'),
        long_description=_('Property values removed from a UDM object can be automatically blocked for future use. Each blocklist can be assigned a retention period. Once this retention period has elapsed, the blocking object is automatically deleted, and the property value can be reassigned. The retention period is set using the following schema "1y6m3d" (which equals one year, six months and three days).'),
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Blocklist settings'), layout=[
        Group(_('General settings'), layout=[
            ['name'],
            ['retentionTime'],
            ['blockingProperties'],
        ]),
    ]),
]
# fmt: on


def mapBlockingProperty(vals, encoding=()):
    return [' '.join(val).encode(*encoding) for val in vals]


def unmapBlockingProperty(vals, encoding=()):
    return [val.decode(*encoding).split(' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('blockingProperties', 'univentionBlockingProperties', mapBlockingProperty, unmapBlockingProperty)
mapping.register('retentionTime', 'univentionBlocklistRetentionTime', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE

    @classmethod
    def identify(cls, dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
        return b'univentionBlocklist' in attr.get('objectClass', [])

    # do not set univentionObjectIdentifier on blocklist objects - they are saved in a different LDAP base
    @classmethod
    def _register_univention_object_identifier_property(cls, module):
        return


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
