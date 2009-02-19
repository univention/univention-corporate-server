# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  functions for checking/manipulating ip addresses and ranges
#
# Copyright (C) 2004-2009 Univention GmbH
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

import sys, string
import socket, struct


def dotted2int(ds):
	return struct.unpack('!I', socket.inet_aton(ds))[0]

def int2dotted(i):
	return socket.inet_ntoa(struct.pack('!I', i))

def ip_plus_one(ip):
	newIp = int2dotted(dotted2int(ip) + 1)
	last  = newIp.split('.')[3]
	if last == '255' or last == '0':
		newIp = int2dotted(dotted2int(newIp) + 1)
	return newIp

def ip_is_in_network(subnet, subnetmask, ip):
	lip=struct.unpack('!I', socket.inet_aton(ip))[0] >> 32-int(subnetmask)
	lnet=struct.unpack('!I', socket.inet_aton(subnet))[0] >> 32-int(subnetmask)
	if lip == lnet:
		return 1
	return 0

def ip_is_network_address(subnet, subnetmask, ip):
	network_address = struct.unpack('!I', socket.inet_aton(subnet))[0];
	network_address = network_address >> 32-int(subnetmask)
	network_address = network_address << 32-int(subnetmask)
	ip_address = struct.unpack('!I', socket.inet_aton(ip))[0]
	if network_address == ip_address:
		return 1
	return 0

def ip_is_broadcast_address(subnet, subnetmask, ip):
	network_address = struct.unpack('!I', socket.inet_aton(subnet))[0];
	shiftbit = 1
	for i in range(0, 32-int(subnetmask)):
		network_address = network_address ^ shiftbit;
		shiftbit = shiftbit << 1
	ip_address = struct.unpack('!I', socket.inet_aton(ip))[0]
	if network_address == ip_address:
		return 1
	return 0

def ip_compare(ip1, ip2):
	if not ip1:
		return 1
	if not ip2:
		return -1

	sip1=ip1.split('.')
	sip2=ip2.split('.')
	for i in range(0,4):
		if int(sip1[i]) > int(sip2[i]):
			return -1
		elif int(sip1[i]) < int(sip2[i]):
			return 1

	return 0

def is_ip_in_range(ip, range):
	if int(ip_compare(ip, range[0])) < 1 and int(ip_compare(ip,range[1])) > -1:
		return 1
	else:
		return 0

def is_range_overlapping(range1, range2):
	if is_ip_in_range(range1[0], range2) or is_ip_in_range(range1[1], range2):
		return 1
	if is_ip_in_range(range2[0], range1) or is_ip_in_range(range2[1], range1):
		return 1
	return 0

