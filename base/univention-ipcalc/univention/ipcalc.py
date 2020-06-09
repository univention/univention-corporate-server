#!/usr/bin/python2.7
#
"""Univention IP Calculator for DNS records (IPv6 edition)."""
#
# Copyright 2011-2020 Univention GmbH
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

import sys
import six
if six.PY3:
	from ipaddress import IPv6Interface, IPv4Interface

	class IPv4Network(IPv4Interface):
		def __init__(self, address, strict=True):
			IPv4Interface.__init__(self, address)

	class IPv6Network(IPv6Interface):
		def __init__(self, address, strict=True):
			IPv6Interface.__init__(self, address)

else:
	from ipaddress import IPv6Network, IPv4Network


def _prefixlen(interface):  # PY2 VS PY3
	return interface.network.prefixlen if not hasattr(interface, 'prefixlen') else interface.prefixlen


# IPv4: 4.3.                            2.1.                        IN-ADDR.ARPA
# IPv6: f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.IP6.ARPA
#       \__________ pointer __________/ \__________ reverse __________/
# network: "full network address"
# reverse: dns/reverse_zone.subnet (forward notation)
#          dns/reverse_zone.zoneName (backward notation)
# pointer: dns/ptr_record.address (LDAP: relativeDomainName)


def calculate_ipv6_reverse(network):
	"""Return reversed network part of IPv4 network.
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0', False))
	'0'
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1', False))
	'0'
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4', False))
	'0'
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/16', False))
	'0123'
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/124', False))
	'0123:4567:89ab:cdef:0123:4567:89ab:cde'
	>>> calculate_ipv6_reverse(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128', False))
	'0123:4567:89ab:cdef:0123:4567:89ab:cde'
	"""
	# at least one part must remain for zone entry
	prefixlen = min(_prefixlen(network) // 4, network.max_prefixlen // 4 - 1) or 1
	prefix = network.network_address.exploded.replace(':', '')[:prefixlen]
	return ':'.join([prefix[i:i + 4] for i in range(0, len(prefix), 4)])


def calculate_ipv4_reverse(network):
	"""Return reversed network part of IPv4 network.
	>>> calculate_ipv4_reverse(IPv4Network(u'1.2.3.4/0', False))
	'1'
	>>> calculate_ipv4_reverse(IPv4Network(u'1.2.3.4/8', False))
	'1'
	>>> calculate_ipv4_reverse(IPv4Network(u'1.2.3.4/16', False))
	'1.2'
	>>> calculate_ipv4_reverse(IPv4Network(u'1.2.3.4/24', False))
	'1.2.3'
	>>> calculate_ipv4_reverse(IPv4Network(u'1.2.3.4/32', False))
	'1.2.3'
	"""
	# at least one part must remain for zone entry
	prefixlen = min(_prefixlen(network) // 8, network.max_prefixlen // 8 - 1) or 1
	prefix = network.network_address.exploded.split('.')[:prefixlen]
	return '.'.join(prefix)


def calculate_ipv6_network(network):
	"""Return network part of IPv6 network.
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0', False))
	''
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1', False))
	''
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4', False))
	'0'
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/16', False))
	'0123'
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/112', False))
	'0123:4567:89ab:cdef:0123:4567:89ab'
	>>> calculate_ipv6_network(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128', False))
	'0123:4567:89ab:cdef:0123:4567:89ab:cdef'
	"""
	prefixlen = _prefixlen(network) // 4
	prefix = network.network_address.exploded.replace(':', '')[:prefixlen]
	return ':'.join([prefix[i:i + 4] for i in range(0, len(prefix), 4)])


def calculate_ipv4_network(network):
	"""Return network part of IPv4 network.
	>>> calculate_ipv4_network(IPv4Network(u'1.2.3.4/0', False))
	''
	>>> calculate_ipv4_network(IPv4Network(u'1.2.3.4/1', False))
	''
	>>> calculate_ipv4_network(IPv4Network(u'1.2.3.4/8', False))
	'1'
	>>> calculate_ipv4_network(IPv4Network(u'1.2.3.4/24', False))
	'1.2.3'
	>>> calculate_ipv4_network(IPv4Network(u'1.2.3.4/32', False))
	'1.2.3.4'
	"""
	prefixlen = _prefixlen(network) // 8
	prefix = network.network_address.exploded.split('.')[:prefixlen]
	return '.'.join(prefix)


def calculate_ipv6_pointer(network):
	"""Return host part of IPv6 network.
	>>> calculate_ipv6_pointer(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/0', False))
	'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
	>>> calculate_ipv6_pointer(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/1', False))
	'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
	>>> calculate_ipv6_pointer(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/4', False))
	'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1'
	>>> calculate_ipv6_pointer(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/124', False))
	'f'
	>>> calculate_ipv6_pointer(IPv6Network(u'0123:4567:89ab:cdef:0123:4567:89ab:cdef/128', False))
	'f'
	"""
	prefixlen = min(_prefixlen(network) // 4, network.max_prefixlen // 4 - 1) or 1
	suffix = network.network_address.exploded.replace(':', '')[prefixlen:]
	return '.'.join(reversed(suffix))


def calculate_ipv4_pointer(network):
	"""Return host part of IPv4 network.
	>>> calculate_ipv4_pointer(IPv4Network(u'1.2.3.4/0', False))
	'4.3.2'
	>>> calculate_ipv4_pointer(IPv4Network(u'1.2.3.4/1', False))
	'4.3.2'
	>>> calculate_ipv4_pointer(IPv4Network(u'1.2.3.4/8', False))
	'4.3.2'
	>>> calculate_ipv4_pointer(IPv4Network(u'1.2.3.4/24', False))
	'4'
	>>> calculate_ipv4_pointer(IPv4Network(u'1.2.3.4/32', False))
	'4'
	"""
	prefixlen = min(_prefixlen(network) // 8, network.max_prefixlen // 8 - 1) or 1
	suffix = network.network_address.exploded.split('.')[prefixlen:]
	return '.'.join(reversed(suffix))


def main():
	"""Run internal test suite."""
	import doctest
	res = doctest.testmod()
	sys.exit(int(bool(res[0])))


if __name__ == "__main__":
	main()
