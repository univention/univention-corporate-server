#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Python
#  DNS utilities
#
# Copyright 2002-2010 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

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
