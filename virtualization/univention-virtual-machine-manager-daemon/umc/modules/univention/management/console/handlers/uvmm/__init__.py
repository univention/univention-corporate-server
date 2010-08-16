#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010 Univention GmbH
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
import operator
import os
import socket
import time

import notifier.popen

import uvmmd
from treeview import TreeView
from tools import *
from types import *
from wizards import *

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

name = 'uvmm'
icon = 'uvmm/module'
short_description = _('Virtual Machines (UVMM)')
long_description = _('Univention Virtual Machine Manager')
categories = [ 'system', 'all' ]
hide_tabs = True

# fields of a drive definition
drive_type = umcd.make( ( 'type', DriveTypeSelect( _( 'Type' ) ) ), attributes = { 'width' : '250' } )
drive_uri = umcd.make( ( 'uri', umc.String( 'URI' ) ), attributes = { 'width' : '250' } )
drive_dev = umcd.make( ( 'dev', umc.String( _( 'Drive' ) ) ), attributes = { 'width' : '250' } )

boot_dev = umcd.make( ( 'bootdev', BootDeviceSelect( _( 'Boot order' ) ) ), attributes = { 'width' : '200' } )

dest_node_select = NodeSelect( _( 'Destination host' ) )
arch_select = ArchSelect( _( 'Architecture' ) )
type_select = VirtTechSelect( _( 'Virtualization Technology' ), may_change = False )
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
				   'vnc' : umc.Boolean( _( 'VNC remote access' ) ),
				   'vnc_global' : umc.Boolean( _( 'Available globally' ) ),
				   'vnc_passwd' : umc.Password( _( 'Password' ), required = False ),
				   'vnc_passwd_remove' : umc.Boolean( _( 'Remove password' ), required = False ),
				   'kblayout' : KBLayoutSelect( _( 'Keyboard layout' ) ),
				   'arch' : arch_select,
				   'type' : type_select,
				   'drives' : umc.StringList( _( 'Drive' ) ),
				   'os' : umc.String( _( 'Operating System' ), required = False ),
				   'user' : umc.String( _( 'User' ), required = False ),
				   'advkernelconf' : umc.Boolean( _( 'Advanved kernel configuration' ), required = False ),
				   'initrd' : umc.String( _( 'RAM disk' ), required = False ),
				   'cmdline' : umc.String( _( 'Kernel parameter' ), required = False ),
				   'kernel' : umc.String( _( 'Kernel' ), required = False ),
				   'bootdevs' : umc.StringList( _( 'Boot order' ), required = False ),
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
	'uvmm/domain/save': umch.command(
		short_description = _( 'Save virtual instance' ),
		long_description = _( 'Saves the state of a virtual instances' ),
		method = 'uvmm_domain_save',
		values = {},
		),
	'uvmm/domain/restore': umch.command(
		short_description = _( 'Restore virtual instance' ),
		long_description = _( 'Restores the state of a virtual instances' ),
		method = 'uvmm_domain_restore',
		values = {},
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
	'uvmm/drive/create': umch.command(
		short_description = _( 'New Drive' ),
		long_description = _('Create a new drive' ),
		method = 'uvmm_drive_create',
		values = {},
		),
	'uvmm/drive/remove': umch.command(
		short_description = _( 'Remove Drive' ),
		long_description = _('Removes a drive' ),
		method = 'uvmm_drive_remove',
		values = {},
		),
	'uvmm/drive/bootdevice': umch.command(
		short_description = _( 'Set drive as boot device' ),
		long_description = _('Set drive as boot device' ),
		method = 'uvmm_drive_bootdevice',
		values = {},
		),
	'uvmm/daemon/restart': umch.command(
		short_description = _( 'Restarts libvirt service' ),
		long_description = _( 'Restarts libvirt service' ),
		method = 'uvmm_daemon_restart',
		values = {},
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
		self.drive_wizard = DriveWizard( 'uvmm/drive/create' )
		self.domain_wizard = InstanceWizard( 'uvmm/domain/create' )

	@staticmethod
	def _getattr( object, attr, default = '' ):
		value = getattr( object, attr, default )
		if value == None:
			value = ''
		return str( value )

	@staticmethod
	def _getstr( object, attr, default = '' ):
		value = object.options.get( attr, default )
		if value == None:
			value = default
		return value

	def set_content( self, object, content ):
		# create position links
		lst = umcd.List( attributes = { 'width' : '100%', 'type' : 'umc_mini_padding umc_nowrap' } )
		row = []
		options = {}
		keys = []
		refresh = ''
		slash = umcd.Cell( umcd.HTML( '&rarr;' ), attributes = { 'type' : 'umc_mini_padding umc_nowrap' } )
		row.append( umcd.Cell( umcd.HTML( '<b>%s</b>' % _( 'Location:' ) ), attributes = { 'type' : 'umc_mini_padding umc_nowrap' } ) )
		if 'group' in object.options:
			keys.append( 'group' )
			if 'node' in object.options or 'source' in object.options or 'dest' in object.options:
				if 'node' in object.options:
					key = 'node'
				else:
					key = 'dest'
					if 'source' in object.options:
						key = 'source'
				options[ 'node' ] = object.options[ key ]
				keys.append( 'node' )
				if 'domain' in object.options and object.options[ 'domain' ] != 'NONE':
					keys.append( 'domain' )
		opts = {}
		for key in keys[ : -1 ]:
			opts[ key ] = object.options[ key ]
			cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % key , options = copy.copy( opts ) )
			# FIXME: should be removed if UVMMd supports groups
			if key == 'group' and object.options[ key ] == 'default':
				text = _( 'Physical servers' )
			else:
				text = object.options[ key ]
			lnk = umcd.LinkButton( text , actions = [ umcd.Action( cmd ) ] )
			row.append( umcd.Cell( lnk, attributes = { 'type' : 'umc_mini_padding umc_nowrap' } ) )
			row.append( slash )
		refresh = keys[ -1 ]
		opts[ keys[ -1 ] ] = object.options[ keys[ -1 ] ]
		# FIXME: should be removed if UVMMd supports groups
		if refresh == 'group' and opts[ refresh ] == 'default':
			text = _( 'Physical servers' )
		else:
			text = object.options[ refresh ]
		row.append( umcd.Cell( umcd.Text( text ), attributes = { 'type' : 'umc_mini_padding umc_nowrap' } ) )

		reload_cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % refresh, options = copy.copy( opts ) )
		reload_btn = umcd.LinkButton( _( 'Refresh' ), 'actions/refresh', actions = [ umcd.Action( reload_cmd ) ] )
		reload_btn.set_size( umct.SIZE_SMALL )
		row.append( umcd.Cell( reload_btn, attributes = { 'width' : '100%', 'align' : 'right', 'type' : 'umc_mini_padding' } ) )
		lst.add_row( row, attributes = { 'type' : 'umc_mini_padding' } )
		object.dialog[ 0 ].set_dialog( umcd.List( content = [ [ lst, ], [ content, ] ] ) )

	def uvmm_overview( self, object ):
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object )
		if success:
			self.domain_wizard.reset()
			res.dialog[ 0 ].set_dialog( umcd.ModuleDescription( 'Univention Virtual Machine Manager (UVMM)', _( 'This module provides a management interface for physical servers that are registered within the UCS domain.\nThe tree view on the left side shows an overview of all existing physical servers and the residing virtual instances. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual instance can be invoked on each of the instances.\nAlso possible is the remote access to virtual instances via VNC. Therefor it must be activated in the configuration.\nEach virtual instance entry in the tree view provides access to detailed information und gives the possibility to change the configuration or state and migrated it to another physical server.' ) ) )
		self.finished( object.id(), res )

	def uvmm_group_overview( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Group overview' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', ) )
		if not success:
			self.finished(object.id(), res)
			return
		self.domain_wizard.reset()
		nodes = self.uvmm.get_group_info( object.options[ 'group' ] )

		table = umcd.List()
		table.set_header( [ _( 'Physical server' ), _( 'CPU usage' ), _( 'Memory usage' ) ] )
		for node in nodes:
			node_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name } )
			node_btn = umcd.LinkButton( node.name, actions = [ umcd.Action( node_cmd ) ] )
			node_uri = self.uvmm.node_name2uri( node.name )
			if node_uri.startswith( 'xen' ):
				cpu_usage = percentage(float(node.cpu_usage) / 10.0, width=150)
			else:
				cpu_usage = umcd.HTML( '<i>%s</i>' % _( 'not available' ) )
			mem_usage = percentage( float( node.curMem ) / node.phyMem * 100, '%s / %s' % ( MemorySize.num2str( node.curMem ), MemorySize.num2str( node.phyMem ) ), width = 150 )
			table.add_row( [ node_btn, cpu_usage, mem_usage ] )
		self.set_content( res, table )
		self.finished(object.id(), res)

	def _create_domain_buttons( self, object, node, domain, overview = 'node', operations = False, remove_failure = 'domain' ):
		buttons = []
		overview_cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % overview, options = object.options )
		comma = umcd.HTML( '&nbsp;' )
		# migrate? if parameter set
		if operations:
			cmd = umcp.SimpleCommand( 'uvmm/domain/migrate', options = { 'group' : object.options[ 'group' ], 'source' : node.name, 'domain' : domain.name } )
			buttons.append( umcd.LinkButton( _( 'Migrate' ), actions = [ umcd.Action( cmd ) ] ) )
			buttons.append( comma )

		# Start? if state is not running, blocked or suspended
		cmd_opts = { 'group' : object.options[ 'group' ], 'node' : node.name, 'domain' : domain.name }
		if not domain.state in ( 1, 2, 3 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Start' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Stop? if state is not stopped
		if not domain.state in ( 4, 5 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'SHUTDOWN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Stop' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Suspend? if state is running or idle
		if domain.state in ( 1, 2):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'PAUSE'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Suspend' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Resume? if state is paused
		if domain.state in ( 3, ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Resume' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Remove? always
		if operations:
			opts = copy.copy( cmd_opts )
			cmd = umcp.SimpleCommand( 'uvmm/domain/remove/images', options = opts )
			buttons.append( umcd.LinkButton( _( 'Remove' ), actions = [ umcd.Action( cmd ), ] ) )
			buttons.append( comma )

		# TODO: not yet fully implemented
		# # Save? if machine is idle or running
		# if domain.state in ( 1, 2 ):
		# 	opts = copy.copy( cmd_opts )
		# 	cmd = umcp.SimpleCommand( 'uvmm/domain/save', options = opts )
		# 	buttons.append( umcd.LinkButton( _( 'Save' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
		# 	buttons.append( comma )

		# # Restore? if state is not stopped and we have a snapshot
		# if domain.state in ( 5, ) and self.uvmm.snapshot_exists( object.options[ 'node' ], domain ):
		# 	opts = copy.copy( cmd_opts )
		# 	cmd = umcp.SimpleCommand( 'uvmm/domain/restore', options = opts )
		# 	buttons.append( umcd.LinkButton( _( 'Restore' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
		# 	buttons.append( comma )

		# create drive
		# if operations:
		# 	opts = copy.copy( cmd_opts )
		# 	cmd = umcp.SimpleCommand( 'uvmm/drive/create', options = opts )
		# 	buttons.append( umcd.LinkButton( _( 'New Drive' ), actions = [ umcd.Action( cmd ), ] ) )
		# 	buttons.append( comma )

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
			if configRegistry.get('uvmm/umc/vnc', 'internal').lower() in ('external', ):
				uri = 'vnc://%s:%s' % (host, vnc.port)
				html = umcd.HTML( '<a class="nounderline" target="_blank" href="%s"><span class="content">VNC</span></a>' % uri )
			else:
				popupwindow = ("<html><head><title>" + \
				               _("%(dn)s on %(nn)s") + \
				               "</title></head><body>" + \
				               "<applet archive='/TightVncViewer.jar' code='com.tightvnc.vncviewer.VncViewer' height='100%%' width='100%%'>" + \
				               "<param name='host' value='%(h)s'>" + \
				               "<param name='port' value='%(p)s'>" + \
				               "<param name='offer relogin' value='no'>" + \
				               "</applet>" + \
				               "</body></html>") % {'h': host, 'p': vnc.port, 'nn': node.name, 'dn': domain.name}
				id = ''.join([c for c in '%s%s' % (host, vnc.port) if c.lower() in set('abcdefghijklmnopqrstuvwxyz0123456789') ])
				javascript = "var w=window.open('','VNC%s','dependent=no,resizable=yes');if(w.document.applets.length > 0){w.focus();}else{w.document.write('%s');w.document.close();};return false;" % (id, popupwindow.replace("'", "\\'"))
				html = umcd.HTML( ('<a class="nounderline" href="#" onClick="%s"><span class="content">VNC</span></a>') % javascript )
			buttons.append( html )
			buttons.append( comma )

		return buttons[ : -1 ]

	def _drive_name( self, drive ):
		if drive == uvmmn.Disk.DEVICE_DISK:
			return _( 'hard drive' )
		else:
			return _( 'CDROM drive' )

	def uvmm_node_overview( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Node overview' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node' ) )
		if not success:
			self.finished(object.id(), res)
			return
		self.domain_wizard.reset()

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		if not node_uri:
			res.dialog[ 0 ].set_dialog( umcd.InfoBox( _( 'The physical server is not available at the moment' ) ) )
			self.finished(object.id(), res)
			return
		node = self.uvmm.get_node_info( node_uri )

		content = umcd.List( attributes = { 'width' : '100%' } )

		node_table = umcd.List( attributes = { 'width' : '100%' } )
		# node_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name } )
		# node_btn = umcd.LinkButton( node.name, actions = [ umcd.Action( node_cmd ) ] )
		if node_uri.startswith( 'xen' ):
			cpu_usage = percentage(float(node.cpu_usage) / 10.0, width=150)
		else:
			cpu_usage = umcd.HTML( '<i>%s</i>' % _( 'CPU usage not available' ) )
		mem_usage = percentage( float( node.curMem ) / node.phyMem * 100, '%s / %s' % ( MemorySize.num2str( node.curMem ), MemorySize.num2str( node.phyMem ) ), width = 150 )
		# node_table.add_row( [ _( 'Physical server' ), node_btn ] )
		node_table.add_row( [ _( 'CPU usage' ), umcd.Cell( cpu_usage, attributes = { 'width' : '100%' } ) ] )
		node_table.add_row( [ _( 'Memory usage' ), umcd.Cell( mem_usage, attributes = { 'width' : '100%' } ) ] )
		content.add_row( [ umcd.Section( _( 'Physical server' ), node_table, attributes = { 'width' : '100%' } ) ] )

		table = umcd.List()
		num_buttons = 0
		for domain in sorted( node.domains, key = operator.attrgetter( 'name' ) ):
			# ignore XEN Domain-0
			if domain.name == 'Domain-0':
				continue
			domain_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = { 'group' : object.options[ 'group' ], 'node' : node.name, 'domain' : domain.name } )
			domain_icon = 'uvmm/domain'
			if domain.state in ( 1, 2 ):
				domain_icon = 'uvmm/domain-on'
			elif domain.state in ( 3, ):
				domain_icon = 'uvmm/domain-paused'
			domain_btn = umcd.LinkButton( domain.name, tag = domain_icon, actions = [ umcd.Action( domain_cmd ) ] )
			domain_btn.set_size( umct.SIZE_SMALL )
			buttons = self._create_domain_buttons( object, node, domain, remove_failure = 'node' )
			if len( buttons ) > num_buttons:
				num_buttons = len( buttons )
			os = getattr( domain, 'annotations', {} ).get( 'os', '' )
			if len( os ) > 15:
				os = os[ : 13 ] + '...'
			table.add_row( [ domain_btn, os, percentage( float( domain.cputime[ 0 ] ) / 10, width = 80 ), umcd.Number( MemorySize.num2str( domain.maxMem ) ), buttons ] )# + buttons )

		if len( table.get_content() ):
			table.set_header( [ _( 'Instance' ), _( 'Operating System' ), _( 'CPU usage' ), _( 'Memory' ) ] )

		content.add_row( [ umcd.Cell( table, attributes = { 'colspan' : '2' } ), ] )
		self.set_content( res, content )
		self.finished(object.id(), res)

	def _dlg_domain_settings( self, object, node, domain_info ):
		content = umcd.List()

		types = []
		archs = []
		for template in node.capabilities:
			tech = '%s-%s' % ( template.domain_type, template.os_type )
			ud.debug( ud.ADMIN, ud.INFO, 'domain settings: virtualisation technology: %s' % tech )
			if not tech in VirtTechSelect.MAPPING:
				continue
			if not tech in types:
				types.append( tech )
			if not template.arch in archs:
				archs.append( template.arch )
		type_select.update_choices( types )
		arch_select.update_choices( archs )

		# if domain is not stopped ...
		if domain_info.state != 5:
			make_func = umcd.make_readonly
		else:
			make_func = umcd.make
		name = make_func( self[ 'uvmm/domain/configure' ][ 'name' ], default = handler._getattr( domain_info, 'name', '' ), attributes = { 'width' : '250' } )
		tech_default = '%s-%s' % ( handler._getattr( domain_info, 'domain_type', 'xen' ), handler._getattr( domain_info, 'os_type', 'hvm' ) )
		virt_tech = umcd.make_readonly( self[ 'uvmm/domain/configure' ][ 'type' ], default = tech_default, attributes = { 'width' : '250' } )
		arch = make_func( self[ 'uvmm/domain/configure' ][ 'arch' ], default = handler._getattr( domain_info, 'arch', 'i686' ), attributes = { 'width' : '250' } )
		os_widget = make_func( self[ 'uvmm/domain/configure' ][ 'os' ], default = getattr(domain_info, 'annotations', {}).get('os', ''), attributes = { 'width' : '250' } )
		cpus_select.max = int( node.cpus )
		cpus = make_func( self[ 'uvmm/domain/configure' ][ 'cpus' ], default = handler._getattr( domain_info, 'vcpus', '1' ), attributes = { 'width' : '250' } )
		mem = handler._getattr( domain_info, 'maxMem', '536870912' )
		memory = make_func( self[ 'uvmm/domain/configure' ][ 'memory' ], default = MemorySize.num2str( mem ), attributes = { 'width' : '250' } )
		if domain_info and domain_info.interfaces:
			iface = domain_info.interfaces[ 0 ]
			iface_mac = iface.mac_address
			iface_source = iface.source
		else:
			iface_mac = ''
			iface_source = 'eth0'
		mac = make_func( self[ 'uvmm/domain/configure' ][ 'mac' ], default = iface_mac, attributes = { 'width' : '250' } )
		interface = make_func( self[ 'uvmm/domain/configure' ][ 'interface' ], default = iface_source, attributes = { 'width' : '250' } )
		# if no bootloader is set we use the advanced kernel configuration options
		if handler._getattr( domain_info, 'bootloader', '' ):
			akc = False
		else:
			akc = True
		advkernelconf = make_func( self[ 'uvmm/domain/configure' ][ 'advkernelconf' ], default = akc )
		ram_disk = make_func( self[ 'uvmm/domain/configure' ][ 'initrd' ], default = handler._getattr( domain_info, 'initrd', '' ), attributes = { 'width' : '250' } )
		root_part = make_func( self[ 'uvmm/domain/configure' ][ 'cmdline' ], default = handler._getattr( domain_info, 'cmdline', '' ), attributes = { 'width' : '250' } )
		kernel = make_func( self[ 'uvmm/domain/configure' ][ 'kernel' ], default = handler._getattr( domain_info, 'kernel', '' ), attributes = { 'width' : '250' } )
		bootdev_default = getattr( domain_info, 'boot', [ 'cdrom', 'hd' ] )
		bd_default = []
		if bootdev_default:
			for dev in bootdev_default:
				for key, descr in BootDeviceSelect.CHOICES:
					ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: boot devices (compare): %s == %s' % ( key, dev ) )
					if key == str( dev ):
						bd_default.append( ( key, descr ) )
						break
		if domain_info.state != 5:
			boot_dev.syntax.may_change = False
		else:
			boot_dev.syntax.may_change = True
		bootdevs = umcd.MultiValue( self[ 'uvmm/domain/configure' ][ 'bootdevs' ], fields = [ boot_dev ], default = bd_default, attributes = { 'width' : '200' } )
		if domain_info.state != 5:
			bootdevs.syntax.may_change = False
		else:
			bootdevs.syntax.may_change = True
		# drive listing
		drive_sec = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		opts = copy.copy( object.options )
		if domain_info.state == 5:
			cmd = umcp.SimpleCommand( 'uvmm/drive/create', options = opts )
			drive_sec.add_row( [ umcd.LinkButton( _( 'Add new drive' ), actions = [ umcd.Action( cmd ), ] ) ] )
		disk_list = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		disk_list.set_header( [ _( 'Type' ), _( 'Image' ), _( 'Size' ), _( 'Pool' ), '' ] )
		if domain_info and domain_info.disks:
			defaults = []
			overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = copy.copy( object.options ) )
			storage_volumes = {}
			first = True
			for dev in domain_info.disks:
				remove_cmd = umcp.SimpleCommand( 'uvmm/drive/remove', options = copy.copy( object.options ) )
				remove_cmd.incomplete = True
				bootdev_cmd = umcp.SimpleCommand( 'uvmm/drive/bootdevice', options = copy.copy( object.options ) )
				remove_cmd.options[ 'disk' ] = None
				values = {}
				values[ 'type' ] = self._drive_name( dev.device )
				values[ 'image' ] = os.path.basename( dev.source )
				dir = os.path.dirname( dev.source )
				values[ 'pool' ] = dir
				for pool in node.storages:
					if pool.path == dir:
						values[ 'pool' ] = pool.name
						if not pool.name in storage_volumes:
							storage_volumes[ pool.name ] = self.uvmm.storage_pool_volumes( self.uvmm.node_name2uri( object.options[ 'node' ] ), pool.name )
						for vol in storage_volumes[ pool.name ]:
							if vol.source == dev.source:
								dev.size = vol.size
								break
						break
				if not dev.size:
					values[ 'size' ] = _( 'unknown' )
				else:
					values[ 'size' ] = MemorySize.num2str( dev.size )

				remove_cmd.options[ 'disk' ] = copy.copy( dev.source )
				remove_btn = umcd.LinkButton( _( 'Remove' ), actions = [ umcd.Action( remove_cmd ) ] )
				if domain_info.state == 5:
					if not first:
						bootdev_cmd.options[ 'disk' ] = dev.source
						bootdev_btn = umcd.LinkButton( _( 'Set as boot device' ), actions = [ umcd.Action( bootdev_cmd, options = { 'disk' : dev.source } ), umcd.Action( overview_cmd ) ] )
						buttons = [ remove_btn, bootdev_btn ]
					else:
						buttons = [ remove_btn, ]
				else:
					buttons = []

				disk_list.add_row( [ values[ 'type' ], values[ 'image' ], values[ 'size' ], values[ 'pool' ], buttons ] )
				if domain_info.os_type == 'xen':
					first = False

		drive_sec.add_row( [disk_list ] )
		vnc_bool = False
		vnc_global = True
		vnc_keymap = 'de'
		if domain_info and domain_info.graphics:
			for gfx in domain_info.graphics:
				if gfx.type == uuv_node.Graphic.TYPE_VNC:
					if gfx.autoport:
						vnc_bool = True
					elif not gfx.autoport and gfx.port > 0:
						vnc_bool = True
					else:
						vnc_bool = False
					if gfx.listen != '0.0.0.0':
						vnc_global = False
					vnc_keymap = gfx.keymap
					break

		vnc = make_func( self[ 'uvmm/domain/configure' ][ 'vnc' ], default = vnc_bool, attributes = { 'width' : '250' } )
		kblayout = make_func( self[ 'uvmm/domain/configure' ][ 'kblayout' ], default = vnc_keymap, attributes = { 'width' : '250' } )
		vnc_global = make_func( self[ 'uvmm/domain/configure' ][ 'vnc_global' ], default = vnc_global, attributes = { 'width' : '250' } )
		vnc_passwd = make_func( self[ 'uvmm/domain/configure' ][ 'vnc_passwd' ], attributes = { 'width' : '250' } )
		vnc_passwd_remove = make_func( self[ 'uvmm/domain/configure' ][ 'vnc_passwd_remove' ], attributes = { 'width' : '250' } )

		content.add_row( [ name, os_widget ] )
		content.add_row( [ arch, '' ] )
		content.add_row( [ cpus, mac ] )
		content.add_row( [ memory, interface ] )

		content2 = umcd.List()
		content2.add_row( [ virt_tech ] )
		if domain_info.os_type == 'hvm':
			content2.add_row( [ bootdevs ] )
		else:
			content2.add_row( [ advkernelconf ] )
			content2.add_row( [ kernel ] )
			content2.add_row( [ ram_disk ] )
			content2.add_row( [ root_part ] )

		content2.add_row( [ umcd.Text( '' ) ] )

		content2.add_row( [ vnc, vnc_passwd ] )
		content2.add_row( [ vnc_global, vnc_passwd_remove ] )
		content2.add_row( [ kblayout, '' ] )

		content2.add_row( [ umcd.Text( '' ) ] )

		ids = ( name.id(), os_widget.id(), virt_tech.id(), arch.id(), cpus.id(), mac.id(), memory.id(), interface.id(), ram_disk.id(), root_part.id(), kernel.id(), vnc.id(), vnc_global.id(), vnc_passwd.id(), vnc_passwd_remove.id(), kblayout.id(), bootdevs.id() )
		cfg_cmd = umcp.SimpleCommand( 'uvmm/domain/configure', options = object.options )
		overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = object.options )

		sections = umcd.List()
		if domain_info.state != 5:
			sections.add_row( [ umcd.HTML( _( '<b>The settings of a virtual instance can just be modified if it is shut off.</b>' ) ) ] )
		if not domain_info:
			sections.add_row( [ umcd.Section( _( 'Drives' ), drive_sec, hideable = False, hidden = False, name = 'drives.newdomain' ) ] )
			sections.add_row( [ umcd.Section( _( 'Settings' ), content, hideable = False, hidden = False, name = 'settings.newdomain' ) ] )
			sections.add_row( [ umcd.Section( _( 'Extended Settings' ), content2, hideable = False, hidden = False, name = 'extsettings.newdomain' ) ] )
		else:
			sections.add_row( [ umcd.Section( _( 'Drives' ), drive_sec, hideable = True, hidden = False, name = 'drives.%s' % domain_info.name ) ] )
			sections.add_row( [ umcd.Section( _( 'Settings' ), content, hideable = True, hidden = False, name = 'settings.%s' % domain_info.name ) ] )
			sections.add_row( [ umcd.Section( _( 'Extended Settings' ), content2, hideable = True, hidden = False, name = 'extsettings.%s' % domain_info.name ) ] )
		if domain_info.state == 5:
			sections.add_row( [ umcd.Cell( umcd.Button( _( 'Save' ), actions = [ umcd.Action( cfg_cmd, ids ), umcd.Action( overview_cmd ) ], default = True ), attributes = { 'align' : 'right' } ) ] )

		return sections

	def uvmm_domain_overview( self, object, finish = True ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain overview' )

		migrate = object.options.get( 'migrate' )
		if migrate == 'success':
			object.options[ 'node' ] = object.options[ 'dest' ]
		elif  migrate == 'failure':
			object.options[ 'node' ] = object.options[ 'source' ]
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return
		self.domain_wizard.reset()

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		# node = self.uvmm.get_node_info( node_uri )
		node, domain_info = self.uvmm.get_domain_info_ext( node_uri, object.options[ 'domain' ] )

		blind_table = umcd.List()

		if not domain_info:
			resync_cmd = umcd.Action( umcp.SimpleCommand( 'uvmm/daemon/restart', options = copy.copy( object.options ) ) )
			overview_cmd = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = copy.copy( object.options ) ) )
			resync = umcd.LinkButton( _( 'Resynchronize' ), actions = [ resync_cmd, overview_cmd ] )
			blind_table.add_row( [ _( 'The information about the virtual instance could not be retrieved. Clicking the refresh button will retry to collect the information. If this does not work a resynchronization can be triggered by clicking the following button.' ) ] )
			blind_table.add_row( [ umcd.Cell( resync, attributes = { 'align' : 'right' } ) ] )
		else:
			infos = umcd.List()
			infos.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Status' ) ), handler.STATES[ domain_info.state ] ] )
			infos.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Operating System' ) ), getattr(domain_info, 'annotations', {}).get('os', '' ) ] )

			stats = umcd.List()
			if domain_info.maxMem:
				pct = int( float( domain_info.curMem ) / domain_info.maxMem * 100 )
			else:
				pct = 0
			mem_usage = percentage( pct, label = '%s / %s' % ( MemorySize.num2str( domain_info.curMem ), MemorySize.num2str( domain_info.maxMem ) ), width = 130 )
			cpu_usage = percentage( float( domain_info.cputime[ 0 ] ) / 10, width = 130 )
			stats.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'Memory usage' ) ), mem_usage ] )
			stats.add_row( [ umcd.HTML( '<b>%s</b>' % _( 'CPU usage' ) ), cpu_usage ] )

			ops = umcd.List()
			buttons = self._create_domain_buttons( object, node, domain_info, overview = 'domain', operations = True )
			ops.add_row( buttons )

			tab = umcd.List()
			tab.add_row( [ infos, stats ] )

			tech = '%s-%s' % ( domain_info.domain_type, domain_info.os_type )
			blind_table.add_row( [ umcd.Section( _( 'Virtual instance %(domain)s - <i>%(tech)s</i>' ) % { 'domain' : domain_info.name, 'tech' : VirtTechSelect.MAPPING[ tech ] }, tab ) ] )
			blind_table.add_row( [ umcd.Cell( umcd.Section( _( 'Operations' ), ops ) ) ] )

			content = self._dlg_domain_settings( object, node, domain_info )
			blind_table.add_row( [ content ] )

		self.set_content( res, blind_table )
		if finish:
			self.finished(object.id(), res)
		return res

	def uvmm_domain_migrate( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain migrate' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'source', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		content = umcd.List()
		if 'dest' in object.options:
			src_uri = self.uvmm.node_name2uri( object.options[ 'source' ] )
			dest_uri = self.uvmm.node_name2uri( object.options[ 'dest' ] )
			domain_info = self.uvmm.get_domain_info( src_uri, object.options[ 'domain' ] )
			ud.debug( ud.ADMIN, ud.INFO, 'Domain migrate: %s, %s, %s' % ( src_uri, dest_uri, domain_info ) )
			resp = self.uvmm.domain_migrate( src_uri, dest_uri, domain_info.uuid )
		else:
			domains = self.uvmm.get_group_info( object.options[ 'group' ] )
			dest_node_select.update_choices( [ domain.name for domain in domains ], object.options[ 'source' ] )
			content.set_header( [ umcd.Text( _( 'Migrate %(domain)s from %(source)s to:' ) % object.options ) ] )
			dest = umcd.make( self[ 'uvmm/domain/migrate' ][ 'dest' ] )
			content.add_row( [ dest, '' ] )
			opts = copy.copy( object.options )
			opts[ 'migrate' ] = 'success'
			cmd_success = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = opts ), [ dest.id(), ], status_range = umcd.Action.SUCCESS )
			opts2 = copy.copy( object.options )
			opts2[ 'migrate' ] = 'failure'
			cmd_failure = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = opts2 ), status_range = umcd.Action.FAILURE )

			content.add_row( [ '', umcd.Button( _( 'Migrate' ), actions = [ umcd.Action( umcp.SimpleCommand( 'uvmm/domain/migrate', options = object.options ), [ dest.id() ] ), cmd_success, cmd_failure ], default = True ) ] )
			res.dialog[ 0 ].set_dialog( content )
			resp = None

		if resp and self.uvmm.is_error( resp ):
			res.status( 301 )
			ud.debug( ud.ADMIN, ud.INFO, 'Domain migrate: error: %s' % str( resp.msg ) )
			self.finished( object.id(), res, report = str( resp.msg ) )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_configure( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		# node = self.uvmm.get_node_info( node_uri )
		node, domain_info = self.uvmm.get_domain_info_ext( node_uri, object.options[ 'domain' ] )

		domain = uuv_proto.Data_Domain()
		if domain_info:
			domain.uuid = domain_info.uuid
		domain.name = object.options[ 'name' ]
		domain.domain_type, domain.os_type = object.options[ 'type' ].split( '-' )
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: operating system: %s' % handler._getstr( object, 'os' ) )
		domain.annotations['os'] = handler._getstr( object, 'os' )
		domain.arch = object.options[ 'arch' ]
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: architecture: %s' % domain.arch )
		domain.vcpus = int( object.options[ 'cpus' ] )
		# if para-virtualized machine ...
		if domain.os_type == 'xen':
			if object.options.get( 'advkernelconf', False ):
				domain.kernel = handler._getstr( object, 'kernel' )
				domain.cmdline = handler._getstr( object, 'cmdline' )
				domain.initrd = handler._getstr( object, 'initrd' )
			else:
				domain.bootloader = '/usr/bin/pygrub'
				domain.bootloader_args = '-q' # Bug #19249: PyGrub timeout
		domain.boot = handler._getstr( object, 'bootdevs' )
		domain.maxMem = MemorySize.str2num( object.options[ 'memory' ] )

		# interface
		iface = uuv_node.Interface()
		iface.mac_address = handler._getstr( object, 'mac' )
		iface.source = handler._getstr( object, 'interface' )
		domain.interfaces.append( iface )

		# disks
		if domain_info:
			domain.disks = domain_info.disks

		# graphics
		ud.debug( ud.ADMIN, ud.INFO, 'Configure Domain: graphics: %s' % object.options[ 'vnc' ] )
		if object.options[ 'vnc' ]:
			gfx = uuv_node.Graphic()
			gfx.keymap = object.options[ 'kblayout' ]
			if object.options[ 'vnc_passwd' ]:
				gfx.passwd = object.options[ 'vnc_passwd' ]
			elif object.options[ 'vnc_passwd_remove' ]:
				gfx.passwd = None
			else:
				gfx.passwd = domain_info.graphics[ 0 ].passwd
			if object.options[ 'vnc_global' ]:
				gfx.listen = '0.0.0.0'
			domain.graphics.append( gfx )
			ud.debug( ud.ADMIN, ud.INFO, 'Configure Domain: graphics: %s' % str( gfx ) )

		resp = self.uvmm.domain_configure( object.options[ 'node' ], domain )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = resp.msg )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_state( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain State' )
		res = umcp.Response( object )

		ud.debug( ud.ADMIN, ud.INFO, 'Domain State: change to %s' % object.options[ 'state' ] )
		resp = self.uvmm.domain_set_state( object.options[ 'node' ], object.options[ 'domain' ], object.options[ 'state' ] )
		ud.debug( ud.ADMIN, ud.INFO, 'Domain State: changed to %s' % object.options[ 'state' ] )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = str( resp.msg ) )
		else:
			self.finished( object.id(), res )

	def uvmm_domain_create( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive create' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		# user cancelled the wizard
		if object.options.get( 'action' ) == 'cancel':
			self.drive_wizard.reset()
			self.uvmm_node_overview( object )
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )

		if not 'action' in object.options:
			self.domain_wizard.max_memory = node.phyMem
			self.domain_wizard.archs = set([t.arch for t in node.capabilities])
			self.domain_wizard.reset()

		result = self.domain_wizard.action( object, ( node_uri, node ) )

		# domain wizard finished?
		if self.domain_wizard.result():
			resp = self.uvmm.domain_configure( object.options[ 'node' ], self.domain_wizard.result() )
			object.options[ 'domain' ] = object.options[ 'name' ]
			if self.uvmm.is_error( resp ):
				# FIXME: something went wrong. We have to erase als 'critical' data and restart with the drive wizard part
				self.domain_wizard._result = None
				self.domain_wizard.current = 1
				self.domain_wizard.drives = []
				self.domain_wizard.action( object, ( node_uri, node ) )
				page = self.domain_wizard.setup( object )
				res.dialog[ 0 ].set_dialog( page )
				res.status( 301 )
				self.finished( object.id(), res, report = resp.msg )
			else:
				self.uvmm_domain_overview( object )
			return
		else:
			page = self.domain_wizard.setup( object )
			ud.debug( ud.ADMIN, ud.INFO, 'Domain create: dialog: %s' % str( page ) )
			res.dialog[ 0 ].set_dialog( page )

		if not result:
			res.status( 201 )
			report = result.text
		else:
			report = ''
		self.finished( object.id(), res, report = report )

	def uvmm_domain_remove_images( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain remove images' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		# node = self.uvmm.get_node_info( node_uri )
		node, domain_info = self.uvmm.get_domain_info_ext( node_uri, object.options[ 'domain' ] )

		boxes = []
		lst = umcd.List()

		lst.add_row( [ umcd.Cell( umcd.Text( _( 'When removing a virtual instance the disk images bind to it may be removed also. Please select the disks that should be remove with the virtual instance. Be sure that none of the images to be delete are used by any other instance.' ) ), attributes = { 'colspan' : '3' } ) ] )
		lst.add_row( [ '' ] )
		if domain_info.disks:
			defaults = []
			for disk in domain_info.disks:
				if not disk.source: continue
				static_options = { 'drives' : disk.source }
				chk_button = umcd.Checkbox( static_options = static_options )
				chk_button.set_text( '%s: %s' % ( self._drive_name( disk.device ), disk.source ) )
				boxes.append( chk_button.id() )
				lst.add_row( [ umcd.Cell( umcd.Text( '' ), attributes = { 'width' : '10' } ), umcd.Cell( chk_button, attributes = { 'colspan' : '2' } ) ] )

			opts = copy.copy( object.options )
			opts[ 'drives' ] = []
			back = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			req = umcp.SimpleCommand( 'uvmm/domain/remove', options = opts )
			fail_overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			opts2 = copy.copy( object.options )
			del opts2[ 'domain' ]
			success_overview_cmd = umcp.SimpleCommand( 'uvmm/node/overview', options = opts2 )
			cancel = umcd.Button( _( 'Cancel' ), actions = [ umcd.Action( back ) ] )
			button = umcd.Button( _( 'Remove' ), actions = [ umcd.Action( req, boxes ), umcd.Action( success_overview_cmd, status_range = umcd.Action.SUCCESS ), umcd.Action( fail_overview_cmd, status_range = umcd.Action.FAILURE ) ], default = True )
			lst.add_row( [ '' ] )
			lst.add_row( [ umcd.Cell( cancel, attributes = { 'align' : 'right', 'colspan' : '2' } ), umcd.Cell( button, attributes = { 'align' : 'right' } ) ] )

		res.dialog[ 0 ].set_dialog( umcd.Section( _( 'Remove the virtual instance %(instance)s?' ) % { 'instance' : domain_info.name }, lst, hideable = False ) )
		self.finished(object.id(), res)

	def uvmm_domain_remove( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain remove' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		# shutdown machine before removing it
		self.uvmm.domain_set_state( object.options[ 'node' ], object.options[ 'domain' ], 'SHUTDOWN' )

		# remove domain
		resp = self.uvmm.domain_undefine( node_uri, domain_info.uuid, object.options[ 'drives' ] )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Removing the instance <i>%(domain)s</i> failed' ) % { 'domain' : object.options[ 'domain' ] } )
		else:
			res.status( 201 )
			self.finished( object.id(), res, report = _( 'The instance <i>%(domain)s</i> was removed successfully' ) % { 'domain' : object.options[ 'domain' ] } )

	def uvmm_domain_save( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain save' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		# save machine
		resp = self.uvmm.domain_save( object.options[ 'node' ], domain_info )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Saving the instance <i>%(domain)s</i> failed' ) % { 'domain' : object.options[ 'domain' ] } )
		else:
			res.status( 201 )
			self.finished( object.id(), res, report = _( 'The instance <i>%(domain)s</i> was saved successfully' ) % { 'domain' : object.options[ 'domain' ] } )

	def uvmm_domain_restore( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain restore' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )

		# save machine
		resp = self.uvmm.domain_restore( object.options[ 'node' ], domain_info )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Restoring the instance <i>%(domain)s</i> failed' ) % { 'domain' : object.options[ 'domain' ] } )

	def uvmm_drive_create( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive create' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return
		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		node = self.uvmm.get_node_info( node_uri )

		ud.debug( ud.ADMIN, ud.INFO, 'Drive create: action: %s' % str( object.options.get( 'action' ) ) )
		# user cancelled the wizard
		if object.options.get( 'action' ) == 'cancel':
			self.drive_wizard.reset()
			del object.options[ 'action' ]
			self.uvmm_domain_overview( object )
			return

		# starting the wizard
		if not 'action' in object.options:
			self.uvmm.next_drive_name( node_uri, object.options[ 'domain' ], object )
			ud.debug( ud.ADMIN, ud.ERROR, 'Drive create: suggestion for drive name: %s' % str( object.options.get( 'drive-image' ) ) )

		result = self.drive_wizard.action( object, ( node_uri, node ) )

		# domain wizard finished?
		if self.drive_wizard.result():
			new_disk = self.drive_wizard.result()
			domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
			domain_info.disks.append( new_disk )
			resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )
			new_disk = self.drive_wizard.reset()
			if self.uvmm.is_error( resp ):
				res = self.uvmm_domain_overview( object, finish = False )
				res.status( 301 )
				self.finished( object.id(), res, report = resp.msg )
			else:
				self.uvmm_domain_overview( object )
			return
		# navigating in the wizard ...
		page = self.drive_wizard.setup( object )
		res.dialog[ 0 ].set_dialog( page )
		if not result:
			res.status( 201 )
			report = result.text
		else:
			report = ''
		self.finished( object.id(), res, report = report )

	def uvmm_drive_remove( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive remove' )
		res = umcp.Response( object )

		if object.incomplete:
			ud.debug( ud.ADMIN, ud.INFO, 'drive remove' )
			( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
			if not success:
				self.finished(object.id(), res)
				return
			# remove domain
			# if the attached drive could be removed successfully the user should be ask, if the image should be removed
			node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
			node = self.uvmm.get_node_info( node_uri )
			lst = umcd.List()

			lst.add_row( [ umcd.Cell( umcd.Text( _( 'The drive will be detached from the virtual instance. Additionally the associated image %(image)s may be deleted permanently. Should this be done also?' ) % { 'image' : object.options[ 'disk' ] } ), attributes = { 'colspan' : '3' } ) ] )
			opts = copy.copy( object.options )
			overview = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = True
			remove = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = False
			detach = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )
			no = umcd.Button( _( 'No' ), actions = [ umcd.Action( detach ), umcd.Action( overview ) ] )
			yes = umcd.Button( _( 'Yes' ), actions = [ umcd.Action( remove ), umcd.Action( overview ) ], default = True )
			lst.add_row( [ '' ] )
			lst.add_row( [ umcd.Cell( no, attributes = { 'align' : 'right', 'colspan' : '2' } ), umcd.Cell( yes, attributes = { 'align' : 'right' } ) ] )
			res.dialog[ 0 ].set_dialog( lst )
			self.finished(object.id(), res)
		else:
			node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
			domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
			new_disks = []
			for dev in domain_info.disks:
				if dev.source != object.options[ 'disk' ]:
					new_disks.append( dev )
			domain_info.disks = new_disks
			resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )

			if self.uvmm.is_error( resp ):
				res.status( 301 )
				self.finished( object.id(), res, report = _( 'Detaching the drive <i>%(drive)s</i> failed' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )
				return

			if object.options.get( 'drive-remove', False ):
				resp = self.uvmm.storage_volumes_destroy( node_uri, [ object.options[ 'disk' ], ] )

				if not resp:
					res.status( 301 )
					self.finished( object.id(), res, report = _( 'Removing the image <i>%(disk)s</i> failed. It must be removed manually.' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )
					return
				res.status( 201 )
				self.finished( object.id(), res, report = _( 'The drive <i>%(drive)s</i> was detached and removed successfully' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )
			res.status( 201 )
			self.finished( object.id(), res, report = _( 'The drive <i>%(drive)s</i> was detached successfully' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )

	def uvmm_drive_bootdevice( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive boot device' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
		new_disks = []
		for dev in domain_info.disks:
			if dev.source != object.options[ 'disk' ]:
				new_disks.append( dev )
			else:
				new_disks.insert( 0, dev )
		domain_info.disks = new_disks
		resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Setting the drive <i>%(drive)s</i> as boot device as failed' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )
		else:
			self.finished( object.id(), res )

	def uvmm_daemon_restart( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive boot device' )
		res = umcp.Response( object )

		child = notifier.popen.run( '/usr/sbin/invoke-rc.d univention-virtual-machine-manager-node-common restart', timeout = 10000, stdout = False, stderr = False, shell = False )
		if child.exitcode == None: # failed to restart libvirt
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Resynchronisation has failed!' ) )
			return

		time.sleep( 5 )
		self.finished( object.id(), res )
