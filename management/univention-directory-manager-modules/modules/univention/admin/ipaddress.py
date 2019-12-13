# -*- coding: utf-8 -*-
"""
|UDM| functions for checking/manipulating |IP| addresses and ranges.
"""
# Copyright 2004-2019 Univention GmbH
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

from __future__ import absolute_import

import socket
import struct
try:
	from typing import Tuple  # noqa F401
except ImportError:
	pass


def dotted2int(ds):
	# type: (str) -> int
	"""
	Convert dotted-quad |IPv4| address to integer.

	:param ds: An |IPv4| address in dotted-quad notation.
	:returns: The numeric |IPv4| address.

	>>> dotted2int('0.0.0.0')
	0
	"""
	return struct.unpack('!I', socket.inet_aton(ds))[0]


def int2dotted(i):
	# type: (int) -> str
	"""
	Convert integer address to dotted-quad |IPv4| address.

	:param i: A numeric |IPv4| address.
	:returns: An |IPv4| address in dotted-quad notation.

	>>> int2dotted(0)
	'0.0.0.0'
	"""
	return socket.inet_ntoa(struct.pack('!I', i))


def ip_plus_one(ip):
	# type: (str) -> str
	"""
	Return logical next |IPv4| address.

	:param ip: An |IPv4| address in dotted-quad notation.
	:returns: An |IPv4| address in dotted-quad notation.

	>>> ip_plus_one('0.0.0.0')
	'0.0.0.1'
	>>> ip_plus_one('0.0.0.254')
	'0.0.1.0'
	>>> ip_plus_one('0.0.0.255')
	'0.0.1.1'
	"""
	newIp = int2dotted(dotted2int(ip) + 1)
	last = newIp.split('.')[3]
	if last == '255' or last == '0':
		newIp = int2dotted(dotted2int(newIp) + 1)
	return newIp


def ip_is_in_network(subnet, subnetmask, ip):
	# type: (str, str, str) -> int
	"""
	Check if the given |IPv4| address is inside the given subnet.

	:param subnet: A |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `1` if the |IP| address is inside the subnet, `0` otherwise.

	>>> ip_is_in_network('192.0.2.0', 24, '192.0.2.42')
	1
	"""
	lip = struct.unpack('!I', socket.inet_aton(ip))[0] >> 32 - int(subnetmask)
	lnet = struct.unpack('!I', socket.inet_aton(subnet))[0] >> 32 - int(subnetmask)
	if lip == lnet:
		return 1
	return 0


def ip_is_network_address(subnet, subnetmask, ip):
	# type: (str, str, str) -> int
	"""
	Check if the given |IPv4| address is the network address (host bits are all zero).

	:param subnet: A |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `1` if the |IP| address is the network address, `0` otherwise.

	>>> ip_is_network_address('192.0.2.0', 24, '192.0.2.0')
	1
	"""
	network_address = struct.unpack('!I', socket.inet_aton(subnet))[0]
	network_address = network_address >> 32 - int(subnetmask)
	network_address = network_address << 32 - int(subnetmask)
	ip_address = struct.unpack('!I', socket.inet_aton(ip))[0]
	if network_address == ip_address:
		return 1
	return 0


def ip_is_broadcast_address(subnet, subnetmask, ip):
	# type: (str, str, str) -> int
	"""
	Check if the given |IPv4| address is the network broadcast address (host bits are all one).

	:param subnet: The |IPv4| network address.
	:param subnetmask: The |IPv4| network prefix length.
	:param ip: The |IPv4| address to check.
	:returns: `1` if the |IP| address is the network broadcast address, `0` otherwise.

	>>> ip_is_broadcast_address('192.0.2.0', 24, '192.0.2.255')
	1
	"""
	network_address = struct.unpack('!I', socket.inet_aton(subnet))[0]
	shiftbit = 1
	for i in range(0, 32 - int(subnetmask)):
		network_address = network_address ^ shiftbit
		shiftbit = shiftbit << 1
	ip_address = struct.unpack('!I', socket.inet_aton(ip))[0]
	if network_address == ip_address:
		return 1
	return 0


def ip_compare(ip1, ip2):
	# type: (str, str) -> int
	"""
	Compare two |IPv4| addresses in dotted-quad format.

	:param ip1: The first |IPv4| address.
	:param ip2: The second |IPv4| address.
	:returns: `1` if the first address is before the second, `-1` if the first is after the second, or `0` when they are equal.

	>>> ip_compare('192.0.2.1', '192.0.2.2')
	1
	>>> ip_compare('192.0.2.2', '192.0.2.2')
	0
	>>> ip_compare('192.0.2.3', '192.0.2.2')
	-1
	"""
	if not ip1:
		return 1
	if not ip2:
		return -1

	sip1 = ip1.split('.')
	sip2 = ip2.split('.')
	for i in range(0, 4):
		if int(sip1[i]) > int(sip2[i]):
			return -1
		elif int(sip1[i]) < int(sip2[i]):
			return 1

	return 0


def is_ip_in_range(ip, range):
	# type: (str, Tuple[str, str]) -> int
	"""
	Check if a |IPv4| address is inside the given range.

	:param ip: The |IPv4| address to check.
	:param range: The inclusive range as a 2-tuple (low, hight) of |IPv4| addresses.
	:returns: `1` if the address is inside the range, `0` otherwise.

	>>> is_ip_in_range('192.0.2.10', ('192.0.2.0', '192.0.2.255'))
	1
	"""
	if int(ip_compare(ip, range[0])) < 1 and int(ip_compare(ip, range[1])) > -1:
		return 1
	else:
		return 0


def is_range_overlapping(range1, range2):
	# type: (Tuple[str, str], Tuple[str, str]) -> int
	"""
	Check if two |IPv4| addresses overlap.

	:param range1: The first range as a 2-tuple (low, high) of |IPv4| addresses.
	:param range2: The second range as a 2-tuple (low, high) of |IPv4| addresses.
	:returns: `1` if the ranges overlap, `0` otherwise.

	>>> is_range_overlapping(('192.0.2.0', '192.0.2.127'), ('192.0.2.128', '192.0.2.255'))
	0
	>>> is_range_overlapping(('192.0.2.0', '192.0.2.127'), ('192.0.2.64', '192.0.2.191'))
	1
	>>> is_range_overlapping(('192.0.2.0', '192.0.2.255'), ('192.0.2.64', '192.0.2.191'))
	1
	>>> is_range_overlapping(('192.0.2.128', '192.0.2.255'), ('192.0.2.64', '192.0.2.191'))
	1
	"""
	if is_ip_in_range(range1[0], range2) or is_ip_in_range(range1[1], range2):
		return 1
	if is_ip_in_range(range2[0], range1) or is_ip_in_range(range2[1], range1):
		return 1
	return 0


if __name__ == '__main__':
	import doctest
	doctest.testmod()
