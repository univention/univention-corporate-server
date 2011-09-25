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
	LEVEL_ROOT, LEVEL_GROUP, LEVEL_NODE, LEVEL_DOMAIN = range(len(LEVELS))

	@staticmethod
	def __get_item_path(options, current=LEVELS[1:]):
		"""Calculate /group/node/domain path."""
		path = ()
		for level in current:
			if level in options:
				path += (options[level],)
			else:
				break
		return path

	@staticmethod
	def button_create( text, icon, command, options, current ):
		"""Create button."""
		cmd = umcp.SimpleCommand( command, options = copy.copy( options ) )
		action = umcd.Action( cmd )
		highlight = current == TreeView.__get_item_path(options)
		link = umcd.LinkButton( text, icon, actions = [ action ], current = highlight, attributes = { 'class' : 'umc_nowrap' } )
		link.set_size( umct.SIZE_SMALL )

		return link

	@staticmethod
	def safely_get_tree(uvmm_client, request, current=()):
		"""
		Create TreeView.
		'current' is a list of parameter names ('group', 'node', 'domain') passed via 'request.options' to determin the currenty selected item.
		"""
		res = umcp.Response(request)
		success = True

		current_path = TreeView.__get_item_path(request.options, current)
		try:
			table = TreeView.get_tree(uvmm_client, request, current=current_path)
		except uvmmd.ConnectionError:
			table = umcd.SimpleTreeTable()
			table.set_tree_data( [] )
			table.set_dialog( umcd.InfoBox( _( 'The connection to the Univention Virtual Machine Manager service could not be established. Please verify that it is started. You may use the UMC service module therefor.' ) ) )
			success = False
		res.dialog = umcd.Dialog( [ table ], attributes = { 'type' : 'uvmm_frame' } )

		return ( success, res )

	@staticmethod
	def get_tree(uvmm_client, request, current):
		"""
		Create TreeView.
		'current' is a prefix of the n-tuple (group_name, node_uri, domain_uuid) of the currently selected item.
		Additionally fills in some 'missing' request.options-parameters from UVMMd-data.
		"""
		node_tree = uvmm_client.get_node_tree()

		tree_view = []
		for group_name, nodes in sorted(node_tree.items(), key=lambda (group_name, nodes): group_name):
			is_current_group = group_name == request.options.get('group')
			# FIXME: should be removed if UVVMd supports groups
			if group_name == 'default':
				group_label = _('Physical servers')
			else:
				group_label = group_name
			options = {'group': group_name}
			link = TreeView.button_create(group_label, 'uvmm/group', 'uvmm/group/overview', options, current)
			tree_view.append(link)

			group_view = []
			tree_view.append(group_view)
			for node_uri, (age, domains) in sorted(nodes.items(), key=lambda (node_uri, (age, domains)): uvmmd.Client._uri2name(node_uri)): # sort by FQDN
				is_current_node = node_uri == request.options.get('node')
				if is_current_node:
					# Fill in missing 'group' from UVMMd data
					request.options.setdefault('group', group_name)

				node_name_short = uvmmd.Client._uri2name(node_uri, short=True)
				node_is_off = age > 0

				if node_uri.startswith('qemu'):
					icon = 'uvmm/node-kvm'
				elif node_uri.startswith('xen'):
					icon = 'uvmm/node-xen'
				else:
					icon = 'uvmm/node'
				if node_is_off:
					icon += '-off'
				options = {'group': group_name, 'node': node_name} # FIXME: node_name→node_uri
				link = TreeView.button_create(node_name_short, icon, 'uvmm/node/overview', options, current)
				group_view.append(link)

				domain_view = []
				group_view.append(domain_view)

				options = {'group': group_name, 'node': node_name, 'domain': 'NONE'} # FIXME: node_name→node_uri
				link = TreeView.button_create(_('Add'), 'uvmm/add', 'uvmm/domain/create', options, current)
				domain_view.append(link)

				for domain_uuid, domain_info in sorted(domains.items(), key=lambda (domain_uuid, domain_info): domain_info.name):
					is_current_domain = is_current_node and domain_uuid == request.options.get('domain')
					# Fill in missing 'domain_name' from UVMMd data
					if is_current_domain:
						request.options.setdefault('domain_name', domain_info.name)

					if domain_info.name == 'Domain-0':
						continue
					if node_is_off:
						icon = 'uvmm/domain-off'
					elif domain_info.state in (1, 2):
						icon = 'uvmm/domain-on'
					elif domain_info.state in (3,):
						icon = 'uvmm/domain-paused'
					else:
						icon = 'uvmm/domain'
					options = {'group': group_name, 'node': node_name, 'domain': domain_info.name, 'domain-uuid': domain_uuid} # FIXME: node_name→node_uri
					link = TreeView.button_create(domain_info.name, icon, 'uvmm/domain/overview', options, current)
					domain_view.append(link)

		table = umcd.SimpleTreeTable(collapsible=TreeView.LEVEL_NODE)
		table.set_tree_data([tree_view]) # the extra nesting is important
		return table
