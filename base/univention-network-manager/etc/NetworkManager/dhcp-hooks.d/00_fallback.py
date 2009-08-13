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

VARIABLE_MAP = ( ( 'new_ip_address', 'address' ), ( 'new_broadcast_address', 'broadcast' ), ( 'new_sub_netmask', 'netmask' ), ( 'new_network', 'network' ) )

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

def aton( ip_address ):
	'''convert decimal dotted quad string to long integer'''
	return struct.unpack( 'I', socket.inet_aton( ip_address ) )[ 0 ]

def ntoa( num ):
	'''convert long int to dotted quad string'''
	return socket.inet_ntoa( struct.pack( 'I',num ) )
	  
def get_network( ip_address, netmask ):
	'''examples:
	print get_network( '192.168.0.154', '255.255.255.0' )
	print get_network( '192.168.0.154', 24 )'''

	n_ip = aton( ip_address )

	if isinstance( netmask, int ):
		n_mask = ( 2 << ( netmask - 1 ) ) - 1
	else:
		n_mask = aton( netmask )

	n_network = n_ip & n_mask

	return ntoa( n_network )

def update_ucr_variables():
	variables = []
	for env, var in VARIABLE_MAP:
		if os.environ[ env ] != configRegistry.get( 'interfaces/%s/%s' % ( os.environ[ 'interface' ], var ) ):
			variables.append( 'interfaces/%s/%s=%s' % ( os.environ[ 'interface' ], var, os.environ[ env ] ) )

	ucr.handler_set( variables )

def get_dns_servers():
	# check for a valid nameserver
	nameservers = []
	for i in range( 1, 4 ):
		var = 'nameserver%d' % i
		if var in configRegistry:
			namservers.append( configRegistry[ var ] )

	return nameservers

if os.environ.get( 'reason' ) in ( 'FAIL', 'TIMEOUT' ):
	os.environ[ 'reason' ] = 'BOUND'
	for env, var in VARIABLE_MAP:
		print '%s=%s' % ( env, configRegistry.get( 'interfaces/%s/fallback/%s' % ( os.environ[ 'interface' ], var ) ) )
	print '%s=%s' % ( 'new_routers', configRegistry.get( 'fallback/gateway' ) )

	# DNS server
	servers = get_dns_servers()
	if servers:
		print 'new_domain_name_servers=%s' % ','.join( servers )

	# DNS server
	servers = get_dns_servers()
	if servers:
		print 'new_domain_name_servers=%s' % ','.join( servers )

	# hostname
	print 'new_host_name=%s' % configRegistry[ 'hostname' ]

	# domainname
	print 'new_domain_name=%s' % configRegistry[ 'domainname' ]

	# domain search option
	if 'domain/search' in configRegistry:
		print 'new_domain_search=%s' % configRegistry[ 'domain/search' ]
elif os.environ.get( 'reason' ) in ( 'BOUND', 'RENEW', 'REBIND' ):
	print 'new_network=%s' % get_network( os.environ[ 'new_ip_address' ], os.environ[ 'new_sub_netmask' ] )

	# DNS server
	if not os.environ.get( 'new_domain_name_servers' ):
		servers = get_dns_servers()
		if servers:
			print 'new_domain_name_servers=%s' % ','.join( servers )

	# hostname
	if not os.environ.get( 'new_host_name' ):
		print 'new_host_name=%s' % configRegistry[ 'hostname' ]

	# domainname
	if not os.environ.get( 'new_domain_name' ):
		print 'new_domain_name=%s' % configRegistry[ 'domainname' ]

	# domain search option
	if not os.environ.get( 'new_domain_search' ) and 'domain/search' in configRegistry:
		print 'new_domain_search=%s' % configRegistry[ 'domain/search' ]
else:
	sys.exit( 0 )

update_ucr_variables()

sys.exit( 0 )

	
