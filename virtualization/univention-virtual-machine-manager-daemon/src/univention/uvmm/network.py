# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  network management
#
# Copyright 2011-2015 Univention GmbH
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
"""UVMM storage handler.

This module implements functions to handle network configurations. 
"""

import libvirt
import logging
from helpers import TranslatableException, N_ as _
from protocol import Network

logger = logging.getLogger('uvmmd.network')

class NetworkError( TranslatableException ):
	'''Error occurred during operation on network object'''
	pass

def network_is_active( conn, name ):
	'''checks if the network with the given name ist currently active'''
	try:
		return name in conn.listNetworks()
	except libvirt.libvirtError, e:
		logger.error( e )
		raise NetworkError( _( 'Error retrieving list of active networks: %(error)s' ), error = e.get_error_message() )

def network_start( conn, name ):
	'''Starts the network specified by given name. Returns Trie if the
	network could be activated or if it was already active.'''
	try:
		network = conn.networkLookupByName( name )
		if not network.autostart():
			network.setAutostart( True )
		if not network.isActive():
			return network.create() == 0
		return True
	except libvirt.libvirtError, e:
		logger.error( e )
		raise NetworkError( _( 'Error starting network %(name)s: %(error)s' ), name = name, error = e.get_error_message() )

def network_find_by_bridge( conn, bridge ):
	try:
		networks = conn.listNetworks() + conn.listDefinedNetworks()
	except libvirt.libvirtError, e:
		logger.error( e )
		raise NetworkError( _( 'Error retrieving list of networks: %(error)s' ), error = e.get_error_message() )
	for name in networks:
		try:
			net = conn.networkLookupByName( name )
		except libvirt.libvirtError, e:
			logger.error( e )
		if net.bridgeName() == bridge:
			network = Network()
			network.uuid = net.UUIDString()
			network.name = net.name()
			network.bridge = net.bridgeName()
			return network

	return None
