#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Firewall
#  firewall script
#
# Copyright (C) 2004-2007 Univention GmbH
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

import univention_baseconfig, time, os, sys

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()

### functions^Wmethods
def open_iptables_script (file):
	fh = open(file, 'w')
	fh.write('#!/bin/sh\n\n')
	fh.write('#\n# Written by univention-baseconfig at '+time.strftime('%H:%M   %d %b %Y')+' \n#\n\n')
	fh.write('iptables=/sbin/iptables\n\n')
	return fh

# Add a IPTables entry to the INPUT chain
# iptables -A INPUT  -p tcp --dport 111 -j univention-thinclient
# call: add_iptables_entry('tcp', '111', 'thinclient')

def add_iptables_entry(proto, port, action):
	jump = ""
	
	if action == 'deny':
		if proto == 'tcp':
			jump = 'REJECT --reject-with tcp-reset'
		if proto == 'udp':
			jump = 'DROP'
	elif action == 'accept':
		jump = 'ACCEPT'

	return ('$iptables -A INPUT -p %s --dport %s -j %s\n' % (proto, port, jump))


# Important initialize
# This is the data one firewall-service record consists of
# After all data has been collected out of the baseconfig the
# entry is written as iptables script
oldservice = ''
udp = {}
tcp = {}
allowip = []
denyip = []
log = ''
policy = ''
enable = ''

# Open the main file
fh_accept = open_iptables_script("/etc/security/netfilter.d/10accept")
fh_deny = open_iptables_script("/etc/security/netfilter.d/15deny")

base = baseConfig.keys()
base.sort()

for key in base:
	value = baseConfig[key]
	#print "[%s]\t\t%s" % (key, value)


	if key.startswith('security/packetfilter/tcp/') or key.startswith('security/packetfilter/udp/'):
		tmp = key.split('/')
		proto = tmp[2]
		action = tmp[3]

		if action == 'accept' or action == 'deny':
			port = value
			port_chunks = port.split(",")
			for i in port_chunks:
				port_range = i.split("-")
				if len(port_range) == 1:
					if action == 'deny':
						fh_deny.write(add_iptables_entry(proto, port_range[0], action))
					elif action == 'accept':
						fh_accept.write(add_iptables_entry(proto, port_range[0], action))
				elif len(port_range) == 2:
					if action == 'deny':
						fh_deny.write(add_iptables_entry(proto, (port_range[0] + ":" + port_range[1]), action))
					elif action == 'accept':
						fh_accept.write(add_iptables_entry(proto, (port_range[0] + ":" + port_range[1]), action))
							
				else:
					# Syntax error, log error message
					pass
# Close the main script
fh_accept.write('\n')
fh_deny.write('\n')
fh_accept.close()
fh_deny.close()
os.system("chmod a+x /etc/security/netfilter.d/10accept")
os.system("chmod a+x /etc/security/netfilter.d/15deny")
