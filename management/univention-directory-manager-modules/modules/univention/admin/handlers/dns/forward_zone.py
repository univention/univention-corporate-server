# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DNS| forward zones"""

from __future__ import annotations

import ipaddress
from typing import Any

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin import configRegistry
from univention.admin.handlers.dns import (
    ARPA_IP4, ARPA_IP6, escapeSOAemail, is_dns, is_forward_zone, is_zone, stripDot, unescapeSOAemail,
)
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/forward_zone'
operations = ['add', 'edit', 'remove', 'search']
columns = ['nameserver', 'a', 'mx', 'txt']
childs = True
childmodules = ['dns/alias', 'dns/host_record', 'dns/srv_record', 'dns/txt_record', 'dns/ns_record']
short_description = _('DNS: Forward lookup zone')
object_name = _('Forward lookup zone')
object_name_plural = _('Forward lookup zones')
long_description = _('Map names to IP addresses (and other data).')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dNSZone'],
    ),
}
property_descriptions = {
    'zone': univention.admin.property(
        short_description=_('Zone name'),
        long_description=_('The name of the domain.'),
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
        ldap_attribute='zoneName',
        map=stripDot,
        encoding='ASCII',
    ),
    'zonettl': univention.admin.property(
        short_description=_('Zone time to live'),
        long_description=_('The time this entry may be cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        required=True,
        default=(('3', 'hours'), []),
        dontsearch=True,
        ldap_attribute='dNSTTL',
        map=mapUNIX_TimeInterval,
        unmap=unmapUNIX_TimeInterval,
    ),
    'contact': univention.admin.property(
        short_description=_('Contact person'),
        long_description=_('The email address of the person responsible for this zone.'),
        syntax=univention.admin.syntax.emailAddressThatMayEndWithADot,
        required=True,
        default=('root@%(domainname)s.' % configRegistry, []),
    ),
    'serial': univention.admin.property(
        short_description=_('Serial number'),
        long_description=_('The sequence number for this zone. Updates automatically.'),
        syntax=univention.admin.syntax.integer,
        required=True,
        default=('1', []),
    ),
    'refresh': univention.admin.property(
        short_description=_('Refresh interval'),
        long_description=_('The time interval secondary DNS servers use to check the zone for updates.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        required=True,
        default=(('8', 'hours'), []),
    ),
    'retry': univention.admin.property(
        short_description=_('Retry interval'),
        long_description=_('The time interval secondary DNS servers use to retry failed refresh updates.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        required=True,
        default=(('2', 'hours'), []),
    ),
    'expire': univention.admin.property(
        short_description=_('Expiry interval'),
        long_description=_('The time interval after which secondary DNS servers will expire failed zones.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        required=True,
        default=(('7', 'days'), []),
    ),
    'ttl': univention.admin.property(
        short_description=_('Negative time to live'),
        long_description=_('The time interval "not found" answers are cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        required=True,
        default=(('3', 'hours'), []),
    ),
    'nameserver': univention.admin.property(
        short_description=_('Name server'),
        long_description=_('The FQDNs of the servers serving this zone. A FQDN must end with a dot.'),
        syntax=univention.admin.syntax.dnsHostname,
        multivalue=True,
        required=True,
        ldap_attribute='nSRecord',
        encoding='ASCII',
    ),
    'mx': univention.admin.property(
        short_description=_('Mail exchanger host'),
        long_description=_('The FQDNs of the hosts responsible for receiving mail for this DNS name.'),
        syntax=univention.admin.syntax.dnsMX,
        multivalue=True,
        ldap_attribute='mXRecord',
        map=mapMX,
        unmap=unmapMX,
        encoding='ASCII',
    ),
    'txt': univention.admin.property(
        short_description=_('Text Record'),
        long_description=_('One or more arbitrary text strings.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        ldap_attribute='tXTRecord',
        encoding='ASCII',
    ),
    'a': univention.admin.property(
        short_description=_('IP addresses'),
        long_description=_('One or more IP addresses, to which the name is resolved to.'),
        syntax=univention.admin.syntax.ipAddress,
        multivalue=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General forward lookup zone settings'), layout=[
            'zone',
            'zonettl',
            'nameserver',
        ]),
    ]),
    Tab(_('Start of authority'), _('Primary name server information'), layout=[
        Group(_('Start of authority'), layout=[
            'contact',
            'serial',
            ['refresh', 'retry'],
            ['expire', 'ttl'],
        ]),
    ]),
    Tab(_('IP addresses'), _('IP addresses of the zone'), layout=[
        Group(_('IP addresses of the zone'), layout=[
            'a',
        ]),
    ]),
    Tab(_('MX records'), _('Mail exchanger records'), layout=[
        Group(_('MX records'), layout=[
            'mx',
        ]),
    ]),
    Tab(_('TXT records'), _('Text records'), layout=[
        Group(_('TXT records'), layout=[
            'txt',
        ]),
    ]),
]


def mapMX(old: list[list[str]], encoding: univention.admin.handlers._Encoding = ()) -> list[bytes]:
    return [' '.join(entry).encode(*encoding) for entry in old]


def unmapMX(old: list[bytes], encoding: univention.admin.handlers._Encoding = ()) -> list[list[str]]:
    return [entry.decode(*encoding).split(' ', 1) for entry in old]


mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def __init__(
        self,
        co: None,
        lo: univention.admin.uldap.access,
        position: univention.admin.uldap.position | None,
        dn: str = '',
        superordinate: univention.admin.handlers.simpleLdap | None = None,
        attributes: univention.admin.handlers._Attributes | None = None,
    ) -> None:
        univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)
        if not self.dn and not self.position:
            raise univention.admin.uexceptions.insufficientInformation(_('Neither DN nor position given.'))

    def _post_unmap(self, info: univention.admin.handlers._Properties, values: univention.admin.handlers._Attributes) -> univention.admin.handlers._Properties:
        info = super()._post_unmap(info, values)
        info['a'] = []
        if 'aRecord' in values:
            info['a'] += (x.decode('ASCII') for x in values['aRecord'])
        if 'aAAARecord' in values:
            info['a'] += (ipaddress.IPv6Address(x.decode('ASCII')).exploded for x in values['aAAARecord'])
        return info

    def open(self) -> None:
        univention.admin.handlers.simpleLdap.open(self)

        soa = self.oldattr.get('sOARecord', [b''])[0].split(b' ')
        if len(soa) > 6:
            self['contact'] = unescapeSOAemail(soa[1].decode('ASCII'))
            self['serial'] = soa[2].decode('ASCII')
            self['refresh'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[3])
            self['retry'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[4])
            self['expire'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[5])
            self['ttl'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[6])

        self.save()

    def _ldap_addlist(self) -> list[tuple[str, Any]]:
        return [*super()._ldap_addlist(), ('relativeDomainName', [b'@'])]

    def _ldap_modlist(self) -> list[tuple[str, Any, Any]]:
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
        if self.hasChanged(['nameserver', 'contact', 'serial', 'refresh', 'retry', 'expire', 'ttl']):
            if self['contact'] and not self['contact'].endswith('.'):
                self['contact'] += '.'
            for i, ns in enumerate(self['nameserver']):
                if ns and ':' not in ns and '.' in ns and not ns.endswith('.'):
                    self['nameserver'][i] += '.'
            refresh = univention.admin.mapping.mapUNIX_TimeInterval(self['refresh'])
            retry = univention.admin.mapping.mapUNIX_TimeInterval(self['retry'])
            expire = univention.admin.mapping.mapUNIX_TimeInterval(self['expire'])
            ttl = univention.admin.mapping.mapUNIX_TimeInterval(self['ttl'])
            soa = b'%s %s %s %s %s %s %s' % (
                self['nameserver'][0].encode('ASCII'),
                escapeSOAemail(self['contact']).encode('ASCII'),
                self['serial'].encode('ASCII'),
                refresh,
                retry,
                expire,
                ttl,
            )
            ml.append(('sOARecord', self.oldattr.get('sOARecord', []), [soa]))

        oldAddresses = self.oldinfo.get('a')
        newAddresses = self.info.get('a')
        oldARecord = []
        newARecord = []
        oldAaaaRecord = []
        newAaaaRecord = []
        if oldAddresses != newAddresses:
            if oldAddresses:
                for address in oldAddresses:
                    if ':' in address:  # IPv6
                        oldAaaaRecord.append(address.encode('ASCII'))
                    else:
                        oldARecord.append(address.encode('ASCII'))
            if newAddresses:
                for address in newAddresses:
                    if ':' in address:  # IPv6
                        newAaaaRecord.append(ipaddress.IPv6Address('%s' % (address,)).exploded.encode('ASCII'))
                    else:
                        newARecord.append(address.encode('ASCII'))
            ml.append(('aRecord', oldARecord, newARecord))
            ml.append(('aAAARecord', oldAaaaRecord, newAaaaRecord))
        return ml

    def _ldap_pre_modify(self) -> None:
        super()._ldap_pre_modify()
        # update SOA record
        if not self.hasChanged('serial'):
            self['serial'] = str(int(self['serial']) + 1)

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'dNSZone'),
            univention.admin.filter.expression('sOARecord', '*', escape=False),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP4, escape=False)]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP6, escape=False)]),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    return bool(
        is_zone(attr) and is_dns(attr) and is_forward_zone(attr),
    )
