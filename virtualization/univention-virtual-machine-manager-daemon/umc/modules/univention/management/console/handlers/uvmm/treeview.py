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

import copy

import univention.management.console as umc
import univention.management.console.protocol as umcp
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import uvmmd

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class TreeView( object ):
	LEVELS = ( '', 'group', 'node', 'domain', )

	@staticmethod
	def get_item_path( options ):
		path = ''
		for level in TreeView.LEVELS[ 1 : ]:
			if level in options:
				path += '/%s' % options[ level ]
			else:
				break
		return path

	@staticmethod
	def button_create( text, icon, command, options, current ):
		cmd = umcp.SimpleCommand( command, options = copy.copy( options ) )
		action = umcd.Action( cmd )
		highlight = False
		if current == TreeView.get_item_path( options ):
			highlight = True
		link = umcd.LinkButton( text, icon, actions = [ action ], current = highlight, attributes = { 'class' : 'umc_nowrap' } )
		link.set_size( umct.SIZE_SMALL )

		return link

	@staticmethod
	def convert(data, current, level=0, options={}, additional_buttons={}, uvmm=None, node_uri=None, cache={}):
		"""
		Convert nested list|tuple into TreeView of buttons.
		Depth-first recursion which creation on return path.

		data: nested list|tuples.
		level: recursion level.
		options: dictionary[level_name] of options for buttons.
		additional_buttons: dictionary[level] of buttons.
		uvmm: instance of uvmmd client.
		node_uri: URI of node for levels below 2.
		cache: dictionary for caching data during recursion calls.
		"""
		def get_node_info(node_uri):
			"""Get (cached) node_info."""
			try:
				node_info = cache[node_uri]
			except KeyError, e:
				node_info = cache.setdefault(node_uri, uvmm.get_node_info(node_uri))
			return node_info

		treedata = []
		opt = TreeView.LEVELS[ level ]
		command = 'uvmm/%s/overview' % opt

		icon = 'uvmm/' + opt

		for item in data:
			if item == None:
				continue
			if type( item ) not in ( list, tuple ):
				options[ opt ] = item
				if level == 2:
					node_uri = uvmm.node_name2uri( item )
					# FIXME: need to know the virtualization technology of offline nodes
					icon = 'uvmm/node-kvm-off'
					try:
						node_info = get_node_info(node_uri)
						if node_info.last_try == node_info.last_update:
							if node_uri.startswith( 'xen:' ):
								icon = 'uvmm/node-xen'
							else:
								icon = 'uvmm/node-kvm'
					except Exception, e:
						pass
					# remove domain name from hostname
					dot = item.find( '.' )
					if  dot > -1:
						item = item[ : dot ]
				elif level == 3:
					if item == 'Domain-0':
						continue
					node_info = get_node_info(node_uri)
					icon = 'uvmm/domain'
					for domain_info in node_info.domains:
						if domain_info.name == item:
							if domain_info.state in ( 1, 2 ):
								icon = 'uvmm/domain-on'
							elif domain_info.state in ( 3, ):
								icon = 'uvmm/domain-paused'
							break
				# FIXME: should be removed if UVVMd supports groups
				if level == 1 and item == 'default':
					item = _( 'Physical servers' )
				link = TreeView.button_create( item, icon, command, options, current )
				treedata.append( link )
			else: # list or tuple
				# check for additional buttons to append
				items = []
				if level in additional_buttons:
					for button in additional_buttons[ level ]:
						text, myicon, mycommand, myoptions = button
						myoptions.update( options )
						link = TreeView.button_create( text, myicon, mycommand, myoptions, current )
						items.append( link )
				items.extend(TreeView.convert(item, current, level + 1, options=copy.copy(options), additional_buttons=additional_buttons, uvmm=uvmm, node_uri=node_uri, cache=cache))
				treedata.append( items )

		return treedata

	@staticmethod
	def safely_get_tree( uvmm_client, object, current = [] ):
		res = umcp.Response( object )
		success = True

		current_path = ''
		for key in current:
			current_path += '/%s' % object.options[ key ]
		try:
			table = TreeView.get_tree( uvmm_client, current = current_path )
		except uvmmd.ConnectionError:
			table = umcd.SimpleTreeTable()
			table.set_tree_data( [] )
			table.set_dialog( umcd.InfoBox( _( 'The connection to the Univention Virtual Machine Manager service could not be established. Please verify that it is started. You may use the UMC service module therefor.' ) ) )
			success = False
		res.dialog = [ table ]

		return ( success, res )

	@staticmethod
	def get_tree( uvmm_client, current ):
		additional_buttons = { 2 : ( ( _( 'Add' ), 'uvmm/add', 'uvmm/domain/create', { 'domain' : 'NONE' } ), ) }
		table = umcd.SimpleTreeTable( collapsible = 2 )
		table.set_tree_data( TreeView.convert( uvmm_client.get_node_tree(), current, additional_buttons = additional_buttons, uvmm = uvmm_client, cache = {} ) )

		return table


