#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the |DHCP| subnet"""

from __future__ import annotations

import sys
from ipaddress import IPv4Address, IPv4Network
from typing import TYPE_CHECKING

import univention.admin.localization
import univention.admin.uexceptions as uex
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Tab


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


Range = tuple[IPv4Address, IPv4Address]

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

# fmt: off
_properties = {
    'option': univention.admin.property(
        short_description=_('DHCP options'),
        long_description=_('Additional options for DHCP'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        options=['options'],
    ),
    'statements': univention.admin.property(
        short_description=_('DHCP Statements'),
        long_description=_('Additional statements for DHCP'),
        syntax=univention.admin.syntax.TextArea,
        multivalue=True,
        options=['options'],
    ),
}
_options = {
    'options': univention.admin.option(
        short_description=_('Allow custom DHCP options'),
        long_description=_('Allow adding custom DHCP options. Experts only!'),
        default=False,
        editable=True,
        objectClasses=['dhcpOptions'],
    ),
}
_mappings = (
    ('option', 'dhcpOption', None, None, 'ASCII'),
    ('statements', 'dhcpStatements', None, None, 'ASCII'),
)
# fmt: on


def rangeMap(value: Iterable[list[str]], encoding: tuple[str, ...] = ()) -> list[bytes]:
    return [' '.join(x).encode(*encoding) for x in value]


def rangeUnmap(value: Iterable[bytes], encoding: tuple[str, ...] = ()) -> list[list[str]]:
    return [x.decode(*encoding).split() for x in value]


def add_dhcp_options(module_name: str) -> None:
    module = sys.modules[module_name]

    options = module.options
    options.update(_options)

    properties = module.property_descriptions
    properties.update(_properties)

    mapping = module.mapping
    for item in _mappings:
        mapping.register(*item)

    layout = module.layout
    layout.append(Tab(
        _('Low-level DHCP configuration'),
        _('Custom DHCP options'),
        advanced=True,
        layout=['option', 'statements'],
    ))  # fmt: skip


def check_range_overlap(ranges: Sequence[Range]) -> None:
    """
    Check IPv4 address ranges for overlapping

    :param ranges: List of 2-tuple (first-IP, last-IP) of type :py:class:`IPv4Address`.
    :raises uex.rangesOverlapping: when an overlap exists.

    >>> first = (IPv4Address(u"192.0.2.0"), IPv4Address(u"192.0.2.127"))
    >>> second = (IPv4Address(u"192.0.2.128"), IPv4Address(u"192.0.2.255"))
    >>> both = (IPv4Address(u"192.0.2.0"), IPv4Address(u"192.0.2.255"))
    >>> check_range_overlap([])
    >>> check_range_overlap([first])
    >>> check_range_overlap([first, second])
    >>> check_range_overlap([first, both]) #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    rangesOverlapping: 192.0.2.0-192.0.2.127; 192.0.2.0-192.0.2.255
    """
    prev: list[Range] = []
    for r1 in ranges:
        (s1, e1) = r1
        assert s1 <= e1  # already checked by syntax.IPv4_AddressRange

        for r2 in prev:
            (s2, e2) = r2
            if e2 < s1:
                # [s2 <= e2] << [s1 <= e1]
                pass
            elif e1 < s2:
                # [s1 <= e1] << [s2 <= e2]
                pass
            else:
                raise uex.rangesOverlapping('%s-%s; %s-%s' % (r1 + r2))

        prev.append(r1)


def check_range_subnet(subnet: IPv4Network, ranges: Sequence[Range]) -> None:
    """
    Check IPv4 address ranges are inside the given network.

    :param subnet: IPv4 subnet.
    :param ranges: List of 2-tuple (first-IP, last-IP) of type :py:class:`ipaddress.IPv4Address`.
    :raises uex.rangeInNetworkAddress: when a range includes the reserved network address.
    :raises uex.rangeInBroadcastAddress: when a range includes the reserved broadcast address.
    :raises uex.rangeNotInNetwork: when a range is outside the sub-network.

    >>> subnet = IPv4Network(u'192.0.2.0/24')
    >>> range_ = (subnet[1], subnet[-2])
    >>> check_range_subnet(subnet, [])
    >>> check_range_subnet(subnet, [(subnet[1], subnet[-2])])
    >>> check_range_subnet(subnet, [(subnet[0], subnet[-2])]) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    rangeInNetworkAddress: 192.0.2.0-192.0.2.254
    >>> check_range_subnet(subnet, [(subnet[1], subnet[-1])]) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    rangeInBroadcastAddress: 192.0.2.1-192.0.2.255
    >>> local = IPv4Address(u"127.0.0.1")
    >>> check_range_subnet(subnet, [(local, local)]) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    rangeNotInNetwork: 127.0.0.1
    """
    for r1 in ranges:
        for ip in r1:
            if ip == subnet.network_address:
                raise uex.rangeInNetworkAddress('%s-%s' % r1)

            if ip == subnet.broadcast_address:
                raise uex.rangeInBroadcastAddress('%s-%s' % r1)

            if ip not in subnet:
                raise uex.rangeNotInNetwork(ip)


class DHCPBase(simpleLdap):
    pass


class DHCPBaseSubnet(DHCPBase):
    def ready(self) -> None:
        super().ready()

        try:
            subnet = IPv4Network('%(subnet)s/%(subnetmask)s' % self.info)
        except ValueError:
            raise uex.valueError(_('The subnet mask does not match the subnet.'), property='subnetmask')

        if self.hasChanged('range') or not self.exists():
            ranges = [tuple(IPv4Address('%s' % (ip,)) for ip in range_) for range_ in self['range']]
            check_range_overlap(ranges)
            check_range_subnet(subnet, ranges)
