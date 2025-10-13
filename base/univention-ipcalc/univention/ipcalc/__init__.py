#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention IP Calculator for DNS records (IPv6 edition)."""

from ipaddress import IPv4Interface, IPv6Interface


_Interface = IPv4Interface | IPv6Interface


def _prefixlen(interface: _Interface) -> int:  # PY2 VS PY3
    return interface.prefixlen if hasattr(interface, 'prefixlen') else interface.network.prefixlen  # type: ignore


# IPv4: 4.3.                            2.1.                        IN-ADDR.ARPA
# IPv6: f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.IP6.ARPA
#       \__________ pointer __________/ \__________ reverse __________/
# network: "full network address"
# reverse: dns/reverse_zone.subnet (forward notation)
#          dns/reverse_zone.zoneName (backward notation)
# pointer: dns/ptr_record.address (LDAP: relativeDomainName)


def calculate_ipv6_reverse(network: _Interface) -> str:
    """
    Return reversed network part of IPv4 network.

    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0'))
    '0'
    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1'))
    '0'
    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4'))
    '0'
    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/16'))
    '0123'
    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/124'))
    '0123:4567:89ab:cdef:0123:4567:89ab:cde'
    >>> calculate_ipv6_reverse(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128'))
    '0123:4567:89ab:cdef:0123:4567:89ab:cde'
    """
    # at least one part must remain for zone entry
    prefixlen = min(_prefixlen(network) // 4, network.max_prefixlen // 4 - 1) or 1
    prefix = network.ip.exploded.replace(':', '')[:prefixlen]
    return ':'.join([prefix[i:i + 4] for i in range(0, len(prefix), 4)])


def calculate_ipv4_reverse(network: _Interface) -> str:
    """
    Return reversed network part of IPv4 network.

    >>> calculate_ipv4_reverse(IPv4Interface(u'1.2.3.4/0'))
    '1'
    >>> calculate_ipv4_reverse(IPv4Interface(u'1.2.3.4/8'))
    '1'
    >>> calculate_ipv4_reverse(IPv4Interface(u'1.2.3.4/16'))
    '1.2'
    >>> calculate_ipv4_reverse(IPv4Interface(u'1.2.3.4/24'))
    '1.2.3'
    >>> calculate_ipv4_reverse(IPv4Interface(u'1.2.3.4/32'))
    '1.2.3'
    """
    # at least one part must remain for zone entry
    prefixlen = min(_prefixlen(network) // 8, network.max_prefixlen // 8 - 1) or 1
    prefix = network.ip.exploded.split('.')[:prefixlen]
    return '.'.join(prefix)


def calculate_ipv6_network(network: _Interface) -> str:
    """
    Return network part of IPv6 network.

    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0'))
    ''
    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1'))
    ''
    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4'))
    '0'
    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/16'))
    '0123'
    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/112'))
    '0123:4567:89ab:cdef:0123:4567:89ab'
    >>> calculate_ipv6_network(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128'))
    '0123:4567:89ab:cdef:0123:4567:89ab:cdef'
    """
    prefixlen = _prefixlen(network) // 4
    prefix = network.ip.exploded.replace(':', '')[:prefixlen]
    return ':'.join([prefix[i:i + 4] for i in range(0, len(prefix), 4)])


def calculate_ipv4_network(network: _Interface) -> str:
    """
    Return network part of IPv4 network.

    >>> calculate_ipv4_network(IPv4Interface(u'1.2.3.4/0'))
    ''
    >>> calculate_ipv4_network(IPv4Interface(u'1.2.3.4/1'))
    ''
    >>> calculate_ipv4_network(IPv4Interface(u'1.2.3.4/8'))
    '1'
    >>> calculate_ipv4_network(IPv4Interface(u'1.2.3.4/24'))
    '1.2.3'
    >>> calculate_ipv4_network(IPv4Interface(u'1.2.3.4/32'))
    '1.2.3.4'
    """
    prefixlen = _prefixlen(network) // 8
    prefix = network.ip.exploded.split('.')[:prefixlen]
    return '.'.join(prefix)


def calculate_ipv6_pointer(network: _Interface) -> str:
    """
    Return host part of IPv6 network.

    >>> calculate_ipv6_pointer(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0'))
    'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
    >>> calculate_ipv6_pointer(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1'))
    'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
    >>> calculate_ipv6_pointer(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4'))
    'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
    >>> calculate_ipv6_pointer(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/124'))
    'f'
    >>> calculate_ipv6_pointer(IPv6Interface(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128'))
    'f'
    """
    prefixlen = min(_prefixlen(network) // 4, network.max_prefixlen // 4 - 1) or 1
    suffix = network.ip.exploded.replace(':', '')[prefixlen:]
    return '.'.join(reversed(suffix))


def calculate_ipv4_pointer(network: _Interface) -> str:
    """
    Return host part of IPv4 network.

    >>> calculate_ipv4_pointer(IPv4Interface(u'1.2.3.4/0'))
    '4.3.2'
    >>> calculate_ipv4_pointer(IPv4Interface(u'1.2.3.4/1'))
    '4.3.2'
    >>> calculate_ipv4_pointer(IPv4Interface(u'1.2.3.4/8'))
    '4.3.2'
    >>> calculate_ipv4_pointer(IPv4Interface(u'1.2.3.4/24'))
    '4'
    >>> calculate_ipv4_pointer(IPv4Interface(u'1.2.3.4/32'))
    '4'
    """
    prefixlen = min(_prefixlen(network) // 8, network.max_prefixlen // 8 - 1) or 1
    suffix = network.ip.exploded.split('.')[prefixlen:]
    return '.'.join(reversed(suffix))
