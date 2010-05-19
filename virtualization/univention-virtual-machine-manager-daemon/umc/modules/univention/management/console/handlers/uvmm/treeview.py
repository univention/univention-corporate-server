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
		link = umcd.LinkButton( text, icon, actions = [ action ], current = highlight )
		link.set_size( umct.SIZE_SMALL )

		return link

	@staticmethod
	def convert( data, current, level = 0, options = {}, additional_buttons = {} ):
		treedata = []
		opt = TreeView.LEVELS[ level ]
		command = 'uvmm/%s/overview' % opt
		icon = 'uvmm/' + opt
		for item in data:
			if type( item ) not in ( list, tuple ):
				if item == 'Domain-0':
					continue
				options[ opt ] = item
				link = TreeView.button_create( item, icon, command, options, current )
				treedata.append( link )
			else:
				# check for additional buttons to append
				items = []
				if level in additional_buttons:
					for button in additional_buttons[ level ]:
						text, myicon, mycommand, myoptions = button
						myoptions.update( options )
						link = TreeView.button_create( text, myicon, mycommand, myoptions, current )
						items.append( link )
				items.extend( TreeView.convert( item, current, level + 1, options = copy.copy( options ), additional_buttons = additional_buttons ) )
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
			table.set_dialog( umcd.InfoBox( _( 'The connection to the UVMM service could not be established. Please verify that it is started. You may use the UMC service module therefor.' ) ) )
			success = False
		res.dialog = [ table ]

		return ( success, res )
		
	@staticmethod
	def get_tree( uvmm_client, current ):
		additional_buttons = { 2 : ( ( _( 'Add' ), 'uvmm/add', 'uvmm/domain/create', { 'domain' : 'NONE' } ), ) }
		table = umcd.SimpleTreeTable( collapsible = 2 )
		table.set_tree_data( TreeView.convert( uvmm_client.get_node_tree(), current, additional_buttons = additional_buttons ) )
		
		return table


