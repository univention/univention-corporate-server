# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""|UDM| module for |DNS| host records"""

import ipaddress
from typing import Any  # noqa: F401

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization
from univention.admin.handlers.dns import (  # noqa: F401
    DNSBase, has_any, is_dns, is_not_handled_by_other_module_than, is_zone,
)
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/host_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['a']
superordinate = 'dns/forward_zone'
childs = False
short_description = _('DNS: Host Record')
object_name = _('Host record')
object_name_plural = _('Host records')
long_description = _('Resolve the symbolic name to IP addresses.')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dNSZone'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Hostname'),
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
        default=(('3', 'hours'), []),
        dontsearch=True,
    ),
    'a': univention.admin.property(
        short_description=_('IP addresses'),
        long_description=_('One or more IP addresses, to which the name is resolved to.'),
        syntax=univention.admin.syntax.ipAddress,
        multivalue=True,
    ),
    'mx': univention.admin.property(
        short_description=_('Mail exchanger host'),
        long_description=_('The FQDNs of the hosts responsible for receiving mail for this DNS name.'),
        syntax=univention.admin.syntax.dnsMX,
        multivalue=True,
        dontsearch=True,
    ),
    'txt': univention.admin.property(
        short_description=_('Text Record'),
        long_description=_('One or more arbitrary text strings.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General host record settings'), layout=[
            'name',
            'a',
            'zonettl',
        ]),
    ]),
    Tab(_('Mail'), _('Mail exchangers for this host'), advanced=True, layout=[
        'mx',
    ]),
    Tab(_('Text'), _('Optional text'), advanced=True, layout=[
        'txt',
    ]),
]


def unmapMX(old, encoding=()):
    # type: (list[bytes], univention.admin.handlers._Encoding) -> list[list[str]]
    return [
        i.decode(*encoding).split(u' ', 1)
        for i in old
    ]


def mapMX(old, encoding=()):
    # type: (list[list[str]], univention.admin.handlers._Encoding) -> list[bytes]
    return [
        u' '.join(i).encode(*encoding)
        for i in old
    ]


def unmapIPAddresses(values, encoding=()):
    # type: (dict[str, list[bytes]], univention.admin.handlers._Encoding) -> list[str]
    records = []  # type: list[str]
    if 'aRecord' in values:
        records += (x.decode(*encoding) for x in values['aRecord'])
    if 'aAAARecord' in values:
        records += (ipaddress.IPv6Address(x.decode(*encoding)).exploded for x in values['aAAARecord'])
    return records


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('mx', 'mXRecord', mapMX, unmapMX, encoding='ASCII')
mapping.register('txt', 'tXTRecord', encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.registerUnmapping('a', unmapIPAddresses, encoding='ASCII')


class object(DNSBase):
    module = module

    def _ldap_modlist(self):  # IPv6
        # type: () -> list[tuple[str, Any, Any]]
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
        oldAddresses = self.oldinfo.get('a')
        newAddresses = self.info.get('a')
        oldARecord = []
        newARecord = []
        oldAaaaRecord = []
        newAaaaRecord = []
        if oldAddresses != newAddresses:
            if oldAddresses:
                for address in oldAddresses:
                    if u':' in address:  # IPv6
                        oldAaaaRecord.append(address.encode('ASCII'))
                    else:
                        oldARecord.append(address.encode('ASCII'))
            if newAddresses:
                for address in newAddresses:
                    if u':' in address:  # IPv6
                        newAaaaRecord.append(address)
                    else:
                        newARecord.append(address.encode('ASCII'))

            # explode all IPv6 addresses and remove duplicates
            unique = {ipaddress.IPv6Address(u'%s' % (x,)).exploded for x in newAaaaRecord}
            values = [x.encode('ASCII') for x in unique]

            ml.append(('aRecord', oldARecord, newARecord))
            ml.append(('aAAARecord', oldAaaaRecord, values))
        return ml

    @classmethod
    def unmapped_lookup_filter(cls):
        # type: () -> univention.admin.filter.conjunction
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'dNSZone'),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('sOARecord', '*', escape=False)]),
            univention.admin.filter.conjunction('|', [
                univention.admin.filter.expression('aRecord', '*', escape=False),
                univention.admin.filter.expression('aAAARecord', '*', escape=False),
                univention.admin.filter.expression('mXRecord', '*', escape=False),
                univention.admin.filter.expression('univentionObjectType', module, escape=True),  # host record without any record
            ]),
        ])

    @classmethod
    def rewrite_filter(cls, filter, mapping):
        # type: (univention.admin.filter.expression, univention.admin.mapping.mapping) -> None
        if filter.variable == 'a':
            filter.transform_to_conjunction(univention.admin.filter.conjunction('|', [
                univention.admin.filter.expression('aRecord', filter.value, escape=False),
                univention.admin.filter.expression('aAAARecord', filter.value, escape=False),
            ]))
        else:
            return super(object, cls).rewrite_filter(filter, mapping)


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr, canonical=False):
    # type: (str, univention.admin.handlers._Attributes, bool) -> bool
    return bool(
        is_dns(attr)
        and not is_zone(attr)
        and is_not_handled_by_other_module_than(attr, module)
        and (has_any(attr, 'aRecord', 'aAAARecord', 'mXRecord') or attr.get("univentionObjectType")),
    )
