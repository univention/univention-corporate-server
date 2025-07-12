# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for blocklist settings"""

from __future__ import annotations

import univention.admin.blocklist
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate

module = 'blocklists/entry'
operations = ['add', 'edit', 'remove', 'search']
childs = False
superordinate = 'blocklists/list'
short_description = _('Univention blocklist entries')
object_name = _('Univention blocklist entry')
object_name_plural = _('Univention blocklist entries')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionBlockingEntry'],
    ),
}
property_descriptions = {
    'value': univention.admin.property(
        short_description=_('Blocklist entry value'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
        ldap_attribute='cn',
    ),
    'blockedUntil': univention.admin.property(
        short_description=_('Blocked until'),
        long_description=_('This blocklist entry is valid until timestamp (generalized time in LDAP-Syntax -> 21241212000000Z). Expired entries are deleted.'),
        syntax=univention.admin.syntax.GeneralizedTimeUTC,
        required=True,
        ldap_attribute='blockedUntil',
    ),
    'originUniventionObjectIdentifier': univention.admin.property(
        short_description=_('Origin ID'),
        long_description=_('The ID of the UDM object that lead to this blocklist entry. The value of this blocklist entry can still be used on that UDM object.'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
        ldap_attribute='originUniventionObjectIdentifier',
    ),
}

layout = [
    Tab(_('General'), _('Blocklist entry settings'), layout=[
        Group(_('General settings'), layout=[
            ["value"],
            ["blockedUntil"],
            ["originUniventionObjectIdentifier"],
        ]),
    ]),
]
# fmt: on


mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE

    @classmethod
    def rewrite_filter(cls, filter: univention.admin.filter.expression, mapping: univention.admin.mapping.mapping) -> None:
        super().rewrite_filter(filter, mapping)
        if filter.variable == 'cn':
            filter.value = univention.admin.blocklist.hash_blocklist_value(filter.value.encode('UTF-8'))

    @classmethod
    def identify(cls, dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
        return b'univentionBlockingEntry' in attr.get('objectClass', [])

    def _ldap_pre_create(self) -> None:
        self['value'] = univention.admin.blocklist.hash_blocklist_value(self['value'].encode('UTF-8'))
        super()._ldap_pre_create()

    @classmethod
    def _register_univention_object_identifier_property(cls, module):
        return


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
