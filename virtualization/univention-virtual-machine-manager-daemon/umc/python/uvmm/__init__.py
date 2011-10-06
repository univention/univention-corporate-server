#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2011 Univention GmbH
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
import re
import socket
import time

import notifier.popen

import uvmmd
from treeview import TreeView
from tools import *
from types import *
from wizards import *
from nic import *
from drive import *

configRegistry = ucr.ConfigRegistry()
configRegistry.load()
try:
	TreeView.SHOW_LEVEL = int(configRegistry.get('uvmm/umc/show/treeview'))
except Exception:
	pass

_ = umc.Translation('univention.management.console.handlers.uvmm').translate
_uvmm_locale = umc.Translation('univention.virtual.machine.manager').translate

name = 'uvmm'
icon = 'uvmm/module'
short_description = _('Virtual Machines (UVMM)')
long_description = _('Univention Virtual Machine Manager')
categories = [ 'system', 'all' ]
hide_tabs = True

# fields of a drive definition
# drive_type = umcd.make( ( 'type', DriveTypeSelect( _( 'Type' ) ) ), attributes = { 'width' : '250' } )
# drive_uri = umcd.make( ( 'uri', umc.String( 'URI' ) ), attributes = { 'width' : '250' } )
# drive_dev = umcd.make( ( 'dev', umc.String( _( 'Drive' ) ) ), attributes = { 'width' : '250' } )

boot_dev_select = BootDeviceSelect()
boot_dev = umcd.make( ( 'bootdev', boot_dev_select ), attributes = { 'width' : '200' } )

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
	'uvmm/search': umch.command(
		short_description = _( 'Search' ),
		long_description = _( 'Search' ),
		method = 'uvmm_search',
		values = {
			'pattern' : umc.String( _( 'Filter' ) ),
			'option' : SearchOptions( _( 'Search in' ) )
			},
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
		values = { 'domain' : umc.String( 'instance' ), # last uuid, which was used to load the configuration
				   'name' : umc.String( _( 'Name' ) ), # new name
				   'memory' : umc.String( _( 'Memory' ), regex = MemorySize.SIZE_REGEX ),
				   'cpus' : cpus_select,
				   'vnc' : umc.Boolean( _( 'Direct access' ) ),
				   'vnc_global' : umc.Boolean( _( 'Globally available' ) ),
				   'vnc_passwd' : umc.Password( _( 'Password' ), required = False ),
				   'kblayout' : KBLayoutSelect( _( 'Keyboard layout' ) ),
				   'arch' : arch_select,
				   'type' : type_select,
				   'drives' : umc.StringList( _( 'Drive' ) ),
				   'os' : umc.String( _( 'Operating System' ), required = False ),
				   'description' : umc.String( _( 'Description' ), required = False ),
				   'contact' : umc.String( _( 'Contact' ), required = False ),
				   'user' : umc.String( _( 'User' ), required = False ),
				   'advkernelconf' : umc.Boolean( _( 'Advanved kernel configuration' ), required = False ),
				   'initrd' : umc.String( _( 'RAM disk' ), required = False ),
				   'cmdline' : umc.String( _( 'Kernel parameter' ), required = False ),
				   'kernel' : umc.String( _( 'Kernel' ), required = False ),
				   'bootdevs' : umc.StringList( _( 'Boot order' ), required = False ),
				   'rtc_offset': RtcOffsetSelect(_('RTC reference'), required=False),
				   },
		),
	'uvmm/domain/migrate': umch.command(
		short_description = _( 'Migration of virtual instances' ),
		long_description = _( 'Migration of virtual instances' ),
		method = 'uvmm_domain_migrate',
		values = { 'domain' : umc.String( _( 'domain' ) ),
				   'node' : umc.String( 'source node' ),
				   'dest' : dest_node_select,
				  },
		),
	'uvmm/domain/snapshot/create': umch.command(
		short_description=_('Save virtual instance'),
		long_description=_('Saves the state of a virtual instance'),
		method='uvmm_domain_snapshot_create',
		values={
			'node': umc.String('node'),
			'domain': umc.String('domain'),
			'snapshot': umc.String(_('snapshot name')),
			},
		),
	'uvmm/domain/snapshot/revert': umch.command(
		short_description=_('Restore virtual instance'),
		long_description=_('Restore the state of a virtual instance'),
		method='uvmm_domain_snapshot_revert',
		confirm=umch.Confirm(_('Revert to snapshot'), _('Are you sure that the instance should be reverted to this snapshot?')),
		values={
			'node': umc.String('node'),
			'domain': umc.String('domain'),
			'snapshot': umc.String(_('snapshot name')),
			},
		),
	'uvmm/domain/snapshot/delete': umch.command(
		short_description=_('Delete snapshot'),
		long_description=_('Delete the state of a virtual instance'),
		method='uvmm_domain_snapshot_delete',
		confirm=umch.Confirm(_('Remove snapshot'), _('Are you sure that the snapshot should be removed?')),
		values={
			'node': umc.String('node'),
			'domain': umc.String('domain'),
			'snapshot': umc.String(_('snapshot name')),
			},
		),
	'uvmm/domain/snapshots/delete': umch.command(
		short_description=_('Delete selected snapshots'),
		long_description=_('Delete list of states of a virtual instance'),
		method='uvmm_domain_snapshot_delete',
		confirm=umch.Confirm(_('Remove snapshots'), _('Are you sure that the selected snapshots should be deleted?')),
		values={
			'node': umc.String('node'),
			'domain': umc.String('domain'),
			'snapshot': umc.String(_('snapshot name')),
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
	'uvmm/domain/stop': umch.command(
		short_description = _( 'Stop a virtual instance' ),
		long_description = _('Stop a virtual instance' ),
		method = 'uvmm_domain_state',
		confirm = umch.Confirm( _( 'Stop' ), _( 'Stopping the virtual instance will turn it off without shutting down the operating system. Should the virtual instance be stopped?' ) ),
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
	'uvmm/drive/edit': umch.command(
		short_description = _( 'Edit drive settings' ),
		long_description = _('Edit drive' ),
		method = 'uvmm_drive_edit',
		values = {},
		),
	'uvmm/drive/bootdevice': umch.command(
		short_description = _( 'Set drive as boot device' ),
		long_description = _('Set drive as boot device' ),
		method = 'uvmm_drive_bootdevice',
		values = {},
		),
	'uvmm/drive/media/change': umch.command(
		short_description=_('Change media from device'),
		long_description=_('Eject or change media from device'),
		method='uvmm_drive_media_change',
		values={
			'node': umc.String('node'),
			'domain': umc.String('domain'),
			'target_dev': umc.String(''), # uniquely identifies drive
			'source': umc.String(_('Media image')),
			},
		),
	'uvmm/nic/create': umch.command(
		short_description = _( 'New network interface' ),
		long_description = _('Create a new network interface' ),
		method = 'uvmm_nic_create',
		values = {
			'nictype' : umc.String( '' ),
			'driver' : nic_driver_select,
			'source' : umc.String( _( 'Source' ) ),
			'mac' : umc.String( _( 'MAC address' ), required = False ),
			},
		),
	'uvmm/nic/edit': umch.command(
		short_description = _( 'Edit network interface' ),
		long_description = _('Edit a network interface' ),
		method = 'uvmm_nic_edit',
		values = {
			'nictype' : umc.String( '' ),
			'driver' : nic_driver_select,
			'source' : umc.String( _( 'Source' ) ),
			'mac' : umc.String( _( 'MAC address' ), required = False ),
			},
		),
	'uvmm/nic/remove': umch.command(
		short_description = _( 'Remove network interface' ),
		long_description = _('Remove a network interface' ),
		method = 'uvmm_nic_remove',
		values = {},
		confirm = umch.Confirm( _( 'Remove network interface' ), _( 'Should the network interface be removed?')),
		),
	'uvmm/daemon/restart': umch.command(
		short_description = _( 'Restarts libvirt service' ),
		long_description = _( 'Restarts libvirt service' ),
		method = 'uvmm_daemon_restart',
		values = {},
		),
}

class handler( umch.simpleHandler, DriveCommands, NIC_Commands ):
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

	MAIL_REGEX = re.compile( '(^|(?P<name>.*?)[ \t]+)<?(?P<address>[^ @]*@[^ >]*).*' )

	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.drive_wizard = DriveWizard('uvmm/drive/create')
		self.media_wizard = DriveWizard('uvmm/drive/media/change', True)
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

	def set_content( self, object, content, location = True, refresh = True, search = True ):
		"""Set content, add position links, add refresh link, add search link."""
		def get_path_item(key):
			# FIXME: should be removed if UVMMd supports groups
			if key == 'group' and object.options[key] == 'default':
				return _( 'Physical servers' )
			elif key == 'node':
				node_uri = object.options[key]
				return uvmmd.Client._uri2name(node_uri, short=True)
			elif key == 'domain':
				return object.options.get('domain_name') or object.options[key]
			return object.options[key]

		lst = umcd.List( attributes = { 'width' : '100%', 'type' : 'umc_mini_padding umc_nowrap' }, default_type = 'uvmm_table' )
		row = []
		if location:
			options = {}
			keys = []
			refresh = ''
			slash = umcd.Cell( umcd.HTML( '&rarr;' ), attributes = { 'type' : 'umc_nowrap' } )
			row.append( umcd.Cell( umcd.HTML( '<b>%s</b>' % _( 'Location:' ) ), attributes = { 'type' : 'umc_nowrap' } ) )
			if 'group' in object.options:
				keys.append( 'group' )
				if 'node' in object.options:
					keys.append( 'node' )
					if 'domain' in object.options and object.options[ 'domain' ] != 'NONE':
						keys.append( 'domain' )
			opts = {}
			for key in keys[ : -1 ]:
				opts[ key ] = object.options[ key ]
				cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % key , options = copy.copy( opts ) )
				lnk = umcd.LinkButton(get_path_item(key), actions=[umcd.Action(cmd)])
				row.append( umcd.Cell( lnk, attributes = { 'type' : 'umc_nowrap' } ) )
				row.append( slash )
			refresh = keys[ -1 ]
			opts[ keys[ -1 ] ] = object.options[ keys[ -1 ] ]
			row.append(umcd.Cell(umcd.Text(get_path_item(refresh)), attributes={'type': 'umc_nowrap', 'width': '100%'}))
		else:
			row.append( umcd.Cell( umcd.Text( '' ), attributes = { 'type' : 'umc_nowrap', 'width' : '100%' } ) )

		buttons = None
		if refresh or search:
			buttons = umcd.List( attributes = { 'type' : 'uvmm_frame', 'align' : 'left' }, default_type = 'uvmm_frame' )

		if refresh:
			reload_cmd = umcp.SimpleCommand( 'uvmm/%s/overview' % refresh, options = copy.copy( opts ) )
			reload_btn = umcd.LinkButton( _( 'Refresh' ), 'actions/refresh', actions = [ umcd.Action( reload_cmd ) ] )
			reload_btn.set_size( umct.SIZE_SMALL )
			buttons.add_row( [ umcd.Cell( reload_btn, attributes = { 'type' : 'uvmm_frame', 'align' : 'left' } ), ] )
		if search:
			search_cmd = umcp.SimpleCommand( 'uvmm/search', options = copy.copy( object.options ) )
			search_cmd.incomplete = True
			search_btn = umcd.LinkButton( _( 'Search' ), 'uvmm/search', actions = [ umcd.Action( search_cmd ) ] )
			search_btn.set_size( umct.SIZE_SMALL )
			buttons.add_row( [ umcd.Cell( search_btn, attributes = { 'type' : 'uvmm_frame', 'align' : 'left' } ), ] )
			# buttons.append( search_btn )

		if buttons:
			row.append( umcd.Cell( buttons, attributes = { 'width' : '100%', 'align' : 'right', 'type' : 'umc_mini_padding' } ) )

		if location or refresh or search:
			lst.add_row( row, attributes = { 'type' : 'umc_mini_padding' } )
		object.dialog[ 0 ].set_dialog( umcd.List( content = [ [ lst, ], [ content, ] ], default_type = 'uvmm_table' ) )

	def uvmm_overview( self, object ):
		"""Toplevel overview: show info."""
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_ROOT)
		except uvmmd.UvmmError, e:
			res = tv.get_failure_response(e)
		else:
			self.domain_wizard.reset()
			self.set_content( res, umcd.ModuleDescription( 'Univention Virtual Machine Manager (UVMM)', _( 'This module provides a management interface for physical servers that are registered within the UCS domain.\nThe tree view on the left side shows an overview of all existing physical servers and the residing virtual instances. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual instance can be invoked on each of the instances.\nAlso possible is direct access to virtual instances. Therefor it must be activated in the configuration.\nEach virtual instance entry in the tree view provides access to detailed information und gives the possibility to change the configuration or state and migrated it to another physical server.' ) ), location = False, refresh = False )
		self.finished( object.id(), res )

	def uvmm_search( self, object ):
		'''performs a search for physical servers, virtual instances etc.'''
		def _widget( key, default = True ):
			return umcd.make( self[ 'uvmm/search' ][ key ], default = object.options.get( key, default ) )

		ud.debug( ud.ADMIN, ud.INFO, 'Search' )
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_ROOT)
		except uvmmd.UvmmError, e:
			res = tv.get_failure_response(e)
			self.finished(object.id(), res)
			return
		pattern = _widget( 'pattern', '*' )
		option = umcd.make( self[ 'uvmm/search' ][ 'option' ], default = object.options.get( 'option', 'all' ), attributes = { 'width' : '250px' } )

		fields = [ [ ( option, 'all' ), ],
				   [ ( pattern, '*' ) ], ]
		form = umcd.SearchForm( 'uvmm/search', fields )

		if object.incomplete:
			self.set_content( res, [ form ], location = False, refresh = False, search = False )
			self.finished( object.id(), res )
			return

		blind = umcd.List( default_type = 'uvmm_table' )
		blind.add_row( [ form ] )
		try:
			results = self.uvmm.search( object.options[ 'pattern' ], object.options[ 'option' ] )
		except uvmmd.UvmmError, e:
			results = ()
		result_list = umcd.List()
		result_list.set_header([
			umcd.Cell(umcd.Text(''), attributes={'width': '20px'}),
			umcd.HTML(_('Instance'), attributes={'width': '100%', 'type': 'umc_nowrap'}),
			umcd.HTML(_('CPU usage'), attributes={'type': 'umc_nowrap', 'align': 'right'}),
			umcd.HTML(_('Memory') , attributes={'type': 'umc_nowrap', 'align': 'right'}),
			''
			])

		group_name = 'default' # FIXME
		results.sort(key=lambda (node_info, domain_infos): node_info.name.lower())
		for node_info, domain_infos in results:
			node_is_off = node_info.last_update < node_info.last_try
			node_btn = TreeView.button_create_node(group_name, node_info.uri, node_is_off)
			result_list.add_row( [ umcd.Cell( node_btn, attributes = { 'colspan' : '5' } ) ] )

			domain_infos.sort(key=lambda domain_info: domain_info.name.lower())
			for domain_info in domain_infos:
				domain_btn = TreeView.button_create_domain(group_name, node_info.uri, node_is_off, domain_info)
				domain_opts = {'group': group_name, 'node': node_info.uri, 'domain': domain_info.uuid}
				buttons = self._create_domain_buttons( domain_opts, node_info, domain_info, remove_failure = 'node' )
				try:
					cpu_usage = percentage(float(domain_info.cputime[0]) / 10, width=80)
				except (ArithmeticError, ValueError, TypeError), e:
					cpu_usage = umcd.HTML('<i>%s</i>' % _('not available'))
				try:
					mem_usage = umcd.Number(MemorySize.num2str(domain_info.maxMem))
				except (ArithmeticError, ValueError, TypeError), e:
					mem_usage = umcd.HTML('<i>%s</i>' % _('not available'))
				result_list.add_row([
					'',
					domain_btn,
					umcd.Cell(cpu_usage, attributes={'type': 'umc_mini_padding', 'align': 'center'}),
					umcd.Cell(mem_usage, attributes={'type': 'umc_mini_padding umc_nowrap', 'align': 'right'}),
					umcd.Cell(buttons, attributes={'type': 'umc_mini_padding umc_nowrap'})
					])

		# blind.add_row( [ umcd.Frame( [ result_list ], _( 'Search results' ) ) ] )
		blind.add_row( [ umcd.Section( _( 'Search results' ), result_list ) ] )

		self.set_content( res, blind, location = False, refresh = False, search = False )
		self.finished( object.id(), res )

	def uvmm_group_overview( self, object ):
		"""Group overview: show nodes of group with utilization."""
		group_name = object.options['group']
		ud.debug(ud.ADMIN, ud.INFO, 'Group overview of %s' % (group_name,))
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_GROUP)
			nodes = tv.node_tree[group_name]
		except (uvmmd.UvmmError, KeyError), e:
			res = tv.get_failure_response(e)
			self.finished(object.id(), res)
			return
		self.domain_wizard.reset()

		table = umcd.List( default_type = 'uvmm_table')
		table.set_header( [ _( 'Physical server' ), _( 'CPU usage' ), _( 'Memory usage' ) ] )
		for node_uri, node_info in sorted(nodes.items(), key=lambda (k, v): v.name):
			node_opt = {'group': group_name, 'node': node_uri}
			node_cmd = umcp.SimpleCommand('uvmm/node/overview', options=node_opt)
			node_btn = umcd.LinkButton( node_info.name, actions = [ umcd.Action( node_cmd ) ] )

			if node_info.last_update < node_info.last_try:
				info_txt = umcd.InfoBox(_('The physical server is not available at the moment'), columns=2, icon='actions/critical', size=umct.SIZE_SMALL)
				table.add_row([node_btn, info_txt])
			else:
				if node_uri.startswith( 'xen' ):
					try:
						cpu_usage = percentage(float(node_info.cpu_usage) / 10.0, width=150)
					except (ArithmeticError, ValueError, TypeError), e:
						cpu_usage = umcd.HTML('<i>%s</i>' % _('not available'))
				else:
					cpu_usage = umcd.HTML( '<i>%s</i>' % _( 'not available' ) )
				try:
					mem_usage = percentage(float(node_info.curMem) / node_info.phyMem * 100, '%s / %s' % (MemorySize.num2str(node_info.curMem), MemorySize.num2str(node_info.phyMem)), width=150)
				except (ArithmeticError, ValueError, TypeError), e:
					mem_usage = umcd.HTML('<i>%s</i>' % _('not available'))
				table.add_row( [ node_btn, cpu_usage, mem_usage ] )
		self.set_content( res, table )
		self.finished(object.id(), res)

	def _create_domain_snapshots( self, object, node_info, domain_info ):
		"""Create snapshot settings."""
		if not ( configRegistry.is_true( 'uvmm/umc/show/snapshot', True ) and hasattr( domain_info, 'snapshots' ) and isinstance( domain_info.snapshots, dict ) ):
			return None

		overview_cmd = umcp.SimpleCommand( 'uvmm/domain/overview', options = object.options )
		opts = copy.deepcopy( object.options )

		table = umcd.List( default_type = 'uvmm_table' )

		# button: create new snapshot
		if getattr(domain_info, 'suspended', None):
			table.add_row([umcd.InfoBox(_('Snapshots can not be created for suspended domains.'))])
		else:
			opts = copy.copy( object.options )
			create_cmd = umcp.SimpleCommand( 'uvmm/domain/snapshot/create', options = opts )
			create_cmd.incomplete = True
			create_act = [umcd.Action(create_cmd),]#
			btn = umcd.LinkButton( _( 'Create new snapshot' ), 'uvmm/add', actions = create_act )
			btn.set_size( umct.SIZE_SMALL )
			table.add_row( [ btn  ] )

		# listing of existing snapshots
		lst = umcd.List( default_type = 'uvmm_table' )
		btntoggle = umcd.ToggleCheckboxes()

		# no snapshots available
		if not domain_info.snapshots:
			lst.add_row( [ _( 'There are no snapshots available' ) ] )
			table.add_row( [ lst ] )
			return table

		lst.set_header( [ btntoggle, _( 'Name' ), _( 'Date' ), '' ] )

		# show list of snapshots
		f = lambda s: s[ 1 ].ctime
		idlist = []
		for snapshot_name, snap in sorted( domain_info.snapshots.items(), key=f, reverse = True ):
			ctime = time.strftime( "%Y-%m-%d %H:%M:%S", time.localtime( snap.ctime ) )
			name = '%s (%s)' % ( snapshot_name, ctime )
			chkbox = umcd.Checkbox( static_options = { 'snapshot' : snapshot_name } )
			idlist.append( chkbox.id() )
			opts = copy.copy( object.options )
			opts[ 'snapshot' ] =  snapshot_name
			revert_cmd = umcp.SimpleCommand( 'uvmm/domain/snapshot/revert', options = opts )
			revert_act = [ umcd.Action( revert_cmd ), umcd.Action( overview_cmd ) ]
			revert_btn = umcd.LinkButton( _( 'Revert' ), actions = revert_act )
			opts = copy.copy( object.options )
			opts[ 'snapshot' ] =  [ snapshot_name ]
			delete_cmd = umcp.SimpleCommand( 'uvmm/domain/snapshot/delete', options = opts )
			delete_act = [ umcd.Action( delete_cmd ), umcd.Action( overview_cmd ) ]
			delete_btn = umcd.LinkButton( _( 'Delete' ), actions = delete_act )

			lst.add_row( [ chkbox, snapshot_name, ctime, [ revert_btn, delete_btn ] ] )

		btntoggle.checkboxes( idlist )
		opts = copy.copy( object.options )
		opts[ 'snapshot' ] = []
		delete_cmd = umcp.SimpleCommand( 'uvmm/domain/snapshots/delete', options = opts )
		delete_act = [ umcd.Action( delete_cmd, idlist ), umcd.Action( overview_cmd ) ]
		lst.add_row( [ umcd.Cell( [ umcd.HTML( '<b>%s</b>:&nbsp;' % _( 'Selection' ) ), umcd.LinkButton( _( 'Delete' ), actions = delete_act ) ], attributes = { 'colspan' : '5' } ) ] )
		table.add_row( [ lst ] )

		return table

	def _show_op( self, variable, node_uri ):
		"""Check registry if operation should be shown."""
		var = 'uvmm/umc/show/%s' % variable
		if configRegistry.is_true( var, True ):
			return True
		if configRegistry.is_false( var, False ):
			return False

		pos = node_uri.find( ':' )
		if pos == -1:
			return False
		value = configRegistry.get( var )
		schema = node_uri[ : pos ]
		if value == 'xen' and schema == 'xen':
			return True
		if value in ( 'kvm', 'qemu' ) and schema == 'qemu':
			return True

		return False

	def _create_domain_buttons( self, options, node_info, domain_info, overview = 'node', operations = False, remove_failure = 'domain' ):
		"""Create buttons to manage domain."""
		buttons = []
		try: # TODO
			node_uri, node_name = self.uvmm.node_uri_name(options['node'])
		except uvmmd.UvmmError, e:
			return buttons
		node_is_off = node_info.last_update < node_info.last_try
		overview_cmd = umcp.SimpleCommand('uvmm/%s/overview' % overview, options=options)
		comma = umcd.HTML('&nbsp;')

		# Start? if state is not running, blocked or paused
		cmd_opts = {'group' : options['group'], 'node': node_info.uri, 'domain': domain_info.uuid}
		if not node_is_off and not domain_info.state in ( 1, 2, 3 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			if getattr(domain_info, 'suspended', None):
				txt = _('Resume')
			else:
				txt = _('Start')
			buttons.append(umcd.LinkButton(txt, actions=[umcd.Action(cmd), umcd.Action(overview_cmd)]))
			buttons.append( comma )

		# VNC? if running and activated
		if not node_is_off and self._show_op( 'vnc', node_uri ) and domain_info.state in ( 1, 2 ) and domain_info.graphics and domain_info.graphics[ 0 ].port != -1:
			vnc = domain_info.graphics[0]
			host = node_info.name
			try:
				VNC_LINK_BY_NAME, VNC_LINK_BY_IPV4, VNC_LINK_BY_IPV6 = range(3)
				vnc_link_format = VNC_LINK_BY_IPV4
				if vnc_link_format == VNC_LINK_BY_IPV4:
					addrs = socket.getaddrinfo(host, vnc.port, socket.AF_INET)
					(family, socktype, proto, canonname, sockaddr) = addrs[0]
					host = sockaddr[0]
				elif vnc_link_format == VNC_LINK_BY_IPV6:
					addrs = socket.getaddrinfo(host, vnc.port, socket.AF_INET6)
					(family, socktype, proto, canonname, sockaddr) = addrs[0]
					host = '[%s]' % sockaddr[0]
			except: pass
			helptext = '%s:%s' % (host, vnc.port)
			if configRegistry.get('uvmm/umc/vnc', 'internal').lower() in ('external', ):
				uri = 'vnc://%s:%s' % (host, vnc.port)
				html = umcd.HTML('<a class="nounderline" target="_blank" href="%s" title="%s"><span class="content">%s</span></a>' % (uri, helptext, _( 'Direct access' ) ) )
			else:
				popupwindow = ("<html><head><title>" + \
				               _("%(dn)s on %(nn)s") + \
				               "</title></head><body>" + \
				               "<applet archive='/TightVncViewer.jar' code='com.tightvnc.vncviewer.VncViewer' height='100%%' width='100%%'>" + \
				               "<param name='host' value='%(h)s' />" + \
				               "<param name='port' value='%(p)s' />" + \
				               "<param name='offer relogin' value='no' />" + \
				               "</applet>" + \
				               "</body></html>") % {'h': host, 'p': vnc.port, 'nn': node_info.name, 'dn': domain_info.name}
				id = ''.join([c for c in '%s%s' % (host, vnc.port) if c.lower() in set('abcdefghijklmnopqrstuvwxyz0123456789') ])
				javascript = "var w=window.open('','VNC%s','dependent=no,resizable=yes');if(w.document.applets.length > 0){w.focus();}else{w.document.write('%s');w.document.close();};return false;" % (id, popupwindow.replace("'", "\\'"))
				html = umcd.HTML( '<a class="nounderline" href="#" onClick="%s" title="%s"><span class="content">%s</span></a>' % ( javascript, helptext, _( 'Direct access' ) ) )
			buttons.append( html )
			buttons.append( comma )

		# Suspend? if state is running or idle
		if not node_is_off and self._show_op( 'suspend', node_uri ) and hasattr(node_info, 'supports_suspend') and node_info.supports_suspend and domain_info.state in (1, 2):
			opts = copy.copy(cmd_opts)
			opts['state'] = 'SUSPEND'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Suspend' ), actions = [umcd.Action(cmd), umcd.Action(overview_cmd)]))
			buttons.append(comma)

		# Resume? if state is paused
		if not node_is_off and self._show_op( 'pause', node_uri ) and domain_info.state in ( 3, ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'RUN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Unpause' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Pause? if state is running or idle
		if not node_is_off and self._show_op( 'pause', node_uri ) and domain_info.state in ( 1, 2):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'PAUSE'
			cmd = umcp.SimpleCommand( 'uvmm/domain/state', options = opts )
			buttons.append( umcd.LinkButton( _( 'Pause' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# be sure only servers with the same virtualization technology are considered
		group_name = options['group']
		grouplist = set()
		node_type = set([capability.domain_type for capability in node_info.capabilities])
		for node_uri2, node_info2 in self.uvmm.get_group_info(group_name).items():
			if node_uri == node_uri2: # do not migrate to self
				continue
			if node_info2.last_update < node_info2.last_try: # do not migrato to offline nodes
				continue
			if node_type & set([capability.domain_type for capability in node_info2.capabilities]):
				grouplist.add(node_uri2)
		# migrate? if parameter set and state is not paused and more than two physical servers are available
		if len(grouplist) == 0:
			# FIXME: rate limit
			ud.debug( ud.ADMIN, ud.INFO, 'Migration button is disabled. At least two servers with the same virtualization technologie in this group are required.' )
		elif self._show_op('migrate', node_uri) and operations and domain_info.state != 3 and not getattr(domain_info, 'suspended', None):
			opt = {'group': group_name, 'grouplist': grouplist, 'node': node_info.uri, 'domain': domain_info.uuid}
			cmd = umcp.SimpleCommand( 'uvmm/domain/migrate', options=opt)
			buttons.append( umcd.LinkButton( _( 'Migrate' ), actions = [ umcd.Action( cmd ) ] ) )
			buttons.append( comma )

		# Stop? if state is not stopped
		if not node_is_off and not domain_info.state in ( 4, 5 ):
			opts = copy.copy( cmd_opts )
			opts[ 'state' ] = 'SHUTDOWN'
			cmd = umcp.SimpleCommand( 'uvmm/domain/stop', options = opts )
			buttons.append( umcd.LinkButton( _( 'Stop' ), actions = [ umcd.Action( cmd ), umcd.Action( overview_cmd ) ] ) )
			buttons.append( comma )

		# Remove? always
		if not node_is_off and operations:
			opts = copy.copy( cmd_opts )
			cmd = umcp.SimpleCommand( 'uvmm/domain/remove/images', options = opts )
			buttons.append( umcd.LinkButton( _( 'Remove' ), actions = [ umcd.Action( cmd ), ] ) )
			buttons.append( comma )

		# create drive
		# if operations:
		# 	opts = copy.copy( cmd_opts )
		# 	cmd = umcp.SimpleCommand( 'uvmm/drive/create', options = opts )
		# 	buttons.append( umcd.LinkButton( _( 'New Drive' ), actions = [ umcd.Action( cmd ), ] ) )
		# 	buttons.append( comma )

		return buttons[ : -1 ]

	def _drive_name( self, drive ):
		"""Translate disk type to display-string."""
		if drive == uvmmn.Disk.DEVICE_DISK:
			return _( 'hard drive' )
		elif drive == uvmmn.Disk.DEVICE_CDROM:
			return _( 'CDROM drive' )
		elif drive == uvmmn.Disk.DEVICE_FLOPPY:
			return _( 'floppy drive' )
		else:
			return _( 'unknown' )

	def uvmm_node_overview( self, object ):
		"""Node overview: show node utilization and all domains."""
		ud.debug( ud.ADMIN, ud.INFO, 'Node overview' )
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_NODE)
			node_uri = tv.node_uri
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			self.set_content( res, umcd.InfoBox( _( 'The physical server is not available at the moment' ) ) )
			self.finished(object.id(), res)
			return
		self.domain_wizard.reset()

		node_is_off = node_info.last_update < node_info.last_try

		content = umcd.List( attributes = { 'width' : '100%' }, default_type = 'uvmm_table' )

		node_header = _('%s (Physical server)') % self.uvmm._uri2name(node_uri, short=True)
		node_table = umcd.List(attributes={'width': '100%'}, default_type='uvmm_table')
		if node_is_off:
			info_txt = umcd.InfoBox(_('The physical server is not available at the moment'), icon='actions/critical', size=umct.SIZE_MEDIUM)
			node_table.add_row([info_txt])
		else:
			# node_cmd = umcp.SimpleCommand('uvmm/node/overview', options={'group': object.options['group'], 'node': node_info.uri})
			# node_btn = umcd.LinkButton( node.name, actions = [ umcd.Action( node_cmd ) ] )
			if node_uri.startswith( 'xen' ):
				try:
					cpu_usage = percentage(float(node_info.cpu_usage) / 10.0, width=150)
				except (ArithmeticError, ValueError, TypeError), e:
					cpu_usage = umcd.HTML('<i>%s</i>' % _('not available'))
			else:
				cpu_usage = umcd.HTML( '<i>%s</i>' % _( 'not available' ) )
			try:
				mem_usage = percentage(float(node_info.curMem) / node_info.phyMem * 100, '%s / %s' % (MemorySize.num2str(node_info.curMem), MemorySize.num2str(node_info.phyMem)), width=150)
			except (ArithmeticError, ValueError, TypeError), e:
				mem_usage = umcd.HTML('<i>%s</i>' % _('not available'))
			node_table.add_row([
				umcd.HTML('<b>%s</b>' % _('CPU usage'), attributes={'type':'umc_nowrap'}),
				umcd.Cell(cpu_usage, attributes={'width': '50%', 'type': 'umc_nowrap' }),
				umcd.HTML('<b>%s</b>' % _('Memory'), attributes={'type':'umc_nowrap'}),
				umcd.Cell(mem_usage, attributes={'width' : '50%'})])
		content.add_row([umcd.Section(node_header, node_table, attributes={'width': '100%'})])

		table = umcd.List( attributes = { 'type' : 'umc_mini_padding' }, default_type = 'uvmm_table' )
		num_buttons = 0
		for (domain_uuid, domain_info) in sorted(node_info.domains.items(), key=lambda (domain_uuid, domain_info): domain_info.name.lower()):
			# ignore XEN Domain-0
			if domain_info.name == 'Domain-0':
				continue
			domain_opt = {'group': object.options['group'], 'node': node_uri, 'domain': domain_info.uuid}
			domain_cmd = umcp.SimpleCommand('uvmm/domain/overview', options=domain_opt)
			domain_icon = 'uvmm/domain'
			if domain_info.state in ( 1, 2 ):
				domain_icon = 'uvmm/domain-on'
			elif domain_info.state in ( 3, ):
				domain_icon = 'uvmm/domain-paused'
			helptext = domain_info.name
			if domain_info.annotations.get('description'):
				helptext += '- %s' % (domain_info.annotations.get('description'))

			name = domain_info.name
			if len(domain_info.name) > 22:
				name = domain_info.name[0:18] + '...'
			domain_btn = umcd.LinkButton( name, tag = domain_icon, actions = [ umcd.Action( domain_cmd ) ], attributes = {'helptext': helptext} )
			domain_btn.set_size( umct.SIZE_SMALL )
			buttons = self._create_domain_buttons( object.options, node_info, domain_info, remove_failure = 'node' )
			if len( buttons ) > num_buttons:
				num_buttons = len( buttons )
			# os = getattr( domain_info, 'annotations', {} ).get( 'os', '' )
			# if len( os ) > 15:
			# 	os = os[ : 13 ] + '...'
			if not len( table.get_content() ):
				table.set_header( [ umcd.HTML( _('Instance'), attributes = { 'width': '100%', 'type' : 'umc_nowrap'} ), umcd.HTML( _('CPU usage') , attributes = { 'type' : 'umc_nowrap' , 'align':'right'} ), umcd.HTML( _('Memory') , attributes = { 'type' : 'umc_nowrap' , 'align':'right'} ) ] )

			try:
				cpu_usage = percentage(float(domain_info.cputime[0]) / 10, width=80)
			except (ArithmeticError, ValueError, TypeError), e:
				cpu_usage = umcd.HTML('<i>%s</i>' % _('not available'))
			try:
				mem_usage = umcd.Number(MemorySize.num2str(domain_info.maxMem))
			except (ArithmeticError, ValueError, TypeError), e:
				mem_usage = umcd.HTML('<i>%s</i>' % _('not available'))
			table.add_row([
				umcd.Cell(domain_btn, attributes={'type': 'umc_mini_padding', 'width': '100%'}),
				umcd.Cell(cpu_usage, attributes={'type': 'umc_mini_padding', 'align': 'center'}),
				umcd.Cell(mem_usage, attributes={'type': 'umc_mini_padding umc_nowrap', 'align': 'right'}),
				umcd.Cell(buttons, attributes={'type': 'umc_mini_padding umc_nowrap'})
				],
				attributes={'type': 'umc_mini_padding'})# + buttons )

		content.add_row( [ umcd.Cell( table, attributes = { 'colspan' : '2' } ), ] )
		self.set_content( res, content )
		self.finished(object.id(), res)

	def _dlg_domain_settings( self, object, node_info, domain_info ):
		"""Create domain setting widgets."""
		domain_is_off = 5 == domain_info.state
		try: # TODO
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
		except uvmmd.UvmmError, e:
			return []

		is_xen = node_uri.startswith('xen')

		content = umcd.List( default_type = 'uvmm_settings_table' )

		types = []
		archs = []
		for template in node_info.capabilities:
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

		overview_cmd = umcp.SimpleCommand('uvmm/domain/overview', options=copy.copy(object.options))

		# if domain is not stopped ...
		make_func = domain_is_off and umcd.make or umcd.make_readonly

		tech_default = '%s-%s' % ( handler._getattr( domain_info, 'domain_type', 'xen' ), handler._getattr( domain_info, 'os_type', 'hvm' ) )
		cpus_select.max = int( node_info.cpus )
		mem = handler._getattr(domain_info, 'maxMem', str(512<<10)) # KiB
		virt_tech = umcd.make_readonly( self[ 'uvmm/domain/configure' ][ 'type' ], default = tech_default, attributes = { 'width' : '250' } )
		os_widget = umcd.make( self[ 'uvmm/domain/configure' ][ 'os' ], default = getattr(domain_info, 'annotations', {}).get('os', ''), attributes = { 'width' : '250' } )
		contact_widget = umcd.make( self[ 'uvmm/domain/configure' ][ 'contact' ], default = getattr(domain_info, 'annotations', {}).get('contact', ''), attributes = { 'width' : '250' } )
		description_widget = umcd.make( self[ 'uvmm/domain/configure' ][ 'description' ], default = getattr(domain_info, 'annotations', {}).get('description', ''), attributes = { 'width' : '250' } )

		name = make_func( self[ 'uvmm/domain/configure' ][ 'name' ], default = handler._getattr( domain_info, 'name', '' ), attributes = { 'width' : '250' } )
		arch = make_func( self[ 'uvmm/domain/configure' ][ 'arch' ], default = handler._getattr( domain_info, 'arch', 'i686' ), attributes = { 'width' : '250' } )
		cpus = make_func( self[ 'uvmm/domain/configure' ][ 'cpus' ], default = handler._getattr( domain_info, 'vcpus', '1' ), attributes = { 'width' : '250' } )
		memory = make_func( self[ 'uvmm/domain/configure' ][ 'memory' ], default = MemorySize.num2str( mem ), attributes = { 'width' : '250' } )

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
				for key, descr in boot_dev_select.choices():
					ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: boot devices (compare): %s == %s' % ( key, dev ) )
					if key == str( dev ):
						bd_default.append( ( key, descr ) )
						break
		boot_dev.syntax.may_change = domain_is_off
		bootdevs = umcd.MultiValue( self[ 'uvmm/domain/configure' ][ 'bootdevs' ], fields = [ boot_dev ], default = bd_default, attributes = { 'width' : '200' } )
		bootdevs.syntax.may_change = domain_is_off

		# drive listing
		drive_sec = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		if domain_is_off:
			cmd = umcp.SimpleCommand('uvmm/drive/create', options=copy.copy(object.options))
			btn = umcd.LinkButton(_('Add new drive'), 'uvmm/add', actions=[umcd.Action(cmd),])
			btn.set_size( umct.SIZE_SMALL )
			drive_sec.add_row([ btn ])
		disk_list = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		disk_list.set_header( [ _( 'Type' ), _( 'Image' ), _( 'Size' ), _( 'Pool' ), '' ] )
		if domain_info and domain_info.disks:
			defaults = []
			first = True
			for dev in domain_info.disks:
				remove_cmd = umcp.SimpleCommand( 'uvmm/drive/remove', options = copy.copy( object.options ) )
				remove_cmd.incomplete = True
				edit_cmd = umcp.SimpleCommand( 'uvmm/drive/edit', options = copy.copy( object.options ) )
				edit_cmd.incomplete = True
				bootdev_cmd = umcp.SimpleCommand( 'uvmm/drive/bootdevice', options = copy.copy( object.options ) )
				remove_cmd.options[ 'disk' ] = None
				values = {}
				values[ 'type' ] = self._drive_name( dev.device )

				values[ 'image' ] = os.path.basename( dev.source )
				values['pool'] = getattr(dev, 'pool', None) or os.path.dirname(dev.source)
				size = getattr(dev, 'size', None)
				if not dev.source:
					values['size'] = _('empty')
				elif size:
					values['size'] = MemorySize.num2str(size)
				else:
					values['size'] = _('unknown')

				buttons = []
				if domain_is_off:
					remove_cmd.options['disk'] = dev.target_dev
					remove_btn = umcd.LinkButton( _( 'Remove' ), actions = [ umcd.Action( remove_cmd ) ] )
					buttons.append(remove_btn)

					# <= UCS-2.4-2: Only VirtIO can be changed, which is only fully working for HDs
					# >= UCS-2.4-3: +Allow online change of CDROM and FLOPPY
					unchangeable = dev.device == uvmmn.Disk.DEVICE_FLOPPY or dev.type == uvmmn.Disk.TYPE_BLOCK
					if not unchangeable:
						edit_cmd.options['disk'] = dev.target_dev
						edit_btn = umcd.LinkButton( _( 'Edit' ), actions = [ umcd.Action( edit_cmd ) ] )
						buttons.append( edit_btn )

					if not first:
						bootdev_cmd.options['disk'] = dev.target_dev
						bootdev_btn = umcd.LinkButton( _( 'Set as boot device' ), actions = [ umcd.Action( bootdev_cmd, options = { 'disk' : dev.source } ), umcd.Action( overview_cmd ) ] )
						buttons.append( bootdev_btn )

				# Xen can change source, but ...
				# 1) this requires both libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE | libvirt.VIR_DOMAIN_DEVICE_MODIFY_CONFIG,
				# 2) xend barfs with "xend_post: error from xen daemon: (xend.err 'Device 832 not connected')" in File "/usr/lib/python2.5/site-packages/xen/xend/XendDomainInfo.py", line 1218, in device_configure
				if dev.device in (uvmmn.Disk.DEVICE_FLOPPY, uvmmn.Disk.DEVICE_CDROM) and not is_xen:
					change_cmd = umcp.SimpleCommand('uvmm/drive/media/change')
					change_cmd.options['group'] = object.options['group']
					change_cmd.options['node'] = node_uri
					change_cmd.options['domain'] = object.options['domain']
					change_cmd.options['drive-type'] = uvmmn.Disk.map_device(id=dev.device)
					if getattr(dev, 'pool', False):
						change_cmd.options['pool-name'] = dev.pool
					change_cmd.options['vol-name'] = os.path.basename(dev.source)
					change_cmd.options['target_dev'] = dev.target_dev
					change_btn = umcd.LinkButton(_('Change media'), actions=[umcd.Action(change_cmd)])
					buttons.append(change_btn)

				if len(values[ 'image' ])> 40:
					image_name = umcd.HTML('<p title="%s">%s...</p>' % (values[ 'image' ], values[ 'image' ][0:40]))
				else:
					image_name = umcd.HTML('<p title="%s">%s</p>' % (values[ 'image' ], values[ 'image' ]))
				disk_list.add_row( [ values[ 'type' ], image_name, values[ 'size' ], values[ 'pool' ], buttons ] )
				if domain_info.os_type in ( 'linux', 'xen' ):
					first = False
		drive_sec.add_row( [disk_list ] )

		# network interfaces
		nic_sec = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		if domain_is_off:
			cmd = umcp.SimpleCommand( 'uvmm/nic/create', options = copy.copy( object.options ) )
			cmd.incomplete = True
			btn = umcd.LinkButton(_('Add new network interface'), 'uvmm/add', actions=[umcd.Action(cmd),])
			btn.set_size( umct.SIZE_SMALL )
			nic_sec.add_row([ btn ])
		nic_list = umcd.List( attributes = { 'width' : '100%' }, default_type = 'umc_list_element_narrow' )
		nic_list.set_header( [ _( 'Typ' ), _( 'Source' ), _( 'Driver' ), _( 'MAC address' ), '' ] )
		if domain_info and domain_info.interfaces:
			defaults = []
			for iface in domain_info.interfaces:
				opts = copy.copy( object.options )
				opts[ 'nictype' ] = iface.map_type( id = iface.type )
				opts[ 'source' ] = iface.source
				opts[ 'mac' ] = iface.mac_address
				opts[ 'driver' ] = iface.model
				opts[ 'target' ] = iface.target
				remove_cmd = umcp.SimpleCommand( 'uvmm/nic/remove', options = opts )
				edit_cmd = umcp.SimpleCommand( 'uvmm/nic/edit', options = opts )
				edit_cmd.incomplete = True

				values = {}
				if iface.type == uvmmn.Interface.TYPE_BRIDGE:
					nic_type = _( 'Bridge' )
				elif iface.type == uvmmn.Interface.TYPE_NETWORK:
					nic_type = _( 'NAT' )
				elif iface.type == uvmmn.Interface.TYPE_USER:
					nic_type = _('User')
				elif iface.type == uvmmn.Interface.TYPE_ETHERNET:
					nic_type = _('TUN')
				elif iface.type == uvmmn.Interface.TYPE_DIRECT:
					nic_type = _('Direct')
				else:
					nic_type = _( 'unknown' )
				nic_source = iface.source or _('unknown')
				if iface.model:
					nic_driver = iface.model
				else:
					if domain_info.os_type in ( 'xen', 'linux' ):
						nic_driver = 'netfront'
					else:
						nic_driver = 'rtl8139'

				buttons = []
				if domain_is_off:
					buttons.append(umcd.LinkButton(_('Remove'), actions=[umcd.Action(remove_cmd), umcd.Action(overview_cmd)]))
					if iface.type in (uvmmn.Interface.TYPE_BRIDGE, uvmmn.Interface.TYPE_NETWORK):
						buttons.append(umcd.LinkButton(_('Edit'), actions=[umcd.Action(edit_cmd)]))

				nic_list.add_row([
					nic_type,
					nic_source,
					nic_driver_select.description(nic_driver),
					iface.mac_address,
					buttons
					])

		nic_sec.add_row( [ nic_list ] )

		vnc_bool = False
		vnc_global = True
		vnc_keymap = 'de'
		old_passwd = ''
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
					if gfx.passwd:
						old_passwd = gfx.passwd
					vnc_keymap = gfx.keymap
					break

		vnc = make_func( self[ 'uvmm/domain/configure' ][ 'vnc' ], default = vnc_bool, attributes = { 'width' : '250' } )
		kblayout = make_func( self[ 'uvmm/domain/configure' ][ 'kblayout' ], default = vnc_keymap, attributes = { 'width' : '250' } )
		vnc_global = make_func( self[ 'uvmm/domain/configure' ][ 'vnc_global' ], default = vnc_global, attributes = { 'width' : '250' } )
		if is_xen: # Xen does not support online VNC password change
			vnc_passwd = make_func(self['uvmm/domain/configure']['vnc_passwd'], default=old_passwd, attributes={'width': '250'})
		else:
			vnc_passwd = umcd.make(self['uvmm/domain/configure']['vnc_passwd'], default=old_passwd, attributes={'width': '250'})

		rtc_offset = make_func(self[ 'uvmm/domain/configure']['rtc_offset'], default=handler._getattr( domain_info, 'rtc_offset', ''), attributes={'width': '250'})

		content.add_row( [ name, os_widget ] )
		content.add_row( [ contact_widget, description_widget ] )
		if not is_xen: # Ignore on Xen
			content.add_row( [ arch, '' ] )
		content.add_row( [ cpus, memory ] )

		content2 = umcd.List( default_type = 'uvmm_settings_table' )
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
		content2.add_row( [ vnc_global, kblayout ] )

		content2.add_row( [ umcd.Text( '' ) ] )

		content2.add_row([rtc_offset])

		content2.add_row([umcd.Text('')])

		ids = (name.id(), os_widget.id(), contact_widget.id(), description_widget.id(), virt_tech.id(), arch.id(), cpus.id(), memory.id(), ram_disk.id(), root_part.id(), kernel.id(), advkernelconf.id(), vnc.id(), vnc_global.id(), vnc_passwd.id(), kblayout.id(), bootdevs.id(), rtc_offset.id())
		cfg_cmd = umcp.SimpleCommand( 'uvmm/domain/configure', options = object.options )

		sections = []
		if not domain_is_off:
			sections.append( [ umcd.InfoBox( _( 'Most settings of the virtual instance can not be modified while it is running.' ) ) ] )
		if not domain_info:
			sections.append( [ umcd.Section( _( 'Drives' ), drive_sec, hideable = False, hidden = False, name = 'drives.newdomain' ) ] )
			sections.append( [ umcd.Section( _( 'Network Interfaces' ), nic_sec, hideable = False, hidden = False, name = 'interfaces.newdomain' ) ] )
			sections.append( [ umcd.Section( _( 'Settings' ), content, hideable = False, hidden = True, name = 'settings.newdomain' ) ] )
			sections.append( [ umcd.Section( _( 'Extended Settings' ), content2, hideable = False, hidden = True, name = 'extsettings.newdomain' ) ] )
		else:
			sections.append( [ umcd.Section( _( 'Drives' ), drive_sec, hideable = True, hidden = False, name = 'drives.%s' % domain_info.name ) ] )
			sections.append( [ umcd.Section( _( 'Network Interfaces' ), nic_sec, hideable = True, hidden = False, name = 'interfaces.%s' % domain_info.name ) ] )
			sections.append( [ umcd.Section( _( 'Settings' ), content, hideable = True, hidden = True, name = 'settings.%s' % domain_info.name ) ] )
			sections.append( [ umcd.Section( _( 'Extended Settings' ), content2, hideable = True, hidden = True, name = 'extsettings.%s' % domain_info.name ) ] )
		sections.append( [ umcd.Cell( umcd.Button( _( 'Save' ), actions = [ umcd.Action( cfg_cmd, ids ), umcd.Action( overview_cmd ) ], default = True ), attributes = { 'align' : 'right' } ) ] )

		return sections

	def _create_resync_info( self, object, table ):
		resync_cmd = umcd.Action( umcp.SimpleCommand( 'uvmm/daemon/restart', options = copy.copy( object.options ) ) )
		overview_cmd = umcd.Action( umcp.SimpleCommand( 'uvmm/domain/overview', options = copy.copy( object.options ) ) )
		resync = umcd.LinkButton( _( 'Resynchronize' ), actions = [ resync_cmd, overview_cmd ] )
		table.add_row( [ _( 'The information about the virtual instance could not be retrieved. Clicking the refresh button will retry to collect the information. If this does not work a resynchronization can be triggered by clicking the following button.' ) ] )
		table.add_row( [ umcd.Cell( resync, attributes = { 'align' : 'right' } ) ] )

	def uvmm_domain_overview( self, object, finish = True ):
		"""Single domain overview."""
		ud.debug( ud.ADMIN, ud.INFO, 'Domain overview' )

		try:
			object.options[ 'node' ] = object.options[ 'dest' ]
		except KeyError:
			pass

		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			domain_info = tv.domain_info
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			return self.uvmm_node_overview( object )
		self.domain_wizard.reset()

		node_is_off = node_info.last_update < node_info.last_try

		blind_table = umcd.List( default_type = 'uvmm_table' )

		if not domain_info:
			self._create_resync_info( object, blind_table )
		else:
			infos = umcd.List( default_type = 'uvmm_table' )
			w_status = [umcd.HTML('<b>%s</b>' % _('Status')), handler.STATES[domain_info.state]]
			w_os = [umcd.HTML('<b>%s</b>' % _('Operating System')), umcd.Cell( umcd.Text( getattr(domain_info, 'annotations', {}).get('os', '' ) ), attributes = { 'type' : 'umc_mini_padding umc_nowrap' } ) ]
			contact = getattr(domain_info, 'annotations', {}).get('contact', '' )
			if contact:
				match = handler.MAIL_REGEX.match( contact )
				if match:
					infos = match.groupdict()
					if infos[ 'address' ]:
						if infos[ 'name' ]:
							contact = umcd.HTML( '<a href="mailto:%(address)s">%(name)s</a>' % infos )
						else:
							contact = umcd.HTML( '<a href="mailto:%(address)s">%(address)s</a>' % infos )

			w_contact = [umcd.HTML('<b>%s</b>' % _('Contact')), contact ]
			w_description = [umcd.HTML('<b>%s</b>' % _('Description')), getattr(domain_info, 'annotations', {}).get('description', '' )]

			try:
				mem_usage = percentage(int(float(domain_info.curMem) / domain_info.maxMem * 100 ), label='%s / %s' % (MemorySize.num2str(domain_info.curMem), MemorySize.num2str(domain_info.maxMem)), width=130)
				w_mem = [umcd.HTML('<b>%s</b>' % _('Memory usage')), mem_usage]
			except Exception, e:
				w_mem = [umcd.HTML('<i>%s</i>' % _('currently not available'))]
			try:
				cpu_usage = percentage(float(domain_info.cputime[0]) / 10, width=130)
				w_cpu = [umcd.HTML('<b>%s</b>' % _('CPU usage')), cpu_usage]
			except Exception, e:
				w_cpu = [umcd.HTML('<i>%s</i>' % _('currently not available'))]

			ops = umcd.List( default_type = 'uvmm_table' )
			buttons = self._create_domain_buttons( object.options, node_info, domain_info, overview = 'domain', operations = True )
			ops.add_row( buttons )

			if node_is_off:
				snapshots = ()
			else:
				snapshots = self._create_domain_snapshots( object, node_info, domain_info )

			tab = umcd.List( default_type = 'uvmm_table' )
			tab.add_row(w_status + w_cpu)
			tab.add_row(w_os + w_mem)
			tab.add_row( w_contact + w_description )

			tech = '%s-%s' % ( domain_info.domain_type, domain_info.os_type )
			blind_table.add_row( [ umcd.Section( _( 'Virtual instance %(domain)s - <i>%(tech)s</i>' ) % { 'domain' : domain_info.name, 'tech' : VirtTechSelect.MAPPING.get( tech, '' )  }, tab ) ] )
			blind_table.add_row( [ umcd.Cell( umcd.Section( _( 'Operations' ), ops ) ) ] )
			if snapshots:
				blind_table.add_row( [ umcd.Section( _( 'Snapshots' ), snapshots, hideable = True, hidden = True, name = 'domain.snapshots' ) ] )

			if node_is_off:
				info_txt = umcd.InfoBox(_('The physical server is not available at the moment'), icon='actions/critical', size=umct.SIZE_MEDIUM)
				blind_table.add_row([info_txt])
				info_txt = umcd.HTML(_('''<p>For fail over the virtual machine can be migrated to another physical server re-using the last known configuration and all disk images. This can result in <strong>data corruption</strong> if the images are <strong>concurrently used</strong> by multiple running instances! Therefore the failed server <strong>must be blocked from accessing the image files</strong>, for example by blocking access to the shared storage or by disconnecting the network.</p><p>When the server is restored, all its previous virtual instances will be shown again. Any duplicates have to be cleaned up manually by migrating the instances back to the server or by deleting them. Make sure that shared images are not delete.</p>'''))
				blind_table.add_row([info_txt])
			else:
				content = self._dlg_domain_settings( object, node_info, domain_info )
				for line in content:
					blind_table.add_row( line )

		self.set_content( res, blind_table )
		if finish:
			self.finished(object.id(), res)
		return res

	def uvmm_domain_migrate( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain migrate' )
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			src_uri = tv.node_uri
			src_name = tv.node_name
			domain_info = tv.domain_info
			domain_uuid = tv.domain_uuid
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			res = tv.get_failure_response(e)
			self.finished(object.id(), res)
			return

		content = umcd.List()
		try:
			if 'dest' in object.options:
				dest_uri, dest_name = self.uvmm.node_uri_name(object.options['dest'])
				ud.debug(ud.ADMIN, ud.INFO, 'Domain migrate: %s # %s -> %s' % (src_uri, domain_uuid, dest_uri))
				self.uvmm.domain_migrate( src_uri, dest_uri, domain_uuid )
			else:
				dest_node_select.update_choices(object.options.get('grouplist', set()))
				content.add_row([umcd.Text(_('Migrate virtual instance %(domain)s from physical server %(source)s to:') % {'domain': domain_info.name, 'source': src_name} , attributes={'colspan': '2'})])
				dest = umcd.make( self[ 'uvmm/domain/migrate' ][ 'dest' ] )
				content.add_row( [ dest, '' ] )

				cmd_migrate = umcd.Action(umcp.SimpleCommand('uvmm/domain/migrate', options=object.options), [dest.id()])
				cmd_success = umcd.Action(umcp.SimpleCommand('uvmm/domain/overview', options=object.options), [dest.id()], status_range=umcd.Action.SUCCESS)
				cmd_failure = umcd.Action(umcp.SimpleCommand('uvmm/domain/overview', options=object.options), status_range=umcd.Action.FAILURE)

				content.add_row([umcd.Button(_('Cancel'), actions=[cmd_failure]), umcd.Button(_('Migrate'), actions=[cmd_migrate, cmd_success, cmd_failure], default=True)])
				sec = umcd.Section(_('Migrate %(domain)s') % {'domain': domain_info.name}, content, attributes={'width': '100%'})
				self.set_content( res, sec, location = False, refresh = False )
			self.finished( object.id(), res )
		except uvmmd.UvmmError, e:
			res.status( 301 )
			ud.debug(ud.ADMIN, ud.INFO, 'Domain migrate: error: %s' % str(e))
			self.finished(object.id(), res, report=str(e))

	def uvmm_domain_configure( self, object, create = False ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure' )
		res = umcp.Response( object )

		tv = TreeView(self.uvmm, object)
		try:
			node_uri = tv.node_uri
			try:
				domain_info = tv.domain_info
			except (uvmmd.UvmmError, KeyError), e:
				if create:
					domain_info = uuv_proto.Data_Domain()
				else:
					raise
		except (uvmmd.UvmmError, KeyError), e:
			try:
				res = tv.get_tree_response(TreeView.LEVEL_NODE)
			except uvmmd.UvmmError, e:
				res = tv.get_failure_response(e)
				self.finished(object.id(), res)
				return
			table = umcd.List( default_type = 'uvmm_table' )
			self._create_resync_info( object, table )
			self.set_content( res, table )
			self.finished( object.id(), res )
			return
		domain_info.name = object.options[ 'name' ]
		domain_info.domain_type, domain_info.os_type = object.options[ 'type' ].split( '-' )
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: operating system: %s' % handler._getstr( object, 'os' ) )
		domain_info.annotations['os'] = handler._getstr( object, 'os' )
		domain_info.annotations['description'] = handler._getstr( object, 'description' )
		domain_info.annotations['contact'] = handler._getstr( object, 'contact' )
		if 'arch' in object.options:
			domain_info.arch = object.options['arch']
		ud.debug( ud.ADMIN, ud.INFO, 'Domain configure: architecture: %s' % domain_info.arch )
		domain_info.vcpus = int( object.options[ 'cpus' ] )
		# if para-virtualized machine ...
		if domain_info.domain_type == 'xen' and domain_info.os_type in ('linux', 'xen'):
			if object.options.get( 'advkernelconf', False ):
				domain_info.kernel = handler._getstr( object, 'kernel' )
				domain_info.cmdline = handler._getstr( object, 'cmdline' )
				domain_info.initrd = handler._getstr( object, 'initrd' )
				domain_info.bootloader = None
				domain_info.bootloader_args = None
			else:
				domain_info.kernel = None
				domain_info.cmdline = None
				domain_info.initrd = None
				domain_info.bootloader = '/usr/bin/pygrub'
				domain_info.bootloader_args = '-q' # Bug #19249: PyGrub timeout
		domain_info.boot = handler._getstr( object, 'bootdevs' )
		domain_info.maxMem = MemorySize.str2num( object.options[ 'memory' ] )
		domain_info.rtc_offset = handler._getstr(object, 'rtc_offset')

		# graphics
		ud.debug( ud.ADMIN, ud.INFO, 'Configure Domain: graphics: %s' % object.options[ 'vnc' ] )
		if object.options[ 'vnc' ]:
			try:
				vncs = filter(lambda gfx: gfx.type == uuv_node.Graphic.TYPE_VNC, domain_info.graphics)
				gfx = vncs[0]
			except (AttributeError, IndexError), e:
				gfx = uuv_node.Graphic()
				domain_info.graphics.append( gfx )
			gfx.type = uuv_node.Graphic.TYPE_VNC
			gfx.keymap = object.options[ 'kblayout' ]
			gfx.passwd = object.options['vnc_passwd']
			if object.options[ 'vnc_global' ]:
				gfx.listen = '0.0.0.0'
			else:
				gfx.listen = None
			ud.debug( ud.ADMIN, ud.INFO, 'Configure Domain: graphics: %s' % str( gfx ) )
		else:
			# TODO: What about SDL, Spice, ...?
			non_vncs = filter(lambda gfx: gfx.type != uuv_node.Graphic.TYPE_VNC, domain_info.graphics)
			domain_info.graphics = non_vncs

		try:
			resp = self.uvmm.domain_configure(node_uri, domain_info)
		except uvmmd.UvmmError, e:
			res.status( 301 )
			self.finished(object.id(), res, report=str(e))
		else:
			if resp.messages:
				res.status( 201 )
				msg = _('Some information of the virtual instance could not be saved!<br/>') + '<br/>'.join([str(_uvmm_locale(text)) for text in resp.messages])
			else:
				msg = ''
			self.finished( object.id(), res, report = msg )

	def uvmm_domain_state( self, object ):
		ud.debug(ud.ADMIN, ud.INFO, 'Domain State: changing %(domain)s to %(state)s' % object.options)
		res = umcp.Response( object )

		domain_uuid = object.options['domain']
		state = object.options['state']
		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			self.uvmm.domain_set_state(node_uri, domain_uuid, state)
			ud.debug(ud.ADMIN, ud.INFO, 'Domain State: change to %s' % state)
		except uvmmd.UvmmError, e:
			res.status( 301 )
			self.finished(object.id(), res, report=str(e))
		else:
			self.finished( object.id(), res )

	def uvmm_domain_create( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Domain create' )
		# user cancelled the wizard
		if object.options.get( 'action' ) == 'cancel':
			self.drive_wizard.reset()
			self.uvmm_node_overview( object )
			return

		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			return self.uvmm_node_overview( object )

		if not 'action' in object.options:
			self.domain_wizard.max_memory = node_info.phyMem
			self.domain_wizard.archs = set([t.arch for t in node_info.capabilities])
			self.domain_wizard.reset()

		result = self.domain_wizard.action( object, ( node_uri, node_info ) )

		# domain wizard finished?
		if self.domain_wizard.result():
			try:
				resp = self.uvmm.domain_configure(node_uri, self.domain_wizard.result() )
			except uvmmd.UvmmError, e:
				# FIXME: something went wrong. We have to erase als 'critical' data and restart with the drive wizard part
				self.domain_wizard._result = None
				self.domain_wizard.current = 1
				self.domain_wizard.drives = []
				self.domain_wizard.action( object, ( node_uri, node_info ) )
				page = self.domain_wizard.setup( object )
				res.dialog[ 0 ].set_dialog( page )
				res.status( 301 )
				self.finished(object.id(), res, report=str(e))
			else:
				object.options['domain'] = resp.data
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
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			domain_info = tv.domain_info
			domain_uuid = tv.domain_uuid
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			return self.uvmm_node_overview( object )

		boxes = []
		lst = umcd.List( default_type = 'uvmm_table' )

		if domain_info.disks:
			lst.add_row([umcd.Cell(umcd.Text(_('When removing a virtual instance the disk images bind to it may be removed also. Please select the disks that should be remove with the virtual instance. Be sure that none of the images to be delete are used by any other instance.')), attributes={'colspan': '3'})])
			lst.add_row([''])
			defaults = []
			for disk in domain_info.disks:
				try:
					do_delete = self._is_disk_deleteable(disk, tv)
				except (TypeError, ValueError), e:
					continue
				static_options = { 'drives' : disk.source }
				chk_button = umcd.Checkbox(static_options=static_options, default=do_delete)
				chk_button.set_text( '%s: %s' % ( self._drive_name( disk.device ), disk.source ) )
				boxes.append( chk_button.id() )
				lst.add_row( [ umcd.Cell( umcd.Text( '' ), attributes = { 'width' : '10' } ), umcd.Cell( chk_button, attributes = { 'colspan' : '2' } ) ] )

		opts = copy.copy(object.options)
		opts['drives'] = []
		back = umcp.SimpleCommand('uvmm/domain/overview', options=opts)
		req = umcp.SimpleCommand('uvmm/domain/remove', options=opts)
		fail_overview_cmd = umcp.SimpleCommand('uvmm/domain/overview', options=opts)
		opts2 = copy.copy(object.options)
		del opts2['domain']
		success_overview_cmd = umcp.SimpleCommand('uvmm/node/overview', options=opts2)
		cancel = umcd.Button(_('Cancel'), actions=[umcd.Action(back)])
		button = umcd.Button(_('Remove'), actions=[umcd.Action(req, boxes), umcd.Action(success_overview_cmd, status_range=umcd.Action.SUCCESS), umcd.Action(fail_overview_cmd, status_range=umcd.Action.FAILURE)], default=True)
		lst.add_row([''])
		lst.add_row([umcd.Cell(cancel, attributes={'align': 'right', 'colspan': '2'}), umcd.Cell(button, attributes={'align': 'right'})])

		res.dialog[ 0 ].set_dialog( umcd.Section( _( 'Remove the virtual instance %(instance)s?' ) % { 'instance' : domain_info.name }, lst, hideable = False ) )
		self.finished(object.id(), res)

	def uvmm_domain_remove( self, object ):
		ud.debug(ud.ADMIN, ud.INFO, 'Domain remove %(domain)s' % object.options)
		res = umcp.Response( object )

		domain = domain_uuid = object.options['domain']
		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, domain_uuid)
			domain = domain_info.name

			# shutdown machine before removing it
			self.uvmm.domain_set_state(node_uri, domain_uuid, 'SHUTDOWN')

			# remove domain
			self.uvmm.domain_undefine(node_uri, domain_uuid, object.options['drives'])
		except uvmmd.UvmmError, e:
			res.status( 301 )
			self.finished(object.id(), res, report=_('Removing the instance <i>%(domain)s</i> failed') % {'domain': domain})
		else:
			res.status( 201 )
			self.finished(object.id(), res, report=_('The instance <i>%(domain)s</i> was removed successfully') % {'domain': domain})

	def uvmm_domain_snapshot_create(self, object):
		"""Create new snapshot of domain."""
		ud.debug(ud.ADMIN, ud.INFO, 'Domain snapshot create %(domain)s' % object.options)
		domain_uuid = object.options['domain']
		try:
			snapshot_name = object.options['snapshot']
		except KeyError, e:
			snapshot_name = None
			object.incomplete = True

		try:
			tv = TreeView(self.uvmm, object)
			if object.incomplete:
				res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			else:
				domain_info = tv.domain_info
				node_info = tv.node_info
			node_uri = tv.node_uri
		except (uvmmd.UvmmError, KeyError), e:
			res = tv.get_failure_response(e)
			self.finished(object.id(), res)
			return

		if object.incomplete:
			snapshot_cel = umcd.make(self['uvmm/domain/snapshot/create']['snapshot'], attributes={'colspan': '2'})

			opts = copy.copy(object.options)
			overview_cmd = umcp.SimpleCommand('uvmm/domain/overview', options=opts )

			cancel_act = [umcd.Action(overview_cmd)]
			cancel_btn = umcd.LinkButton(_('Cancel'), actions=cancel_act)
			cancel_cel = umcd.Cell(cancel_btn, attributes={'align': 'right', 'colspan': '2'})

			opts = copy.copy(object.options)
			create_cmd = umcp.SimpleCommand('uvmm/domain/snapshot/create', options=opts)

			create_act = [umcd.Action(create_cmd, [snapshot_cel.id()]), umcd.Action(overview_cmd)]
			create_btn = umcd.Button( _( 'Create' ), actions = create_act, default = True )
			create_cel = umcd.Cell(create_btn, attributes={'align': 'right'})

			lst = umcd.List( default_type = 'uvmm_table' )
			lst.add_row([umcd.Cell(umcd.Text(_('Enter the name for the snapshot')), attributes={'colspan': '3'})])
			lst.add_row([snapshot_cel,])
			lst.add_row([cancel_cel, create_cel])
			self.set_content( res, lst, location = False, refresh = False )
			self.finished(object.id(), res)
		else:
			res = umcp.Response(object)
			try:
				self.uvmm.domain_snapshot_create(node_uri, domain_uuid, snapshot_name)
				res.status(201)
				report = _('The instance <i>%(domain)s</i> was snapshoted to <i>%(snapshot)s</i> successfully')
			except uvmmd.UvmmError, e:
				res.status(301)
				report = _('Snapshoting the instance <i>%(domain)s</i> to <i>%(snapshot)s</i> failed')
			values = {'domain': domain_info.name, 'snapshot': snapshot_name}
			self.finished(object.id(), res, report=report % values)

	def uvmm_domain_snapshot_revert(self, object):
		"""Revert to snapshot of domain."""
		ud.debug(ud.ADMIN, ud.INFO, 'Domain snapshot revert %(domain)s' % object.options)
		domain_uuid = object.options['domain']
		snapshot_name = object.options['snapshot']

		res = umcp.Response(object)
		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, domain_uuid)
			self.uvmm.domain_snapshot_revert(node_uri, domain_uuid, snapshot_name)
			res.status(201)
			report = _('The instance <i>%(domain)s</i> was reverted to snapshot <i>%(snapshot)s</i> successfully')
		except uvmmd.UvmmError, e:
			res.status(301)
			report = _('Reverting to snapshot <i>%(snapshot)s</i> of instance <i>%(domain)s</i> failed')
		values = {'domain': domain_info.name, 'snapshot': snapshot_name}
		self.finished(object.id(), res, report=report % values)

	def uvmm_domain_snapshot_delete(self, object):
		"""Delete snapshot of domain."""
		ud.debug(ud.ADMIN, ud.INFO, 'Domain snapshot delete %(domain)s %(snapshot)s' % object.options)
		domain_uuid = object.options['domain']
		snapshot = object.options['snapshot']
		failure = []
		success = []
		res = umcp.Response(object)

		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, domain_uuid)
			for snapshot in snapshot:
				try:
					self.uvmm.domain_snapshot_delete(node_uri, domain_uuid, snapshot)
					success.append( snapshot )
				except uvmmd.UvmmError, e:
					failure.append( snapshot )
			# all snapshots could be deleted
			if success and not failure:
				res.status( 201 )
				if len( success ) == 1:
					report = _( 'The snapshot <i>%(snapshot)s of instance <i>%(domain)s</i> was deleted successfully' ) % { 'snapshot' : success[ 0 ], 'domain': domain_info.name }
				else:
					report = _( 'All selected snapshots of instance <i>%(domain)s</i> were deleted successfully:<br/>%(snapshots)s' ) % { 'snapshots' : ', '.join( success ), 'domain': domain_info.name }
			elif success and failure:
				res.status( 301 )
				report = _( 'Not all of the selected snapshots of instance <i>%(domain)s</i> could be deleted! The following snapshots still exists:<br/>%(snapshots)s' ) % { 'snapshots' : ', '.join( failure ), 'domain': domain_info.name }
			else:
				res.status( 301 )
				if len( failure ) == 1:
					report = _( 'The snapshot <i>%(snapshot)s of instance <i>%(domain)s</i> could not be deleted' ) % { 'snapshot' : failure[ 0 ], 'domain': domain_info.name }
				else:
					report = _( 'The selected snapshots of instance <i>%(domain)s</i> could not be deleted:<br/>%(snapshots)s' ) % { 'snapshots' : ', '.join( failure ), 'domain': domain_info.name }
		except uvmmd.UvmmError, e:
			res.status( 301 )
			report = _('Instance <i>%(domain)s</i> is unavailable')

		self.finished( object.id(), res, report = report )

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
