# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DNS| service records (SRV)"""

from __future__ import annotations

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization
from univention.admin.handlers.dns import DNSBase, is_dns
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/srv_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['location']
superordinate = 'dns/forward_zone'
childs = False
short_description = _('DNS: Service record')
object_name = _('Service record')
object_name_plural = _('Service records')
long_description = _('Resolve well-known services to servers providing those services.')
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
        long_description=_('The name and protocol of the service.'),
        syntax=univention.admin.syntax.dnsSRVName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'location': univention.admin.property(
        short_description=_('Location'),
        long_description=_('The host providing the service.'),
        syntax=univention.admin.syntax.dnsSRVLocation,
        multivalue=True,
        required=True,
    ),
    'zonettl': univention.admin.property(
        short_description=_('Time to live'),
        long_description=_('The time this entry may be cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        default=(('3', 'hours'), []),
        dontsearch=True,
    ),
}
layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General service record settings'), layout=[
            'name',
            'location',
            'zonettl',
        ]),
    ]),
]
# fmt: on


def unmapName(old: list[bytes], encoding: univention.admin.handlers._Encoding = ()) -> list[str]:
    items = old[0].decode(*encoding).split('.', 2)
    items[0] = items[0][1:]
    items[1] = items[1][1:]
    return items


def mapName(old: list[str], encoding: univention.admin.handlers._Encoding = ()) -> bytes:
    if len(old) == 1:
        return old[0].encode(*encoding)
    if len(old) == 3 and old[2]:
        return '_{}._{}.{}'.format(*old).encode(*encoding)
    return '_{}._{}'.format(*old[:2]).encode(*encoding)


def unmapLocation(old: list[bytes], encoding: univention.admin.handlers._Encoding = ()) -> list[list[str]]:
    return [
        i.decode(*encoding).split(' ', 3)
        for i in old
    ]


def mapLocation(old: list[list[str]], encoding: univention.admin.handlers._Encoding = ()) -> list[bytes]:
    return [
        ' '.join(i).encode(*encoding)
        for i in old
    ]


# fmt: off
mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', mapName, unmapName, encoding='ASCII')
mapping.register('location', 'sRVRecord', mapLocation, unmapLocation, encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
# fmt: on


class object(DNSBase):
    module = module

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'dNSZone'),
            univention.admin.filter.expression('sRVRecord', '*', escape=False),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    return bool(
        attr.get('sRVRecord')
        and is_dns(attr),
    )
