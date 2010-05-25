#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  UVMM commands
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA
"""UVMM commands

This module implements parsing the protocol packets, checking parameters for
validity and invoking the real implementation.
"""

import protocol
import node
import logging

logger = logging.getLogger('uvmmd.command')

class CommandError(Exception):
	"""Signal error during command execution."""
	pass

class _Commands:
	@staticmethod
	def NODE_ADD(server, request):
		"""Add node to watch list."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_ADD: uri != string: %s' % (request.uri,))
		logger.debug('NODE_ADD %s' % (request.uri,))

		try:
			node.node_add(request.uri)
		except node.NodeError, (msg):
			raise CommandError('NODE: %s' % (msg,))

	@staticmethod
	def NODE_REMOVE(server, request):
		"""Remove node from watch list."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_REMOVE: uri != string: %s' % (request.uri,))
		logger.debug('NODE_REMOVE %s' % (request.uri,))

		try:
			node.node_remove(request.uri)
		except node.NodeError, (msg):
			raise CommandError('NODE_REMOVE: %s' % (msg,))

	@staticmethod
	def NODE_QUERY(server, request):
		"""Get domain and storage-pool information from node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_QUERY: uri != string: %s' % (request.uri,))
		logger.debug('NODE_QUERY %s' % (request.uri,))

		try:
			local_data = node.node_query(request.uri)
			if local_data is None:
				raise CommandError('NODE_QUERY: unknown node %s' % (request.uri,))

			pkg_data = protocol.Data_Node()
			pkg_data.name = local_data.name
			pkg_data.phyMem = local_data.phyMem
			pkg_data.curMem = local_data.curMem
			pkg_data.maxMem = local_data.maxMem
			pkg_data.cpus = local_data.cpus
			pkg_data.cores = tuple(local_data.cores)
			pkg_data.storages = []
			for store in local_data.storages.values():
				store_data = protocol.Data_StoragePool()
				store_data.uuid = store.uuid
				store_data.name = store.name
				store_data.capacity = store.capacity
				store_data.available = store.available
				pkg_data.storages.append(store_data)
			pkg_data.domains = []
			for domain in local_data.domains.values():
				domain_data = protocol.Data_Domain()
				domain_data.uuid = domain.uuid
				domain_data.name = domain.name
				domain_data.os = domain.os
				domain_data.kernel = domain.kernel
				domain_data.cmdline = domain.cmdline
				domain_data.state = domain.state
				domain_data.maxMem = domain.maxMem
				domain_data.curMem = domain.curMem
				domain_data.vcpus = domain.vcpus
				domain_data.cputime = tuple(domain.cputime)
				domain_data.interfaces = domain.interfaces
				domain_data.disks = domain.disks
				domain_data.graphics = domain.graphics
				pkg_data.domains.append(domain_data)
			pkg_data.capabilities = local_data.capabilities

			res = protocol.Response_DUMP()
			res.data = pkg_data
			return res
		except node.NodeError, (msg):
			raise CommandError('NODE_QUERY: %s' % (msg,))

	@staticmethod
	def NODE_FREQUENCY(server, request):
		"""Set polling interval for node."""
		try:
			hz = int(request.hz)
		except TypeError:
			raise CommandError('NODE_FREQUENCY: hz != int: %s' % (request.hz,))
		if request.uri != None and not isinstance(request.uri, basestring):
			raise CommandError('NODE_FREQUENCY: uri != string: %s' % (request.uri,))
		logger.debug('NODE_FREQUENCY %d %s' % (hz,request.uri))
		try:
			node.node_frequency(hz, request.uri)
		except node.NodeError, (msg):
			raise CommandError('NODE_FREQUENCY: %s' % (msg,))

	@staticmethod
	def NODE_LIST(server, request):
		"""Return list of nodes in group."""
		if not isinstance(request.group, basestring):
			raise CommandError('NODE_LIST: group != string: %s' % (request.group,))
		logger.debug('NODE_LIST')
		try:
			res = protocol.Response_DUMP()
			res.data = node.node_list(request.group)
			return res
		except node.NodeError, (msg):
			raise CommandError('NODE_LIST: %s' % (msg,))

	@staticmethod
	def GROUP_LIST(server, request):
		"""Return list of known groups."""
		logger.debug('GROUP_LIST')
		try:
			res = protocol.Response_DUMP()
			res.data = node.group_list()
			return res
		except node.NodeError, (msg):
			raise CommandError('GROUP_LIST: %s' % (msg,))

	@staticmethod
	def BYE(server, request):
		"""Terminate UVMM daemon."""
		logger.debug('BYE')
		server.eos = True

	@staticmethod
	def DOMAIN_DEFINE(server, request):
		"""Define new domain on node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_DEFINE: uri != string: %s' % (request.uri,))
		if not isinstance(request.domain, protocol.Data_Domain):
			raise CommandError('DOMAIN_DEFINE: definition != Domain: %s' % (request.domain,))
		logger.debug('DOMAIN_DEFINE %s %s' % (request.uri, request.domain))
		try:
			node.domain_define(request.uri, request.domain)
		except node.NodeError, (msg):
			raise CommandError('NODE_DEFINE: %s' % (msg,))

	@staticmethod
	def DOMAIN_STATE(server, request):
		"""Change running state of domain on node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_STATE: uri != string: %s' % (request.uri,))
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_STATE: domain != string: %s' % (request.domain,))
		if not request.state in ('RUN', 'PAUSE', 'SHUTDOWN', 'RESTART'):
			raise CommandError('DOMAIN_STATE: unsupported state: %s' % (request.state,))
		logger.debug('DOMAIN_STATE %s#%s %s' % (request.uri, request.domain, request.state))
		try:
			node.domain_state(request.uri, request.domain, request.state)
		except node.NodeError, (msg):
			raise CommandError('DOMAIN_STATE: %s' % (msg,))

	@staticmethod
	def DOMAIN_SAVE(server, request):
		"""Save defined domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_STATE: uri != string: %s' % (request.uri,))
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_STATE: domain != string: %s' % (request.domain,))
		if not isinstance(request.statefile, basestring):
			raise CommandError('DOMAIN_STATE: statefile != string: %s' % (request.statefile,))
		logger.debug('DOMAIN_SAVE %s#%s %s' % (request.uri, request.domain, request.statefile))
		try:
			node.domain_save(request.uri, request.domain, request.statefile)
		except node.NodeError, (msg):
			raise CommandError('DOMAIN_SAVE: %s' % (msg,))

	@staticmethod
	def DOMAIN_RESTORE(server, request):
		"""Restore defined domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_STATE: uri != string: %s' % (request.uri,))
		if not isinstance(request.statefile, basestring):
			raise CommandError('DOMAIN_STATE: statefile != string: %s' % (request.statefile,))
		logger.debug('DOMAIN_SAVE %s %s' % (request.uri, request.statefile))
		try:
			node.domain_restore(request.uri, request.statefile)
		except node.NodeError, (msg):
			raise CommandError('DOMAIN_RESTORE: %s' % (msg,))

	@staticmethod
	def DOMAIN_UNDEFINE(server, request):
		"""Undefine a domain on a node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_UNDEFINE: uri != string: %s' % (request.uri,))
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_UNDEFINE: domain != string: %s' % (request.domain,))
		if not isinstance(request.volumes, (list, tuple)):
			raise CommandError('DOMAIN_UNDEFINE: volumes != list: %s' % (request.volumes,))
		for vol in request.volumes:
			if not isinstance(vol, basestring):
				raise CommandError('DOMAIN_UNDEFINE: volumes[] != string: %s' % (vol,))
		logger.debug('DOMAIN_UNDEFINE %s#%s [%s]' % (request.uri, request.domain, ','.join(request.volumes)))
		try:
			node.domain_undefine(request.uri, request.domain, request.volumes)
		except node.NodeError, (msg):
			raise CommandError('DOMAIN_UNDEFINE: %s' % (msg,))

	@staticmethod
	def DOMAIN_MIGRATE(server, request):
		"""Migrate a domain from node to the target node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_MIGRATE: uri != string: %s' % (request.uri,))
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_MIGRATE: domain != string: %s' % (request.domain,))
		if not isinstance(request.target_uri, basestring):
			raise CommandError('DOMAIN_MIGRATE: target_uri != string: %s' % (request.target_uri,))
		logger.debug('DOMAIN_MIGRATE %s#%s %s' % (request.uri, request.domain, request.target_uri))
		try:
			node.domain_migrate(request.uri, request.domain, request.target_uri)
		except node.NodeError, (msg):
			raise CommandError('DOMAIN_MIGRATE: %s' % (msg,))

	def __getitem__(self, cmd):
		if cmd.startswith('_'):
			raise CommandError('Command is restricted.')
		return getattr(self, cmd)

commands = _Commands()
