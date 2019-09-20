#!/bin/sh
@%@UCRWARNING=# @%@
#
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

# initialise IPv4
iptables --wait -F
iptables --wait -F -t nat
iptables --wait -F -t mangle

# accept IPv4 connections from localhost
iptables --wait -A INPUT -i lo -j ACCEPT
iptables --wait -A OUTPUT -o lo -j ACCEPT

# accept established IPv4 connections
iptables --wait -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# accept all ICMP messages
iptables --wait -A INPUT -p icmp -j ACCEPT

# initialise IPv6
ip6tables --wait -F
ip6tables --wait -F -t mangle

# accept IPv6 connections from localhost
ip6tables --wait -A INPUT -i lo -j ACCEPT
ip6tables --wait -A OUTPUT -o lo -j ACCEPT

# accept established IPv6 connections
ip6tables --wait -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# accept all ICMPv6 messages
ip6tables --wait -A INPUT -p icmpv6 -j ACCEPT


@!@
def print_packetfilter(key, value):
	items = key.split('/')
	addrv6 = items[-1]
	addrv4 = items[-1]
	# security/packetfilter/package/univention-samba/tcp/139/all=ACCEPT
	if items[-1].lower() == 'all':
		addrv4 = ''
		addrv6 = ''
	elif items[-1].lower() == 'ipv4':
		addrv6 = None
		addrv4 = ''
	elif items[-1].lower() == 'ipv6':
		addrv4 = None
		addrv6 = ''
	elif ':' in items[-1].lower():
		addrv4 = None
	else:
		addrv6 = None

	if addrv4 is not None:
		if addrv4:
			addrv4 = '-d ' + ''.join([ x for x in addrv4 if x in set('0123456789.')])
		print 'iptables --wait -A INPUT -p "%(protocol)s" %(addr_args)s --dport %(port)s -j %(action)s' % {
			'protocol': items[-3],
			'addr_args': addrv4,
			'port': items[-2],
			'action': value,
			}

	if addrv6 is not None:
		if addrv6:
			addrv6 = '-d ' + ''.join([ x for x in addrv6 if x in set('abcdefABCDEF0123456789:.')])
		print 'ip6tables --wait -A INPUT -p "%(protocol)s" %(addr_args)s --dport %(port)s -j %(action)s' % {
			'protocol': items[-3],
			'addr_args': addrv6,
			'port': items[-2],
			'action': value,
			}


def print_descriptions(var):
	print
	for key in [ x for x in configRegistry.keys() if x.startswith('%s/' % var) ]:
		items = key.split('/')
		pkg = 'user'
		if key.startswith('security/packetfilter/package/'):
			pkg = items[3]
		print '# %s[%s]: %s' % (pkg, items[-1], configRegistry.get(key))


filterlist = {}

import re
rePort = re.compile('^\d+(:\d+)?$')

# get package settings
if configRegistry.is_true('security/packetfilter/use_packages', True):
	for key in [ x for x in configRegistry.keys() if x.startswith('security/packetfilter/package/') ]:
		items = key.split('/')
		# check if UCR variable is valid: security/packetfilter/package/univention-samba/tcp/139/all=ACCEPT
		if items[-3] in ['tcp', 'udp'] and rePort.search(items[-2]) is not None:
			filterlist[ '/'.join(items[-3:]) ] = key

# get user settings
for key in [ x for x in configRegistry.keys() if x.startswith('security/packetfilter/') and not x.startswith('security/packetfilter/package/') ]:
	items = key.split('/')
	# check if UCR variable is valid: security/packetfilter/package/univention-samba/tcp/139/all=ACCEPT
	if items[-3] in ['tcp', 'udp'] and rePort.search(items[-2]) is not None:
		filterlist[ '/'.join(items[-3:]) ] = key

# print values
for ucrkey in filterlist.values():
	print_descriptions(ucrkey)
	print_packetfilter(ucrkey, configRegistry[ucrkey])

@!@
