#!/usr/bin/python3
# Copyright 2011-2022 Univention GmbH
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

"""Univention IP Calculator for DNS records (IPv6 edition)."""

from typing import Union  # noqa F401

import six

# use ip_interface for networks for py2 py3 compatability
if six.PY3:
	from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
else:
	from ipaddr import IPv4Address, IPv6Address, IPv4Network as IPv4Interface, IPv6Network as IPv6Interface # noqa F401

_Interface = Union[IPv4Interface, IPv6Interface]


def _prefixlen(interface):  # PY2 VS PY3
	# type: (_Interface) -> int
	return interface.prefixlen if hasattr(interface, 'prefixlen') else interface.network.prefixlen  # type: ignore


# IPv4: 4.3.                            2.1.                        IN-ADDR.ARPA
# IPv6: f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.IP6.ARPA
#       \__________ pointer __________/ \__________ reverse __________/
# network: "full network address"
# reverse: dns/reverse_zone.subnet (forward notation)
#          dns/reverse_zone.zoneName (backward notation)
# pointer: dns/ptr_record.address (LDAP: relativeDomainName)


def calculate_ipv6_reverse(network):
	# type: (_Interface) -> str
	"""Return reversed network part of IPv4 network.
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


def calculate_ipv4_reverse(network):
	# type: (_Interface) -> str
	"""Return reversed network part of IPv4 network.
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


def calculate_ipv6_network(network):
	# type: (_Interface) -> str
	"""Return network part of IPv6 network.
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


def calculate_ipv4_network(network):
	# type: (_Interface) -> str
	"""Return network part of IPv4 network.
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


def calculate_ipv6_pointer(network):
	# type: (_Interface) -> str
	"""Return host part of IPv6 network.
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


def calculate_ipv4_pointer(network):
	# type: (_Interface) -> str
	"""Return host part of IPv4 network.
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
