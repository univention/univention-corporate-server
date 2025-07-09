# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| shared subnets"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab

from .__common import DHCPBaseSubnet, add_dhcp_options, rangeMap, rangeUnmap


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/sharedsubnet'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/shared'
childs = True
childmodules = ['dhcp/pool']
short_description = _('DHCP: Shared subnet')
object_name = _('Shared DHCP subnet')
object_name_plural = _('Shared DHCP subnets')
long_description = _('An IP address range used in a shared network.')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionDhcpSubnet', 'univentionDhcpSharedSubnet'],
    ),
}
property_descriptions = {
    'subnet': univention.admin.property(
        short_description=_('Subnet address'),
        long_description=_('The network address.'),
        syntax=univention.admin.syntax.ipv4Address,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'subnetmask': univention.admin.property(
        short_description=_('Address prefix length (or Netmask)'),
        long_description=_('The number of leading bits of the IP address used to identify the network.'),
        syntax=univention.admin.syntax.v4netmask,
        required=True,
    ),
    'broadcastaddress': univention.admin.property(
        short_description=_('Broadcast address'),
        long_description=_('The IP addresses used to send data to all hosts inside the network.'),
        syntax=univention.admin.syntax.ipv4Address,
    ),
    'range': univention.admin.property(
        short_description=_('Dynamic address assignment'),
        long_description=_('Define a pool of addresses available for dynamic address assignment.'),
        syntax=univention.admin.syntax.IPv4_AddressRange,
        multivalue=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General DHCP shared subnet settings'), layout=[
            ['subnet', 'subnetmask'],
            'broadcastaddress',
            'range',
        ]),
    ]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('subnet', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
mapping.register('subnetmask', 'dhcpNetMask', None, univention.admin.mapping.ListToString)
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString, encoding='ASCII')
# fmt: on

add_dhcp_options(__name__)


class object(DHCPBaseSubnet):
    module = module


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
