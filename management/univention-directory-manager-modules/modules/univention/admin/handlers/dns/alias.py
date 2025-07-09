# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DNS| aliases (CNAME)"""

from __future__ import annotations

import re
from re import Match

from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization
from univention.admin.handlers.dns import DNSBase, is_dns, stripDot
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/alias'
operations = ['add', 'edit', 'remove', 'search']
columns = ['cname']
superordinate = 'dns/forward_zone'
childs = False
short_description = _('DNS: Alias record')
object_name = _('Alias record')
object_name_plural = _('Alias records')
long_description = _('Assign additional names to a host.')
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
        short_description=_('Alias'),
        long_description=_('The name of the entry relative to the domain.'),
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'zonettl': univention.admin.property(
        short_description=_('Time to live'),
        long_description=_('The time this entry may be cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        default=(('3', 'hours'), []),
        dontsearch=True,
    ),
    'cname': univention.admin.property(
        short_description=_('Canonical name'),
        long_description=_("The name this alias points to. A FQDN must end with a dot."),
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General alias record settings'), layout=[
            'name',
            'zonettl',
            'cname',
        ]),
    ]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', stripDot, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('cname', 'cNAMERecord', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
# fmt: on


class object(DNSBase):
    module = module

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction(
            '&',
            [
                univention.admin.filter.expression('objectClass', 'dNSZone'),
                univention.admin.filter.expression('cNAMERecord', '*', escape=False),
            ],
        )


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    return bool(
        attr.get('cNAMERecord') and is_dns(attr),
    )


def lookup_alias_filter(lo: univention.admin.uldap.access, filter_s: str) -> str:
    alias_pattern = re.compile(r'(?:^|\()dnsAlias=([^)]+)($|\))', flags=re.I)

    def _replace_alias_filter(match: Match[str]) -> str:
        alias_filter = object.lookup_filter('name=%s' % match.group(1), lo)
        alias_filter_s = str(alias_filter)
        alias_base = str(lo.base)  # standard dns container might be a better choice
        unmatchable_filter = '(&(objectClass=top)(!(objectClass=top)))'  # if no computers for aliases found, return an impossible filter!
        alias_replaced = ''.join(
            {
                filter_format('(cn=%s)', [attrs['cNAMERecord'][0].split('.', 1)[0]])
                for dn, attrs in lo.search(base=alias_base, scope='sub', filter=alias_filter_s, attr=['cNAMERecord'])
            },
        )
        return '(|%s)' % (alias_replaced,) if alias_replaced else unmatchable_filter

    return alias_pattern.sub(_replace_alias_filter, str(filter_s))
