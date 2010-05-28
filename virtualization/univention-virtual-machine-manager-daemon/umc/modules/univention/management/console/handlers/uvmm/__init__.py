#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright (C) 2010 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct
import univention.management.console.protocol as umcp

import univention.debug as ud
import univention.config_registry as ucr
import univention.service_info as usi
import univention.uvmm.node as uuv_node
import univention.uvmm.protocol as uuv_proto

import copy
import os
import socket

import notifier.popen

import uvmmd
from treeview import TreeView
from tools import *
from types import *

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

name = 'uvmm'
icon = 'uvmm/module'
short_description = _('Virtual Machines')
long_description = _('Univention Virtual Machine Manager')
categories = [ 'system', 'all' ]
hide_tabs = True

# fields of a drive definition
drive_type = umcd.make( ( 'type', DriveTypSelect( _( 'Type' ) ) ) )
drive_uri = umcd.make( ( 'uri', umc.String( 'URI' ) ) )
drive_dev = umcd.make( ( 'dev', umc.String( _( 'Device' ) ) ) )

dest_node_select = NodeSelect( _( 'Destination host' ) )
arch_select = DynamicSelect( _( 'Architecture' ) )
type_select = DynamicSelect( _( 'Virtualization Technique' ) )
cpus_select = NumberSelect( _( 'Number of CPUs' ) )

command_description = {
	'uvmm/overview': umch.command(
		short_description = _('Overview'),
		long_description = _('Overview'),
		method = 'uvmm_overview',
		values = {},
		startup = True,
		),
	'uvmm/group/overview': umch.command(
		short_description = _('Show group information'),
		long_description = _('Show group information'),
		method = 'uvmm_group_overview',
		values = { 'group' : umc.String( 'group' ) },
		),
	'uvmm/node/overview': umch.command(
		short_description = _('Show physical server information'),
		long_description = _('Show physical server information'),
		method = 'uvmm_node_overview',
		values = { 'node' : umc.String( 'node' ) },
		),
	'uvmm/domain/overview': umch.command(
		short_description = _('Show instance information'),
		long_description = _('Show instance information'),
		method = 'uvmm_domain_overview',
		values = { 'domain' : umc.String( 'domain' ) },
		),
	'uvmm/domain/create': umch.command(
		short_description = _('Create a virtual instance'),
		long_description = _('Create a virtual instance'),
		method = 'uvmm_domain_create',
		values = { 'group' : umc.String( 'group' ),
				   'node' : umc.String( 'node' ) },
		),
	'uvmm/domain/remove/images': umch.command(
		short_description = _('Remove drives of a virtual instance'),
		long_description = _('Remove drives of a virtual instance'),
		method = 'uvmm_domain_remove_images',
		values = { 'group' : umc.String( 'group' ),
				   'node' : umc.String( 'node' ),
				   'domain' : umc.String( 'domain' ),
				   },
		),
	'uvmm/domain/remove': umch.command(
		short_description = _('Remove a virtual instance'),
		long_description = _('Remove a virtual instance'),
		method = 'uvmm_domain_remove',
		values = { 'group' : umc.String( 'group' ),
				   'node' : umc.String( 'node' ),
				   'domain' : umc.String( 'domain' ),
				   'drives' : umc.StringList( '' ),
				   },
		confirm = umch.Confirm( _( 'Remove virtual instance' ), _( 'Are you sure that the virtual instance should be removed?' ) ),
		),
	'uvmm/domain/configure': umch.command(
		short_description = _('Configuration of virtual instances'),
		long_description = _('Configuration of virtual instances'),
		method = 'uvmm_domain_configure',
		values = { 'domain' : umc.String( 'instance' ),
				   'name' : umc.String( _( 'Name' ) ),
				   'mac' : umc.String( _( 'MAC address' ), required = False ),
				   'memory' : umc.String( _( 'Memory' ) ),
				   'interface' : umc.String( _( 'Interface' ) ),
				   'cpus' : cpus_select,
				   'vnc' : umc.Boolean( _( 'activate VNC remote access' ) ),
				   'kblayout' : KBLayoutSelect( _( 'Keyboard layout' ) ),
				   'arch' : arch_select,
				   'type' : type_select,
				   'drives' : umc.StringList( _( 'Drive' ) ),
				   'os' : umc.String( _( 'Operating System' ), required = False ),
				   'user' : umc.String( _( 'User' ), required = False ),
				   'initrd' : umc.String( _( 'RAM disk' ), required = False ),
				   'cmdline' : umc.String( _( 'Kernel parameter' ), required = False ),
				   'kernel' : umc.String( _( 'Kernel' ), required = False ),
				   },
		),
	'uvmm/domain/migrate': umch.command(
		short_description = _( 'Migration of virtual instances' ),
		long_description = _( 'Migration of virtual instances' ),
		method = 'uvmm_domain_migrate',
		values = { 'domain' : umc.String( _( 'domain' ) ),
				   'source' : umc.String( 'source node' ),
				   'dest' : dest_node_select,
				  },
		),
	'uvmm/domain/state': umch.command(
		short_description = _( 'Change state of a virtual instance' ),
		long_description = _('Change state of virtual instances' ),
		method = 'uvmm_domain_state',
		values = { 'node' : umc.String( _( 'Instance' ) ),
				   'domain' : umc.String( 'Physical server' ),
				   'state' : umc.String( 'State' ),
				  },
		),
}

class handler( umch.simpleHandler ):
	# level 0 is the container list
	STATES = {
		0 : _( 'unknown' ),
		1 : _( 'running' ),
		2 : _( 'idle' ),
		3 : _( 'paused' ),
		4 : _( 'shut down' ),
		5 : _( 'shut off' ),
		6 : _( 'crashed' ),
		}

	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.uvmm = uvmmd.Client( auto_connect = False )

	@staticmethod
	def _getattr( object, attr, default = '' ):
		value = getattr( object, attr, default )
		if value == None:
			value = ''
		return str( value )

	def uvmm_overview( self, object ):
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object )
		if success:
			res.dialog[ 0 ].set_dialog( umcd.ModuleDescription( 'Univention Virtual Machine Manager', _( 'This UMC module provides a management system for virtualization hosts that are registered within the UCS domain.\nThe tree view on the left side shows an overview of all existing physical servers and the residing virtual instances. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual instance can be invoked on each of the instances.\nAlso possible is the remote access to virtual instances via VNC. Therefor it must be activated in the configuration.\nEach virtual instance entry in the tree view provides access to detailed information und gives the possibility to change the configuration or state and migrated it to another physical server.' ) ) )
		self.finished( object.id(), res )

	def uvmm_group_overview( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: group overview' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', ) )
		if not success:
			self.finished(object.id(), res)
			return

		nodes = self.uvmm.get_group_info( object.options[ 'group' ] )
		content = umcd.List()
		reload_cmd = umcp.SimpleCommand( 'uvmm/group/overview', options = { 'group' : object.options[ 'group' ] } )
		reload_btn = umcd.LinkButton( _( 'Refresh' ), 'actions/refresh', actions = [ umcd.Action( reload_cmd ) ] )
		reload_btn.set_size( umct.SIZE_SMALL )
		content.add_row( [ umcd.Cell( reload_btn, attributes = { 'align' : 'right' } ), ] )
						   
		table = umcd.List()
		table.set_header( [ _( 'Physical server' ), _( 'CPU usage' ), _( 'Memory usage' ) ] )
		for node in nodes:
			node_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name } )
			node_btn = umcd.LinkButton( node.name, actions = [ umcd.Action( node_cmd ) ] )
			cpu_usage = percentage( 0, width = 150 )
			mem_usage = percentage( float( node.curMem ) / node.phyMem * 100, '%s / %s' % ( block2byte( node.curMem ), block2byte( node.phyMem ) ), width = 150 )
			table.add_row( [ node_btn, cpu_usage, mem_usage ] )
		content.add_row( [ table, ] )
		res.dialog[ 0 ].set_dialog( content )
		self.finished(object.id(), res)

	def _create_domain_buttons( self, object, node, domain, overview = 'node', migrate = False, remove = False, remove_failure = 'domain' ):
		buttons = []
		overview_cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % overview, options = object.options )
		
		# migrate? if parameter set
		if migrate:
			cmd = umcp.SimpleCommand( 'uvmm/domain/migrate', options = { 'group' : object.options[ 'group' ], 'source' : node.name, 'domain' : domain.name } )
			buttons.append( umcd.LinkButton( _( 'Migrate' ), actions = [ umcd.Action( cmd ) ] ) )

		# Start? if state is not running, blocked or suspended
		cmd_opts = { 'group' : object.options[ 'group' ], 'node' : node.name, 'domain' : domain.name }
		if not domain.state in ( 1, 2, 3 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN' 
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Start' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )

		# Stop? if state is not stopped or suspended
		if not domain.state in ( 3, 4, 5 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'SHUTDOWN' 
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Stop' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )

		# Suspend? if state is running or blocked
		if domain.state in ( 1, ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'PAUSE' 
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Suspend' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )

		# Resume? if state is paused
		if domain.state in ( 3, ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN' 
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Resume' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )

		# Remove? always
		if remove:
			opts = copy.copy( cmd_opts )
			cmd = umcp.SimpleCommand( 'uvmm/domain/remove/images', options = opts )
			buttons.append( umcd.LinkButton( _( 'Remove' ), actions = [ umcd.Action( cmd ), ] ) )

		# VNC? if running and activated
		if domain.state in ( 1, 2 ) and domain.graphics and domain.graphics[ 0 ].port != -1:
			host = node.name
			try:
				VNC_LINK_BY_NAME, VNC_LINK_BY_IPV4, VNC_LINK_BY_IPV6 = range(3)
				vnc_link_format = VNC_LINK_BY_IPV4
				if vnc_link_format == VNC_LINK_BY_IPV4:
					addrs = socket.getaddrinfo(host, None, socket.AF_INET)
					(family, socktype, proto, canonname, sockaddr) = addrs[0]
					host = sockaddr[0]
				elif vnc_link_format == VNC_LINK_BY_IPV6:
					addrs = socket.getaddrinfo(host, None, socket.AF_INET6)
					(family, socktype, proto, canonname, sockaddr) = addrs[0]
					host = '[%s]' % sockaddr[0]
			except: pass
			vnc = domain.graphics[ 0 ]
			uri = 'vnc://%s:%s' % (host, vnc.port)
			buttons.append( umcd.Link( 'VNC', uri ) )

		return buttons

	def uvmm_node_overview( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: node overview' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node' ) )
		if not success:
			self.finished(object.id(), res)
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )

		content = umcd.List()
		reload_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = { 'group' : object.options[ 'group' ], 'node' : object.options[ 'node' ] } )
		reload_btn = umcd.LinkButton( _( 'Refresh' ), 'actions/refresh', actions = [ umcd.Action( reload_cmd ) ] )
		reload_btn.set_size( umct.SIZE_SMALL )
		# content.add_row( [ umcd.Cell( reload_btn, attributes = { 'align' : 'right' } ), ] )

		node_table = umcd.List()
		node_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name } )
		node_btn = umcd.LinkButton( node.name, actions = [ umcd.Action( node_cmd ) ] )
		cpu_usage = percentage( 0, width = 150 )
		mem_usage = percentage( float( node.curMem ) / node.phyMem * 100, '%s / %s' % ( block2byte( node.curMem ), block2byte( node.phyMem ) ), width = 150 )
		node_table.add_row( [ _( 'Physical server' ), node_btn ] )
		node_table.add_row( [ _( 'CPU usage' ), cpu_usage ] )
		node_table.add_row( [ _( 'Memory usage' ), mem_usage ] )
		content.add_row( [ umcd.Section( _( 'Physical server' ), node_table ), umcd.Cell( reload_btn, attributes = { 'align' : 'right', 'valign' : 'top' } ) ] )

		table = umcd.List()
		num_buttons = 0
		for domain in node.domains:
			# ignore XEN Domain-0
			if domain.name == 'Domain-0':
				continue
			domain_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name, 'domain' : domain.name } )
			domain_btn = umcd.LinkButton( domain.name, actions = [ umcd.Action( domain_cmd ) ] )
			buttons = self._create_domain_buttons( object, node, domain, remove_failure = 'node' )
			if len( buttons ) > num_buttons:
				num_buttons = len( buttons )
			mem_usage = percentage( int( float( domain.curMem ) / domain.maxMem * 100 ), label = '%s / %s' % ( block2byte( domain.curMem ), block2byte( domain.maxMem ) ), width = 120 )
			table.add_row( [ domain_btn, handler.STATES[ domain.state ], domain.virt_tech, percentage( float( domain.cputime[ 0 ] ) / 10, width = 80 ), mem_usage, ] + buttons )

		if len( table.get_content() ):
			table.set_header( [ _( 'Instance' ), _( 'Status' ), _( 'Operating System' ), _( 'CPU usage' ), _( 'Memory usage' ) ] )

		content.add_row( [ umcd.Cell( table, attributes = { 'colspan' : '2' } ), ] )
		res.dialog[ 0 ].set_dialog( content )
		self.finished(object.id(), res)

	def _dlg_domain_settings( self, object, node, domain_info ):
		content = umcd.List()

		types = []
		archs = []
		for template in node.capabilities:
			if not template.os_type in types:
				types.append( template.os_type )
			if not template.arch in archs:
				archs.append( template.arch )
		type_select.update_choices( types )
		arch_select.update_choices( archs )
									
		name = umcd.make( self[ 'uvmm/domain/configure' ][ 'name' ], default = handler._getattr( domain_info, 'name', '' ) )
		os_type = umcd.make( self[ 'uvmm/domain/configure' ][ 'type' ], default = handler._getattr( domain_info, 'os_type', 'xen' ) )
		arch = umcd.make( self[ 'uvmm/domain/configure' ][ 'arch' ], default = handler._getattr( domain_info, '', 'i686' ) )
		os = umcd.make( self[ 'uvmm/domain/configure' ][ 'os' ], default = handler._getattr( domain_info, 'os', 'unknown' ) )
		cpus_select.max = int( node.cpus )
		cpus = umcd.make( self[ 'uvmm/domain/configure' ][ 'cpus' ], default = handler._getattr( domain_info, 'vcpus', '1' ) )
		mem = handler._getattr( domain_info, 'maxMem', '0' )
		memory = umcd.make( self[ 'uvmm/domain/configure' ][ 'memory' ], default = block2byte( mem ) )
		if domain_info and domain_info.interfaces:
			iface = domain_info.interfaces[ 0 ]
			iface_mac = iface.mac_address
			iface_source = iface.source
		else:
			iface_mac = ''
			iface_device = ''
			iface_source = ''
		mac = umcd.make( self[ 'uvmm/domain/configure' ][ 'mac' ], default = iface_mac )
		interface = umcd.make( self[ 'uvmm/domain/configure' ][ 'interface' ], default = iface_source )
		ram_disk = umcd.make( self[ 'uvmm/domain/configure' ][ 'initrd' ], default = handler._getattr( domain_info, 'initrd', '' ) )
		root_part = umcd.make( self[ 'uvmm/domain/configure' ][ 'cmdline' ], default = handler._getattr( domain_info, 'cmdline', '' ) )
		kernel = umcd.make( self[ 'uvmm/domain/configure' ][ 'kernel' ], default = handler._getattr( domain_info, 'kernel', '' ) )
		if domain_info and domain_info.disks:
			defaults = []
			for disk in domain_info.disks:
				if not disk.source: continue
				value = '%s,%s:%s,%s' % ( uuv_node.Disk.map_device( id = disk.device ), disk.driver, disk.source, disk.target_dev )
				defaults.append( ( value, value ) )
			drives = umcd.MultiValue( self[ 'uvmm/domain/configure' ][ 'drives' ], fields = [ drive_type, drive_uri, drive_dev ], separator = ',', label = _( 'Drives' ),
									  default = defaults )
		else:
			drives = umcd.MultiValue( self[ 'uvmm/domain/configure' ][ 'drives' ], fields = [ drive_type, drive_uri, drive_dev ], separator = ',', label = _( 'Drives' ) )
		vnc_bool = False
		vnc_keymap = 'de-de'
		if domain_info and domain_info.graphics:
			for gfx in domain_info.graphics:
				if gfx.type == uuv_node.Graphic.TYPE_VNC:
					vnc_bool = ( gfx.port != -1 )
					vnc_keymap = gfx.keymap
					break
		
		vnc = umcd.make( self[ 'uvmm/domain/configure' ][ 'vnc' ], default = vnc_bool )
		kblayout = umcd.make( self[ 'uvmm/domain/configure' ][ 'kblayout' ], default = vnc_keymap )

		content.add_row( [ name, os ] )
		content.add_row( [ arch, os_type ] )
		content.add_row( [ cpus, mac ] )
		content.add_row( [ memory, interface ] )

		content2 = umcd.List()
		content2.add_row( [ ram_disk, umcd.Cell( drives, attributes = { 'rowspan' : '6' } ) ] )
		content2.add_row( [ root_part ] )
		content2.add_row( [ kernel ] )

		content2.add_row( [ umcd.Text( '' ) ] )

		content2.add_row( [ vnc ] )
		content2.add_row( [ kblayout ] )

		content2.add_row( [ umcd.Text( '' ) ] )

		content.add_row( [ umcd.Cell( umcd.Section( _( 'Extended Settings' ), content2, hideable = True, hidden = True, name = 'subsection.%s' % domain_info.name ), attributes = { 'colspan' : '2' } ), ] )

		ids = ( name.id(), os.id(), os_type.id(), arch.id(), cpus.id(), mac.id(), memory.id(), interface.id(), ram_disk.id(), root_part.id(), kernel.id(), drives.id(), vnc.id(), kblayout.id() )
		cfg_cmd = umcp.SimpleCommand( 'uvmm/domain/configure', options = object.options )
		overview_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = object.options )
		content.add_row( [ '', umcd.Button( _( 'Save' ), actions = [ umcd.Action( cfg_cmd, ids ), umcd.Action( overview_cmd ) ] ) ] )

		return content

	def uvmm_domain_overview( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain overview' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		blind_table = umcd.List()
		
		reload_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = { 'group' : object.options[ 'group' ], 'node' : object.options[ 'node' ], 'domain' : object.options[ 'domain' ] } )
		reload_btn = umcd.LinkButton( _( 'Refresh' ), 'actions/refresh', actions = [ umcd.Action( reload_cmd ) ] )
		reload_btn.set_size( umct.SIZE_SMALL )
		# blind_table.add_row( [ umcd.Cell( reload_btn, attributes = { 'align' : 'right' } ), ] )

		infos = umcd.List()
		infos.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Status' ) ), handler.STATES[ domain_info.state ] ] )
		infos.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Operating System' ) ), 'FIXME' ] )

		stats = umcd.List()
		mem_usage = percentage( int( float( domain_info.curMem ) / domain_info.maxMem * 100 ), label = '%s / %s' % ( block2byte( domain_info.curMem ), block2byte( domain_info.maxMem ) ), width = 130 )
		cpu_usage = percentage( float( domain_info.cputime[ 0 ] ) / 10, width = 130 )
		stats.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Memory usage' ) ), mem_usage ] )
		stats.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'CPU usage' ) ), cpu_usage ] )

		ops = umcd.List()
		buttons = self._create_domain_buttons( object, node, domain_info, overview = 'domain', migrate = True, remove = True )
		ops.add_row( buttons )

		tab = umcd.List()
		tab.add_row( [ infos, stats ] )

		blind_table.add_row( [ umcd.Section( _( 'Virtual instance %(domain)s' ) % { 'domain' : domain_info.name }, tab ), umcd.Cell( reload_btn, attributes = { 'align' : 'right', 'valign' : 'top' } ) ] )
		blind_table.add_row( [ umcd.Cell( umcd.Section( 'Operations', ops ), attributes = { 'colspan' : '2' } ) ] )

		content = self._dlg_domain_settings( object, node, domain_info )
		blind_table.add_row( [ umcd.Cell( umcd.Section( _( 'Settings' ), content, hideable = True, hidden = True, name = 'section.%s' % domain_info.name ), attributes = { 'colspan' : '2' } ) ] )
		
		res.dialog[ 0 ].set_dialog( blind_table )
		self.finished(object.id(), res)

	def uvmm_domain_migrate( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain migrate' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'source', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		content = umcd.List()
		if 'dest' in object.options:
			src_uri = self.uvmm.node_name2uri( object.options[ 'source' ] )
			dest_uri = self.uvmm.node_name2uri( object.options[ 'dest' ] )
			domain_info = self.uvmm.get_domain_info( src_uri, object.options[ 'domain' ] )
			ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: migrate: %s, %s, %s' % ( src_uri, dest_uri, domain_info ) )
			resp = self.uvmm.domain_migrate( src_uri, dest_uri, domain_info.uuid )
			# res.dialog[ 0 ].set_dialog( umcd.InfoBox( _( 'The migration was successfull' ) ) )
		else:
			domains = self.uvmm.get_group_info( object.options[ 'group' ] )
			dest_node_select.update_choices( [ domain.name for domain in domains ], object.options[ 'source' ] )
			content.set_header( [ umcd.Text( _( 'Migrate %(domain)s from %(source)s to:' ) % object.options ) ] )
			dest = umcd.make( self[ 'uvmm/domain/migrate' ][ 'dest' ] )
			content.add_row( [ dest, '' ] )
			opts = copy.copy( object.options )
			cmd_success = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = opts ), [ dest.id(), ], status_range = umcd.Action.SUCCESS )
			opts2 = copy.copy( object.options )
			opts2[ 'node' ] = object.options[ 'source' ]
			cmd_failure = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = opts2 ), status_range = umcd.Action.FAILURE )
			
			content.add_row( [ '', umcd.Button( _( 'Migrate' ), actions = [ umcd.Action( umcp.SimpleCommand( 'uvmm/domain/migrate', options = object.options ), [ dest.id() ] ), cmd_success, cmd_failure ] ) ] )
			res.dialog[ 0 ].set_dialog( content )
			resp = None

		if resp and self.uvmm.is_error( resp ):
			res.status( 301 )
			ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: migrate: error: %s' % str( resp.msg ) )
			self.finished( object.id(), res, report = str( resp.msg ) )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_configure( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain configure' )		
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		domain = uuv_proto.Data_Domain()
		if domain_info:
			domain.uuid = domain_info.uuid
		domain.name = object.options[ 'name' ]
		domain.virt_tech = object.options[ 'type' ]
		domain.os = object.options[ 'os' ]
		domain.arch = object.options[ 'arch' ]
		domain.vcpus = int( object.options[ 'cpus' ] )
		domain.kernel = object.options[ 'kernel' ]
		domain.cmdline = object.options[ 'cmdline' ]
		domain.initrd = object.options[ 'initrd' ]
		domain.maxMem = byte2block( object.options[ 'memory' ] )

		# interface
		iface = uuv_node.Interface()
		iface.mac_address = object.options[ 'mac' ]
		iface.source = object.options[ 'interface' ]
		domain.interfaces.append( iface )

		# disks
		for drive in object.options[ 'drives' ]:
			dev, uri, target = drive.split( ',' )
			disk = uuv_node.Disk()
			disk.device = uuv_node.Disk.map_device( name = dev )
			disk.type = uuv_node.Disk.TYPE_FILE
			if uri.find( ':' ) != -1:
				disk.source = uri.split( ':' )[ 1 ]
			else:
				disk.source = uri
			disk.target_dev = target
			domain.disks.append( disk )
			ud.debug( ud.ADMIN, ud.ERROR, 'drive: %s' % str( disk ) )

		# graphics
		if object.options[ 'vnc' ]:
			gfx = uuv_node.Graphic()
			gfx.keymap = object.options[ 'kblayout' ]
			domain.graphics.append( gfx )

		resp = self.uvmm.domain_configure( object.options[ 'node' ], domain )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = resp.msg )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_state( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain state' )		
		res = umcp.Response( object )

		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: change domain state to %s' % object.options[ 'state' ] )
		resp = self.uvmm.domain_set_state( object.options[ 'node' ], object.options[ 'domain' ], object.options[ 'state' ] )
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: changed domain state to %s' % object.options[ 'state' ] )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = str( resp.msg ) )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_create( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain create' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )
		content = self._dlg_domain_settings( object, node, None )

		res.dialog[ 0 ].set_dialog( umcd.Section( _( 'Add virtual instance' ), content, hideable = False ) )

		self.finished(object.id(), res)

	def uvmm_domain_remove_images( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain remove images' )		
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		boxes = []
		lst = umcd.List()

		lst.add_row( [ umcd.Cell( umcd.Text( _( 'When removing a virtual instance the disk images bind to it may be removed also. Please select the disks that should be remove with the virtual instance. Be sure that none of the images to be delete are just by any other instance.' ) ), attributes = { 'colspan' : '3' } ) ] )
		lst.add_row( [ '' ] )
		if domain_info.disks:
			defaults = []
			for disk in domain_info.disks:
				if not disk.source: continue
				static_options = { 'drives' : disk.source }
				chk_button = umcd.Checkbox( static_options = static_options )
				chk_button.set_text( '%s: %s' % ( uuv_node.Disk.map_device( id = disk.device ), disk.source ) )
				boxes.append( chk_button.id() )
				lst.add_row( [ umcd.Cell( umcd.Text( '' ), attributes = { 'width' : '10' } ), umcd.Cell( chk_button, attributes = { 'colspan' : '2' } ) ] )

			opts = copy.copy( object.options )
			opts[ 'drives' ] = []			
			back = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			req = umcp.SimpleCommand( 'uvmm/domain/remove', options = opts )
			fail_overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			success_overview_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = opts )
			cancel = umcd.Button( _( 'Cancel' ), actions = [ umcd.Action( back ) ] )
			button = umcd.Button( _( 'Remove' ), actions = [ umcd.Action( req, boxes ), umcd.Action( success_overview_cmd, status_range = umcd.Action.SUCCESS ), umcd.Action( fail_overview_cmd, status_range = umcd.Action.FAILURE ) ] )
			lst.add_row( [ '' ] )
			lst.add_row( [ umcd.Cell( cancel, attributes = { 'align' : 'right', 'colspan' : '2' } ), umcd.Cell( button, attributes = { 'align' : 'right' } ) ] )
			
		res.dialog[ 0 ].set_dialog( umcd.Section( _( 'Remove the virtual instance %(instance)s?' ) % { 'instance' : domain_info.name }, lst, hideable = False ) )
		self.finished(object.id(), res)
		
	def uvmm_domain_remove( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'CRUNCHY: domain remove' )		
		res = umcp.Response( object )

		
		# remove domain
		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
		resp = self.uvmm.domain_undefine( node_uri, domain_info.uuid, object.options[ 'drives' ] )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Removing the instance <i>%(domain)s</i> failed' ) % { 'domain' : object.options[ 'domain' ] } )
		else:
			res.status( 201 )
			self.finished( object.id(), res, report = _( 'The instance <i>%(domain)s</i> was removed successfully' ) % { 'domain' : object.options[ 'domain' ] } )
