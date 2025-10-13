# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DNS| text records (TXT)"""

from __future__ import annotations

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.handlers.dns import (
    ARPA_IP4, ARPA_IP6, DNSBase, has_any, is_dns, is_forward_zone, is_not_handled_by_other_module_than, is_zone,
)
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/txt_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['txt']
superordinate = 'dns/forward_zone'
childs = False
short_description = _('DNS: TXT Record')
object_name = _('TXT record')
object_name_plural = _('TXT record')
long_description = _('Resolve the symbolic name to some textual data.')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dNSZone'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('The name of the host relative to the domain.'),
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'zonettl': univention.admin.property(
        short_description=_('Time to live'),
        long_description=_('The time this entry may be cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        default=(('22', 'hours'), []),
        dontsearch=True,
    ),
    'txt': univention.admin.property(
        short_description=_('Text Record'),
        long_description=_('One or more arbitrary text strings.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        required=True,
        size='Two',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General TXT record settings'), layout=[
            'name',
            'txt',
            'zonettl',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('txt', 'tXTRecord', encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
# fmt: on


class object(DNSBase):
    module = module

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'dNSZone'),
            univention.admin.filter.expression('tXTRecord', '*', escape=False),
            # negated forward_zone.py
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('sOARecord', '*', escape=False)]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP4, escape=False)]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP6, escape=False)]),
            # negated host_record.py
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('aRecord', '*', escape=False)]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('aAAARecord', '*', escape=False)]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('mXRecord', '*', escape=False)]),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    return bool(
        attr.get('tXTRecord')
        and is_dns(attr)
        and not is_zone(attr)
        and is_forward_zone(attr)
        and not has_any(attr, 'aRecord', 'aAAARecord', 'mXRecord')
        and is_not_handled_by_other_module_than(attr, module),
    )
