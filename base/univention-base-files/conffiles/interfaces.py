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

import subprocess
import os

def interface(var):
	if var.startswith('interfaces/') and not var.endswith( 'handler' ):
		return var.split('/')[1].replace('_', ':')
	return None

def stop_iface(iface):
	if iface:
		null = open(os.path.devnull, 'w')
		try:
			subprocess.call(['ifdown', iface], stdout=null, stderr=null)
		finally:
			null.close()

def start_iface(iface):
	if iface:
		subprocess.call(['ifup', iface])

def point2point(old, new, netmask):
	if netmask == "255.255.255.255":
		subprocess.call(['ip', 'route', 'del', old])
		if new:
			subprocess.call(['ip', 'route', 'add', '%s/32' % new, 'dev', 'eth0']) # FIXME: hardcoded eth0

def restore_gateway(gateway, netmask):
	try:
		old, new = gateway
	except (TypeError, ValueError):
		if gateway:
			point2point(gateway, gateway, netmask)
			null = open(os.path.devnull, 'w')
			try:
				subprocess.call(['route', 'del', 'default'], stdout=null, stderr=null)
				subprocess.call(['route', 'add', 'default', 'gw', gateway])
			finally:
				null.close()
	else:
		null = open(os.path.devnull, 'w')
		try:
			if new:
				point2point(old, new, netmask)
				subprocess.call(['route', 'del', 'default'], stdout=null, stderr=null)
				subprocess.call(['route', 'add', 'default', 'gw', new])
			else:
				point2point(old, False, netmask)
				subprocess.call(['route', 'del', 'default'], stdout=null, stderr=null)
		finally:
			null.close()

def preinst(configRegistry, changes):
	for iface in set(changes):
		if iface in configRegistry:
			stop_iface(interface(iface))

def postinst(configRegistry, changes):
	for iface in set(changes):
		if iface in configRegistry:
			start_iface(interface(iface))
	if 'gateway' in set(changes) or 'interfaces/eth0/netmask' in set(changes):
		if 'gateway' in set(changes):
			restore_gateway(changes['gateway'], configRegistry.get("interfaces/eth0/netmask", False))
		else:
			restore_gateway(configRegistry.get("gateway", False), configRegistry.get("interfaces/eth0/netmask", False))
