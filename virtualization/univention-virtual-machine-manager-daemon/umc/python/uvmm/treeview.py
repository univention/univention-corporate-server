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

import copy

import univention.management.console as umc
import univention.management.console.protocol as umcp
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import uvmmd

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class TreeView( object ):
	"""
	Query UVMMd for all groups/nodes/domains and create tree-view.
	Save queried data for later calls.
	"""
	LEVELS = ( '', 'group', 'node', 'domain', )
	LEVEL_ROOT, LEVEL_GROUP, LEVEL_NODE, LEVEL_DOMAIN = range(len(LEVELS))
	SHOW_LEVEL = LEVEL_DOMAIN

	def __init__(self, uvmm_client, request):
		"""Create new instance associated with UVMMd."""
		self.uvmm_client = uvmm_client
		self.request = request
		self.node_tree = None

	@property
	def group_name(self):
		group_name = self.request.options['group']
		return group_name

	@property
	def node_uri(self):
		node_uri = self.request.options['node']
		return node_uri

	@property
	def node_name(self):
		node_name = uvmmd.Client._uri2name(self.node_uri)
		return node_name

	@property
	def node_name_short(self):
		node_short_name = uvmmd.Client._uri2name(self.node_uri, short=True)
		return node_short_name

	@property
	def node_info(self):
		try:
			return self._node_info
		except AttributeError, e:
			self._node_info = self.uvmm_client.get_node_info(self.node_uri)
			return self._node_info

	@property
	def domain_uuid(self):
		domain_uuid = self.request.options['domain']
		return domain_uuid

	@property
	def domain_info(self):
		try:
			return self._domain_info
		except AttributeError, e:
			self._node_info, self._domain_info = self.uvmm_client.get_domain_info_ext(self.node_uri, self.domain_uuid)
			return self._domain_info

	def __nonzero__(self):
		"""Return success status."""
		return self.node_tree is not None

	@staticmethod
	def __get_item_path(options, levels=LEVELS[1:]):
		"""Calculate /group/node/domain path."""
		path = ()
		for level_name in levels:
			try:
				path += (options[level_name],)
			except KeyError:
				break
		return path

	@staticmethod
	def button_create( text, icon, command, options, current ):
		"""Create button."""
		cmd = umcp.SimpleCommand(command, options=copy.copy(options))
		action = umcd.Action(cmd)
		highlight = current == TreeView.__get_item_path(options)

		link = umcd.LinkButton(text, icon, actions=[action], current=highlight, attributes={'class': 'umc_nowrap'})
		link.set_size(umct.SIZE_SMALL)
		return link

	@staticmethod
	def button_create_node(group_name, node_uri, node_is_off, current=None):
		node_name_short = uvmmd.Client._uri2name(node_uri, short=True)
		if node_uri.startswith('qemu'):
			icon = 'uvmm/node-kvm'
		elif node_uri.startswith('xen'):
			icon = 'uvmm/node-xen'
		else:
			icon = 'uvmm/node'
		if node_is_off:
			icon += '-off'

		options = {'group': group_name, 'node': node_uri}
		link = TreeView.button_create(node_name_short, icon, 'uvmm/node/overview', options, current)
		return link

	@staticmethod
	def button_create_domain(group_name, node_uri, node_is_off, domain_info, current=None):
		if node_is_off:
			icon = 'uvmm/domain-off'
		elif domain_info.state in (1, 2):
			icon = 'uvmm/domain-on'
		elif domain_info.state in (3,):
			icon = 'uvmm/domain-paused'
		else:
			icon = 'uvmm/domain'

		options = {'group': group_name, 'node': node_uri, 'domain': domain_info.uuid}
		link = TreeView.button_create(domain_info.name, icon, 'uvmm/domain/overview', options, current)
		return link

	def get_failure_response(self, exception=None):
		"""
		Return a response indicating an error in the last request to UVMMd.
		The exception is currently ignored.
		"""
		info_txt = _('The connection to the UCS Virtual Machine Manager service could not be established. Please verify that it is started. You may use the UMC service module therefor.')
		info_box = umcd.InfoBox(info_txt)

		table = umcd.SimpleTreeTable()
		table.set_tree_data([])
		table.set_dialog(info_box)

		res = umcp.Response(self.request)
		res.dialog = umcd.Dialog([table], attributes={'type': 'uvmm_frame'})
		return res

	def get_tree_response(self, level):
		"""
		Return a response containing a dialog with the TreeView.
		"""
		current = TreeView.LEVELS[1 : level + 1]
		current_path = TreeView.__get_item_path(self.request.options, current)

		table = self.get_tree(current=current_path)

		res = umcp.Response(self.request)
		res.dialog = umcd.Dialog([table], attributes={'type': 'uvmm_frame'})
		return res

	def get_tree(self, current):
		"""
		Create TreeView.
		'current' is a prefix of the n-tuple (group_name, node_uri, domain_uuid) of the currently selected item.
		Additionally fills in some 'missing' request.options-parameters from UVMMd-data.
		"""
		try:
			self.node_tree = node_tree = self.uvmm_client.get_node_tree()
		except uvmmd.UvmmError, e:
			raise

		tree_view = []
		for (group_name, node_infos) in sorted(node_tree.items(), key=lambda (group_name, node_infos): group_name):
			try:
				is_current_group = group_name == self.group_name
			except KeyError, e:
				is_current_group = False
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

			if TreeView.SHOW_LEVEL < TreeView.LEVEL_NODE:
				try:
					self._node_info = node_infos[self.node_uri]
					self.request.options.setdefault('group', group_name)
					self._domain_info = self._node_info.domains[self.domain_uuid]
					self.request.options.setdefault('domain_name', self._domain_info.name)
				except KeyError, e:
					pass
				continue

			for (node_uri, node_info) in sorted(node_infos.items(), key=lambda (node_uri, node_info): uvmmd.Client._uri2name(node_uri)): # sort by FQDN
				try:
					is_current_node = node_uri == self.node_uri
				except KeyError, e:
					is_current_node = False
				if is_current_node:
					# Fill in missing 'group' from UVMMd data
					self._node_info = node_info
					self.request.options.setdefault('group', group_name)

				node_name_short = uvmmd.Client._uri2name(node_uri, short=True)
				node_is_off = node_info.last_update < node_info.last_try

				link = TreeView.button_create_node(group_name, node_uri, node_is_off, current)
				group_view.append(link)

				domain_view = []
				group_view.append(domain_view)

				if not node_is_off:
					options = {'group': group_name, 'node': node_uri, 'domain': 'NONE'}
					link = TreeView.button_create(_('Add'), 'uvmm/add', 'uvmm/domain/create', options, current)
					domain_view.append(link)

				if TreeView.SHOW_LEVEL < TreeView.LEVEL_DOMAIN:
					if is_current_node:
						try:
							self._domain_info = node_info.domains[self.domain_uuid]
							self.request.options.setdefault('domain_name', self._domain_info.name)
						except KeyError, e:
							pass
					continue

				for (domain_uuid, domain_info) in sorted(node_info.domains.items(), key=lambda (domain_uuid, domain_info): domain_info.name):
					try:
						is_current_domain = is_current_node and domain_uuid == self.domain_uuid
					except KeyError, e:
						is_current_domain = False
					# Fill in missing 'domain_name' from UVMMd data
					if is_current_domain:
						self._domain_info = domain_info
						self.request.options.setdefault('domain_name', domain_info.name)

					if domain_info.name == 'Domain-0':
						continue
					link = TreeView.button_create_domain(group_name, node_uri, node_is_off, domain_info, current)
					domain_view.append(link)

		table = umcd.SimpleTreeTable(collapsible=TreeView.LEVEL_NODE)
		table.set_tree_data([tree_view]) # the extra nesting is important
		return table
