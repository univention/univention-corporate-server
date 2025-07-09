# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the |DHCP| pool"""

import copy
import ipaddress

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions
from univention.admin.layout import Group, Tab

from .__common import DHCPBase, add_dhcp_options, rangeMap, rangeUnmap


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/pool'
operations = ['add', 'edit', 'remove', 'search']
superordinate = ['dhcp/subnet', 'dhcp/sharedsubnet']
childs = False
short_description = _('DHCP: Pool')
object_name = _('DHCP pool')
object_name_plural = _('DHCP pools')
long_description = _('A pool of dynamic addresses assignable to hosts.')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionDhcpPool'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('A unique name for this DHCP pool object.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'range': univention.admin.property(
        short_description=_('IP range for dynamic assignment'),
        long_description=_('Define a pool of addresses available for dynamic address assignment.'),
        syntax=univention.admin.syntax.IPv4_AddressRange,
        multivalue=True,
        required=True,
    ),
    'failover_peer': univention.admin.property(
        short_description=_('Failover peer configuration'),
        long_description=_('The name of the "failover peer" configuration to use.'),
        syntax=univention.admin.syntax.string,
    ),
    'known_clients': univention.admin.property(
        short_description=_('Allow known clients'),
        long_description=_('Addresses from this pool are given to clients which have a DHCP host entry matching their MAC address, but with no IP address assigned.'),
        syntax=univention.admin.syntax.AllowDeny,
    ),
    'unknown_clients': univention.admin.property(
        short_description=_('Allow unknown clients'),
        long_description=_('Addresses from this pool are given to clients, which do not have a DHCP host entry matching their MAC address.'),
        syntax=univention.admin.syntax.AllowDeny,
    ),
    'dynamic_bootp_clients': univention.admin.property(
        short_description=_('Allow dynamic BOOTP clients'),
        long_description=_('Addresses from this pool are given to clients using the old BOOTP protocol, which has no mechanism to free addresses again.'),
        syntax=univention.admin.syntax.AllowDeny,
    ),
    'all_clients': univention.admin.property(
        short_description=_('All clients'),
        long_description=_('Globally enable or disable this pool.'),
        syntax=univention.admin.syntax.AllowDeny,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General DHCP pool settings'), layout=[
            'name',
            'range',
        ]),
    ]),
    Tab(_('Advanced'), _('Advanced DHCP pool options'), advanced=True, layout=[
        'failover_peer',
        ['known_clients', 'unknown_clients'],
        ['dynamic_bootp_clients', 'all_clients'],
    ]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
mapping.register('failover_peer', 'univentionDhcpFailoverPeer', None, univention.admin.mapping.ListToString, encoding='ASCII')
# fmt: on

add_dhcp_options(__name__)


class object(DHCPBase):
    module = module

    permits_udm2dhcp = {
        'known_clients': 'known clients',
        'unknown_clients': 'unknown clients',
        'dynamic_bootp_clients': 'dynamic bootp clients',
        'all_clients': 'all clients',
    }
    permits_dhcp2udm = {value: key for (key, value) in permits_udm2dhcp.items()}

    def open(self) -> None:
        univention.admin.handlers.simpleLdap.open(self)

        for i in [x.decode('UTF-8') for x in self.oldattr.get('dhcpPermitList', [])]:
            permit, name = i.split(' ', 1)
            if name in self.permits_dhcp2udm:
                prop = self.permits_dhcp2udm[name]
                self[prop] = permit

        self.save()

    def ready(self) -> None:
        super().ready()
        # Use ipaddress.IPv4Interface().network to be liberal with subnet notation
        subnet = ipaddress.IPv4Interface('%(subnet)s/%(subnetmask)s' % self.superordinate.info).network
        for addresses in self.info['range']:
            for addr in addresses:
                if ipaddress.IPv4Address('%s' % (addr,)) not in subnet:
                    raise univention.admin.uexceptions.rangeNotInNetwork(addr)

    def _ldap_modlist(self):
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
        if self.hasChanged(self.permits_udm2dhcp.keys()):
            old = self.oldattr.get('dhcpPermitList', [])
            new = copy.deepcopy(old)

            for prop, value in self.permits_udm2dhcp.items():
                try:
                    permit = self.oldinfo[prop]
                    new.remove(f'{permit} {value}'.encode())
                except LookupError:
                    pass
                try:
                    permit = self.info[prop]
                    new.append(f'{permit} {value}'.encode())
                except LookupError:
                    pass

            ml.append(('dhcpPermitList', old, new))
        if self.info.get('failover_peer', None) and not self.info.get('dynamic_bootp_clients', None) == 'deny':
            raise univention.admin.uexceptions.bootpXORFailover
        return ml

    @classmethod
    def rewrite_filter(cls, filter, mapping):
        if filter.variable in cls.permits_udm2dhcp:
            filter.value = '%s %s' % (filter.value.strip('*'), cls.permits_udm2dhcp[filter.variable])
            filter.variable = 'dhcpPermitList'
        else:
            super().rewrite_filter(filter, mapping)


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
