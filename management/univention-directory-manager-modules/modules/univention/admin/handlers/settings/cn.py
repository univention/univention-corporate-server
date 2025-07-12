# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for a cn=univention singleton object representiong a container for various settings."""

from __future__ import annotations

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/cn'
operations = ['search']
childs = True
short_description = _('Univention Settings')
object_name = _('Univention Setting')
object_name_plural = _('Univention Settings')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'organizationalRole'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
        ldap_attribute='cn',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), ["name"]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'organizationalRole'),
            univention.admin.filter.expression('cn', 'univention'),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    return b'organizationalRole' in attr.get('objectClass', []) and attr.get('cn', []) == [b'univention']
