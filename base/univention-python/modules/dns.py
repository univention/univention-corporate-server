#!/usr/bin/python2.4
#
# Univention Python
#  DNS utilities
#
# Copyright (C) 2002, 2003, 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import DNS

DNS.DiscoverNameServers()

def lookup(query, type='a'):
	result=map(lambda(x): x['data'], DNS.DnsRequest(query, qtype=type).req().answers)
	return result

def splitDotted(ip):
	quad = [0, 0, 0, 0]

	i = 0
	for q in ip.split('.'):
		if i > 3: break
		quad[i] = int(q)
		i += 1

	return quad

def joinDotted(ip):
	return '%d.%d.%d.%d' % (ip[0], ip[1], ip[2], ip[3])

def networkNumber(dottedIp, dottedNetmask):
	ip = splitDotted(dottedIp)
	netmask = splitDotted(dottedNetmask)
	network = [0,0,0,0]

	for i in range(0,4):
		network[i] = ip[i] & netmask[i]

	return joinDotted(network)

def broadcastNumber(dottedNetwork, dottedNetmask):
	network = splitDotted(dottedNetwork)
	netmask = splitDotted(dottedNetmask)
	broadcast = [0,0,0,0]

	for i in range(0,4):
		broadcast[i] = (network[i] ^ 255) ^ netmask[i]

	return joinDotted(broadcast)

if __name__ == '__main__':
	print networkNumber('192.168.0.1', '255.255.255.0')
	print broadcastNumber('192.168.0.0', '255.255.255.0')
