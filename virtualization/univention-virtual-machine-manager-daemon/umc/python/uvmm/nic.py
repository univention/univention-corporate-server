# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2012 Univention GmbH
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

import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console as umc

import univention.uvmm.node as uvmmn

import univention.debug as ud

import copy
import os

from treeview import *
from types import *
from uvmmd import UvmmError

_ = umc.Translation('univention.management.console.handlers.uvmm').translate
_uvmm_locale = umc.Translation('univention.virtual.machine.manager').translate

nic_driver_select = NIC_DriverSelect()

class NIC_Commands( object ):
	def uvmm_nic_dialog( self, response, domain_info, object, command ):
		nic_driver_select.virttech = domain_info.domain_type
		nic_list = umcd.List( attributes = { 'width' : '100%' }, default_type = 'uvmm_table'  )
		ids = []

		nic_list.add_row( [ umcd.HTML( _( 'Two types of network interfaces are support. The first one is <i>Bridge</i> that requires a static network connection on the physical server that is configurated to be used for bridging. By default the network interface called eth0 is setup for such a case on each UVMM node. If a virtual instance should have more than one bridging network interface, additional network interfaces on the physical server must be configured first. The second type is <i>NAT</i> that provides a private network for virtual instances on the physical server and permits access to the external network. This network type is useful for computers with varying network connections like notebooks. For such an interface the network configuration of the UVMM node needs to be modified. This is done automatically by the UVMM service when starting the virtual instance. Further details about the network configuration can be found in <a href="http://sdb.univention.de/1172" target="_blank">this article</a>.' ), attributes = { 'colspan' : '2' } ) ] )
		options = copy.copy( object.options )
		cmd = umcp.SimpleCommand( 'uvmm/nic/%s' % command, options = options )
		cmd.incomplete = True
		choices = ( ( 'bridge', _( 'Bridge' ) ), ( 'network:default', _( 'NAT' ) ) )
		# TODO currently we just support the network default
		if object.options.get( 'nictype' ) == 'network':
			object.options[ 'nictype' ] = 'network:default'
		nic_type = umcd.SimpleSelectButton( _( 'Type' ), option = 'nictype', choices = choices, actions = [ umcd.Action( cmd ) ], default = object.options.get( 'nictype', 'bridge' ) )
		# nic_type = umcd.make( self[ 'uvmm/nic/create' ][ 'nictype' ] )
		if object.options.get( 'nictype', '' ).startswith( 'network:' ):
			info = umcd.InfoBox( _( 'By default the private network is 192.168.122.0/24' ) )
		else:
			info = ''
		nic_list.add_row( [ nic_type, info ] )
		ids.append( nic_type.id() )

		default_driver = object.options.get( 'driver', None )
		if default_driver is None:
			if domain_info.os_type in ( 'xen', 'linux' ):
				default_driver = 'netfront'
			else:
				default_driver = 'rtl8139'
		nic_driver = umcd.make( self[ 'uvmm/nic/create' ][ 'driver' ], default = default_driver )
		nic_list.add_row( [ nic_driver, '' ] )
		ids.append( nic_driver.id() )

		if object.options.get( 'nictype', 'bridge' ) == 'bridge':
			nic_source = umcd.make( self[ 'uvmm/nic/create' ][ 'source' ], default = object.options.get( 'source', 'eth0' ) )
			info = umcd.InfoBox( _( 'The source is the name of the network interface on the phyiscal server that is configured for bridging. By default it is eth0.' ) )
			nic_list.add_row( [ nic_source, info ] )
			ids.append( nic_source.id() )

		nic_mac = umcd.make( self[ 'uvmm/nic/create' ][ 'mac' ], default = object.options.get( 'mac', '' ) )
		nic_list.add_row( [ nic_mac, '' ] )
		ids.append( nic_mac.id() )

		opts = copy.copy( object.options )
		if not 'nictype' in opts:
			opts[ 'nictype' ] = 'bridge'
		cmd = umcp.SimpleCommand( 'uvmm/nic/%s' % command, options = opts )
		options = copy.copy( object.options )
		for key in ( 'nictype', 'driver', 'source', 'mac' ):
			if key in options:
				del options[ key ]
			if 'old-%s' % key in options:
				del options[ 'old-%s' % key ]
		overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = options )

		nic_type.actions[ 0 ].options = ids

		if command == 'edit':
			btn_text = _( 'Save' )
			title = _( 'Edit network interface' )
		else:
			btn_text = _( 'Add' )
			title = _( 'Adding network interface' )
		nic_list.add_row([
			umcd.Button(_('Cancel'), actions=[umcd.Action(overview_cmd)]),
			umcd.Cell(umcd.Button(btn_text, actions=[umcd.Action(cmd, ids), umcd.Action(overview_cmd)], default=True), attributes={'align': 'right'})
			])

		response.dialog[ 0 ].set_dialog( umcd.Section( title, nic_list, attributes = { 'width' : '100%' } ) )

	def uvmm_nic_create( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Network interface create' )
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			domain_info = tv.domain_info
		except (uvmmd.UvmmError, KeyError), e:
			return self.uvmm_node_overview( object )

		report = ''
		if object.incomplete:
			self.uvmm_nic_dialog( res, domain_info, object, 'create' )
		else:
			iface = self.createNIC( object.options )
			domain_info.interfaces.append( iface )
			try:
				resp = self.uvmm.domain_configure(node_uri, domain_info)
			except UvmmError, e:
				res.status( 301 )
				report = _('Failed to add network interface: %s') % str(e)
		self.finished( object.id(), res, report = report )

	def optionsNIC( self, options ):
		typ = options.get( 'nictype' )
		if typ.find( ':' ) > 0:
			typ = typ.split( ':', 1 )[ 0 ]
		src = options.get( 'source' )
		mac = options.get( 'mac' )

		return typ, src, mac

	def sameNIC( self, source_iface, typ, src, mac ):
		if typ.find( ':' ) > 0:
			typ = typ.split( ':', 1 )[ 0 ]
		return source_iface.map_type( id = source_iface.type ) == typ and  source_iface.source == src and  source_iface.mac_address == mac

	def identifyNIC( self, domain_info, options ):
		typ, src, mac = self.optionsNIC( options )

		for iface in domain_info.interfaces:
			if self.sameNIC( iface, typ, src, mac ):
				ud.debug( ud.ADMIN, ud.INFO, 'NIC identify: found %s: %s, %s, %s' % ( str( iface ), typ, src, mac ) )
				return iface

		ud.debug( ud.ADMIN, ud.INFO, 'NIC identify: NOT found' )

	def removeNIC( self, domain_info, options ):
		"""Remove NIC matching options.target."""
		ud.debug(ud.ADMIN, ud.INFO, 'NIC remove(%r)' % (options,))
		typ, src, mac = self.optionsNIC( options )

		interfaces = []
		for iface in domain_info.interfaces:
			if not self.sameNIC( iface, typ, src, mac ):
				interfaces.append( iface )

		domain_info.interfaces = interfaces

		return domain_info

	def replaceNIC( self, domain_info, new_iface, options ):
		"""Replace NIC matching options.target by new_iface."""
		ud.debug(ud.ADMIN, ud.INFO, 'NIC replace(%r)' % (options,))
		typ, src, mac = self.optionsNIC( options )

		interfaces = []
		ud.debug( ud.ADMIN, ud.INFO, '  -> replace %s, %s, %s' % ( typ, src, mac ) )
		for iface in domain_info.interfaces:
			if not self.sameNIC( iface, typ, src, mac ):
				interfaces.append( iface )
			else:
				ud.debug( ud.ADMIN, ud.INFO, '  -> add new NIC' )
				interfaces.append( new_iface )

		domain_info.interfaces = interfaces

		return domain_info

	def createNIC( self, options ):
		"""Create Interface instance from options."""
		ud.debug(ud.ADMIN, ud.INFO, 'NIC create(%r)' % (options,))
		iface = uvmmn.Interface()
		if options[ 'nictype' ].startswith( 'network:' ):
			typ, src = options[ 'nictype' ].split( ':', 1 )
			iface.type = iface.map_type( name = typ )
			iface.source = src
		else:
			iface.type = iface.map_type( name = options[ 'nictype' ] )
			iface.source = options[ 'source' ]
		if options[ 'driver' ] != 'auto':
			iface.model = options['driver']
		if options[ 'mac' ]:
			iface.mac_address = options[ 'mac' ]
		if options.get('target'):
			iface.target = options['target']

		return iface

	def uvmm_nic_remove( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Network interface remove' )
		res = umcp.Response( object )
		report = ''

		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, object.options['domain'])
		except UvmmError, e:
			return self.uvmm_node_overview( object )
		domain_info = self.removeNIC( domain_info, object.options )

		try:
			resp = self.uvmm.domain_configure(node_uri, domain_info )
		except UvmmError, e:
			res.status( 301 )
			report = _('Failed to remove network interface: %s') % str(e)
		self.finished( object.id(), res, report = report )

	def uvmm_nic_edit( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Network interface edit' )
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			domain_info = tv.domain_info
		except (uvmmd.UvmmError, KeyError), e:
			return self.uvmm_node_overview( object )

		report = ''
		if object.incomplete:
			if not 'old-nictype' in object.options:
				for key in ( 'nictype', 'driver', 'source', 'mac' ):
					object.options[ 'old-%s' % key ] = object.options.get( key, '' )
			self.uvmm_nic_dialog( res, domain_info, object, 'edit' )
		else:
			iface = self.createNIC( object.options )
			for key in ( 'nictype', 'driver', 'source', 'mac' ):
				object.options[ key ] = object.options[ 'old-%s' % key ]
			domain_info = self.replaceNIC( domain_info, iface, object.options )
			try:
				resp = self.uvmm.domain_configure(node_uri, domain_info )
			except UvmmError, e:
				res.status( 301 )
				report = _('Failed to modify network interface: %s') % str(e)
		self.finished( object.id(), res, report = report )
