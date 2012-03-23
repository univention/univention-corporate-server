# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  config registry module for the network interfaces
#
# Copyright 2004-2011 Univention GmbH
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

import os

def interface(var):
	if var.startswith('interfaces/') and not var.endswith( 'handler' ):
		return var.split('/')[1].replace('_', ':')
	return None

def stop_iface(iface):
	if iface:
		os.system('ifdown %s >/dev/null 2>&1' % iface)

def start_iface(iface):
	if iface:
		os.system('ifup %s' % iface)

def point2point(old, new, netmask):
	if netmask == "255.255.255.255":
		os.system('ip route del %s' % old)
		if new:
			os.system('ip route add %s/32 dev eth0 ' % new)

def restore_gateway(gateway, netmask):
	if type ( gateway ) == type ( () ):
		old, new = gateway
		if new:
			point2point(old, new, netmask)
			os.system('route del default >/dev/null 2>&1')
			os.system('route add default gw %s' % new)
   		else:
			point2point(old, False, netmask)
			os.system('route del default >/dev/null 2>&1')
	else:
		if gateway:
			point2point(gateway, gateway, netmask)
			os.system('route del default >/dev/null 2>&1')
			os.system('route add default gw %s' % gateway)

def restore_v6gateway(gateway):
	if type(gateway) is tuple:
		(old, new, ) = gateway
		if not new:
			os.system('ip -6 route del to default via %s' % old)
		elif not old:
			os.system('ip -6 route del to default')
			os.system('ip -6 route add to default via %s' % new)
		else:
			os.system('ip -6 route del to default via %s' % old)
			os.system('ip -6 route add to default via %s' % new)
	else:
		if gateway:
			os.system('ip -6 route del to default')
			os.system('ip -6 route add to default via %s' % gateway)

def preinst(configRegistry, changes):
	if configRegistry.is_true('interfaces/restart/auto', True):
		for iface in set(changes):
			if iface in configRegistry:
				stop_iface(interface(iface))

def postinst(configRegistry, changes):
	if configRegistry.is_true('interfaces/restart/auto', True):
		for iface in set(changes):
			if iface in configRegistry:
				start_iface(interface(iface))
		if 'gateway' in set(changes) or 'interfaces/eth0/netmask' in set(changes):
			if 'gateway' in set(changes):
				restore_gateway(changes['gateway'], configRegistry.get("interfaces/eth0/netmask", False))
			else:
				restore_gateway(configRegistry.get("gateway", False), configRegistry.get("interfaces/eth0/netmask", False))
		if 'ipv6/gateway' in changes:
			restore_v6gateway(changes['ipv6/gateway'])
