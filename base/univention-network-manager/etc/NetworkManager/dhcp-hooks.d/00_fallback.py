#!/usr/bin/python2.4
#
# Univention Network Manager
#  script used by NM as dhclient script
#
# Copyright (C) 2009 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

import os
import socket
import subprocess
import struct
import sys

import univention.config_registry as ucr

VARIABLE_MAP = ( ( 'new_ip_address', 'address' ), ( 'new_broadcast_address', 'broadcast' ), ( 'new_subnet_mask', 'netmask' ), ( 'new_network_number', 'network' ) )

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

new_env = os.environ

def update_ucr_variables( environ ):
	variables = []
	for env, var in VARIABLE_MAP:
		if environ[ env ] != configRegistry.get( 'interfaces/%s/%s' % ( os.environ[ 'interface' ], var ) ):
			variables.append( 'interfaces/%s/%s=%s' % ( os.environ[ 'interface' ], var, environ[ env ] ) )

	ucr.handler_set( variables, quiet=True )

def get_dns_servers():
	# check for a valid nameserver
	nameservers = []
	for i in range( 1, 4 ):
		var = 'nameserver%d' % i
		if var in configRegistry.keys():
			nameservers.append( configRegistry[ var ] )

	return nameservers

if os.environ.get( 'reason' ) in ( 'FAIL', 'TIMEOUT', 'EXPIRE' ):
	new_env[ 'reason' ] = 'BOUND'
	for env, var in VARIABLE_MAP:
		value = configRegistry.get( 'interfaces/%s/fallback/%s' % ( os.environ[ 'interface' ], var ) )
		if value:
			new_env[ env ] = value
	if 'fallback/gateway' in configRegistry.keys():
		new_env[ 'new_routers' ] = configRegistry[ 'fallback/gateway' ]

	# DNS server
	servers = get_dns_servers()
	if servers:
		new_env[ 'new_domain_name_servers' ] = ' '.join( servers )

	# hostname
	if 'hostname' in configRegistry.keys():
		new_env[ 'new_host_name' ] = configRegistry[ 'hostname' ]

	# domainname
	if 'domainname' in configRegistry.keys():
		new_env[ 'new_domain_name' ] = configRegistry[ 'domainname' ]

	# domain search option
	if 'domain/search' in configRegistry.keys():
		new_env[ 'new_domain_search' ] % configRegistry[ 'domain/search' ]
elif os.environ.get( 'reason' ) in ( 'BOUND', 'RENEW', 'REBIND', 'REBOOT' ):
	if configRegistry.get( 'networkmanager/dhcp/options/fallback', 'no' ).lower() in ( 'yes', 'true', '1' ):
		# DNS server
		if not os.environ.get( 'new_domain_name_servers' ):
			servers = get_dns_servers()
			if servers:
				new_env[ 'new_domain_name_servers' ] = ' '.join( servers )

		# hostname
		if not os.environ.get( 'new_host_name' ) and 'hostname' in configRegistry.keys():
			new_env[ 'new_host_name' ] = configRegistry[ 'hostname' ]

		# domainname
		if not os.environ.get( 'new_domain_name' ) and 'domainname' in configRegistry.keys():
			new_env[ 'new_domain_name' ] = configRegistry[ 'domainname' ]

		# gateway
		if not os.environ.get( 'new_routers' ) and 'gateway' in configRegistry.keys():
			new_env[ 'new_routers' ] = configRegistry[ 'gateway' ]

		# domain search option
		if not os.environ.get( 'new_domain_search' ) and 'domain/search' in configRegistry.keys():
			new_env[ 'new_domain_search' ] = configRegistry[ 'domain/search' ]
else:
	sys.exit( 0 )

# check whether a gateway should be set from UCR
if not new_env.get( 'new_routers' ) and 'gateway' in configRegistry.keys():
	new_env[ 'new_routers' ] = configRegistry[ 'gateway' ]
	
# update modified values in UCR variables
update_ucr_variables( new_env )

#print out modified environment variables
for item in new_env.items():
	print 'export %s="%s"' % item

sys.exit( 0 )

	
