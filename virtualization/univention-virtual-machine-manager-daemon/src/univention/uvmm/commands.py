# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  UVMM commands
#
# Copyright 2010-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
"""UVMM commands

This module implements parsing the protocol packets, checking parameters for
validity and invoking the real implementation.
"""
from __future__ import absolute_import
import copy

from . import protocol
from . import node
from . import cloudnode
from . import storage
import logging
from .helpers import TranslatableException, N_ as _

logger = logging.getLogger('uvmmd.command')


class CommandError(TranslatableException):

	"""Signal error during command execution."""

	def __init__(self, command, ex, **kv):
		kv['command'] = command
		TranslatableException.__init__(self, ex, kv)


class _Commands(object):

	@staticmethod
	def L_CLOUD_ADD(server, request):
		""" Add cloud via libcloud """
		if not isinstance(request.args, dict):
			raise CommandError('L_CLOUD_ADD', _('args != dict: %(args)s'), args=request.args)

		if not isinstance(request.testconnection, bool):
			raise CommandError('L_CLOUD_ADD', _('testconnection is not a bool %(testconnection)s'), testconnection=request.testconnection)

		logger.debug('L_CLOUD_ADD %s, testconnection: %s', request.args, request.testconnection)
		try:
			cloudnode.cloudconnections.add_connection(request.args, request.testconnection)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_ADD', ex)

	@staticmethod
	def L_CLOUD_REMOVE(server, request):
		""" Remove cloud via libcloud """
		if not isinstance(request.name, basestring):
			raise CommandError('L_CLOUD_REMOVE', _('name != string: %(name)s'), name=request.name)

		logger.debug('L_CLOUD_REMOVE %s', request.name)
		try:
			cloudnode.cloudconnections.remove_connection(request.name)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_REMOVE', ex)

	@staticmethod
	def L_CLOUD_LIST(server, request):
		""" List connected clouds """
		logger.debug('L_CLOUD_LIST')
		if not isinstance(request.pattern, basestring):
			raise CommandError('L_CLOUD_LIST', _('pattern != string: %(pattern)s'), pattern=request.pattern)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list(request.pattern)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_LIST', ex)

	@staticmethod
	def L_CLOUD_INSTANCE_LIST(server, request):
		""" List instances in connected clouds """
		logger.debug('L_CLOUD_INSTANCE_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_INSTANCE_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		if not isinstance(request.pattern, basestring):
			raise CommandError('L_CLOUD_INSTANCE_LIST', _('pattern != string: %(pattern)s'), pattern=request.pattern)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_instances(request.conn_name, request.pattern)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_INSTANCE_LIST', ex)

	@staticmethod
	def L_CLOUD_FREQUENCY(server, request):
		"""Set polling interval for cloud connection"""
		try:
			freq = int(request.freq)
		except TypeError:
			raise CommandError('L_CLOUD_FREQUENCY', _('freq != int: %(freq)s'), freq=request.freq)
		if request.name is not None and not isinstance(request.name, basestring):
			raise CommandError('L_CLOUD_FREQUENCY', _('name != string: %(name)s'), name=request.name)
		logger.debug('L_CLOUD_FREQUENCY %d %s', freq, request.name)
		try:
			cloudnode.cloudconnections.set_poll_frequency(freq, request.name)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_FREQUENCY', ex)

	@staticmethod
	def L_CLOUD_IMAGE_LIST(server, request):
		"""List available cloud instance images of cloud connections"""
		logger.debug('L_CLOUD_IMAGE_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_IMAGE_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)

		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_images(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_IMAGE_LIST', ex)

	@staticmethod
	def L_CLOUD_SIZE_LIST(server, request):
		"""List available cloud instance sizes of cloud connections"""
		logger.debug('L_CLOUD_SIZE_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_SIZE_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_sizes(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_SIZE_LIST', ex)

	@staticmethod
	def L_CLOUD_LOCATION_LIST(server, request):
		"""List available cloud locations of cloud connections"""
		logger.debug('L_CLOUD_LOCATION_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_LOCATION_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_locations(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_LOCATION_LIST', ex)

	@staticmethod
	def L_CLOUD_KEYPAIR_LIST(server, request):
		"""List available cloud keypairs of cloud connections"""
		logger.debug('L_CLOUD_KEYPAIR_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_KEYPAIR_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_keypairs(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_KEYPAIR_LIST', ex)

	@staticmethod
	def L_CLOUD_SECGROUP_LIST(server, request):
		"""List available cloud security groups of cloud connections"""
		logger.debug('L_CLOUD_SECGROUP_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_SECGROUP_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_secgroups(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_SECGROUPS_LIST', ex)

	@staticmethod
	def L_CLOUD_NETWORK_LIST(server, request):
		"""List available cloud networks of cloud connections"""
		logger.debug('L_CLOUD_NETWORK_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_NETWORK_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_networks(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_NETWORK_LIST', ex)

	@staticmethod
	def L_CLOUD_SUBNET_LIST(server, request):
		"""List available cloud subnets of cloud connections"""
		logger.debug('L_CLOUD_SUBNET_LIST')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_SUBNET_LIST', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		try:
			res = protocol.Response_DUMP()
			res.data = cloudnode.cloudconnections.list_conn_subnets(request.conn_name)
			return res
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_SUBNET_LIST', ex)

	@staticmethod
	def L_CLOUD_INSTANCE_STATE(server, request):
		"""Change instance state"""
		logger.debug('L_CLOUD_INSTANCE_STATE')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_INSTANCE_STATE', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		if not isinstance(request.instance_id, basestring):
			raise CommandError('L_CLOUD_INSTANCE_STATE', _('instance_id != string: %(instance_id)s'), instance_id=request.instance_id)
		if request.state not in ('RUN', 'PAUSE', 'SHUTDOWN', 'SHUTOFF', 'SOFTRESTART', 'RESTART', 'SUSPEND'):
			raise CommandError('L_CLOUD_INSTANCE_STATE', _('unsupported state: %(state)s'), state=request.state)
		try:
			cloudnode.cloudconnections.instance_state(request.conn_name, request.instance_id, request.state)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_INSTANCE_STATE', ex)

	@staticmethod
	def L_CLOUD_INSTANCE_TERMINATE(server, request):
		"""Terminate a cloud instance"""
		logger.debug('L_CLOUD_INSTANCE_TERMINATE')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_INSTANCE_TERMINATE', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		if not isinstance(request.instance_id, basestring):
			raise CommandError('L_CLOUD_INSTANCE_TERMINATE', _('instance_id != string: %(instance_id)s'), instance_id=request.instance_id)
		try:
			cloudnode.cloudconnections.instance_terminate(request.conn_name, request.instance_id)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_INSTANCE_TERMINATE', ex)

	@staticmethod
	def L_CLOUD_INSTANCE_CREATE(server, request):
		"""Create a new cloud instance"""
		logger.debug('L_CLOUD_INSTANCE_CREATE')
		if not isinstance(request.conn_name, basestring):
			raise CommandError('L_CLOUD_INSTANCE_CREATE', _('conn_name != string: %(conn_name)s'), conn_name=request.conn_name)
		if not isinstance(request.args, dict):
			raise CommandError('L_CLOUD_INSTANCE_CREATE', _('args != dict: %(args)s'), agrs=request.args)
		try:
			cloudnode.cloudconnections.instance_create(request.conn_name, request.args)
		except cloudnode.CloudConnectionError as ex:
			raise CommandError('L_CLOUD_INSTANCE_CREATE', ex)

	@staticmethod
	def NODE_ADD(server, request):
		"""Add node to watch list."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_ADD', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('NODE_ADD %s', request.uri)

		try:
			node.node_add(request.uri)
		except node.NodeError as ex:
			raise CommandError('NODE_ADD', ex)

	@staticmethod
	def NODE_REMOVE(server, request):
		"""Remove node from watch list."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_REMOVE', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('NODE_REMOVE %s', request.uri)

		try:
			node.node_remove(request.uri)
		except node.NodeError as ex:
			raise CommandError('NODE_REMOVE', ex)

	@staticmethod
	def NODE_QUERY(server, request):
		"""Get domain and storage-pool information from node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('NODE_QUERY', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('NODE_QUERY %s', request.uri)

		try:
			local_data = node.node_query(request.uri)
			if local_data is None:
				raise CommandError('NODE_QUERY', _('unknown node %(uri)s'), uri=request.uri)

			pkg_data = copy.copy(local_data.pd)
			pkg_data.domains = [d.pd for d in local_data.domains.values()]

			res = protocol.Response_DUMP()
			res.data = pkg_data
			return res
		except node.NodeError as ex:
			raise CommandError('NODE_QUERY', ex)

	@staticmethod
	def NODE_FREQUENCY(server, request):
		"""Set polling interval for node."""
		try:
			hz = int(request.hz)
		except TypeError:
			raise CommandError('NODE_FREQUENCY', _('hz != int: %(hz)s'), hz=request.hz)
		if request.uri is not None and not isinstance(request.uri, basestring):
			raise CommandError('NODE_FREQUENCY', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('NODE_FREQUENCY %d %s', hz, request.uri)
		try:
			node.node_frequency(hz, request.uri)
		except node.NodeError as ex:
			raise CommandError('NODE_FREQUENCY', ex)

	@staticmethod
	def NODE_LIST(server, request):
		"""Return list of nodes in group."""
		if not isinstance(request.group, basestring):
			raise CommandError('NODE_LIST', _('group != string: %(group)s'), group=request.group)
		if not isinstance(request.pattern, basestring):
			raise CommandError('NODE_LIST', _('pattern != string: %(pattern)s'), pattern=request.pattern)
		logger.debug('NODE_LIST')
		try:
			res = protocol.Response_DUMP()
			res.data = node.node_list(request.group, request.pattern)
			return res
		except node.NodeError as ex:
			raise CommandError('NODE_LIST', ex)

	@staticmethod
	def GROUP_LIST(server, request):
		"""Return list of known groups."""
		logger.debug('GROUP_LIST')
		try:
			res = protocol.Response_DUMP()
			res.data = node.group_list()
			return res
		except node.NodeError as ex:
			raise CommandError('GROUP_LIST', ex)

	@staticmethod
	def BYE(server, request):
		"""Terminate UVMM daemon."""
		logger.debug('BYE')
		server.eos = True

	@staticmethod
	def DOMAIN_LIST(server, request):
		"""Return a list of available domains of a given node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_LIST', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.pattern, basestring):
			raise CommandError('DOMAIN_LIST', _('pattern != string: %(pattern)s'), pattern=request.pattern)

		logger.debug('DOMAIN_LIST %s %s', request.uri, request.pattern)
		try:
			domains = node.domain_list(request.uri, request.pattern)
			res = protocol.Response_DUMP()
			res.data = domains
			return res
		except node.NodeError as ex:
			raise CommandError('DOMAIN_LIST', ex)

	@staticmethod
	def DOMAIN_INFO(server, request):
		"""Return detailed information about a domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_INFO', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_INFO', _('domain != string: %(domain)s'), domain=request.domain)

		logger.debug('DOMAIN_INFO %s %s', request.uri, request.domain)
		try:
			domain_info = node.domain_info(request.uri, request.domain)
			res = protocol.Response_DUMP()
			res.data = domain_info
			return res
		except node.NodeError as ex:
			raise CommandError('DOMAIN_INFO', ex)

	@staticmethod
	def DOMAIN_DEFINE(server, request):
		"""Define new domain on node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_DEFINE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, protocol.Data_Domain):
			raise CommandError('DOMAIN_DEFINE', _('definition != Domain: %(domain)s'), domain=request.domain)
		logger.debug('DOMAIN_DEFINE %s %s', request.uri, request.domain)
		try:
			uuid, warnings = node.domain_define(request.uri, request.domain)
			res = protocol.Response_DUMP()
			res.data = uuid
			res.messages = warnings
			return res
		except node.NodeError as ex:
			raise CommandError('DOMAIN_DEFINE', ex)

	@staticmethod
	def DOMAIN_STATE(server, request):
		"""Change running state of domain on node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_STATE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_STATE', _('domain != string: %(domain)s'), domain=request.domain)
		if request.state not in ('RUN', 'PAUSE', 'SHUTDOWN', 'SHUTOFF', 'RESTART', 'SUSPEND'):
			raise CommandError('DOMAIN_STATE', _('unsupported state: %(state)s'), state=request.state)
		logger.debug('DOMAIN_STATE %s#%s %s', request.uri, request.domain, request.state)
		try:
			node.domain_state(request.uri, request.domain, request.state)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_STATE', ex)

	@staticmethod
	def DOMAIN_SAVE(server, request):
		"""Save defined domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_SAVE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_SAVE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.statefile, basestring):
			raise CommandError('DOMAIN_SAVE', _('statefile != string: %(file)s'), file=request.statefile)
		logger.debug('DOMAIN_SAVE %s#%s %s', request.uri, request.domain, request.statefile)
		try:
			node.domain_save(request.uri, request.domain, request.statefile)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_SAVE', ex)

	@staticmethod
	def DOMAIN_RESTORE(server, request):
		"""Restore defined domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_RESTORE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_RESTORE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.statefile, basestring):
			raise CommandError('DOMAIN_RESTORE', _('statefile != string: %(file)s'), file=request.statefile)
		logger.debug('DOMAIN_RESTORE %s %s', request.uri, request.statefile)
		try:
			node.domain_restore(request.uri, request.domain, request.statefile)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_RESTORE', ex)

	@staticmethod
	def DOMAIN_UNDEFINE(server, request):
		"""Undefine a domain on a node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_UNDEFINE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_UNDEFINE', _('domain != string: %(domain)s'), domain=request.domain)
		if request.volumes is not None and not isinstance(request.volumes, (list, tuple)):
			raise CommandError('DOMAIN_UNDEFINE', _('volumes != list or None: %(volumes)s'), volumes=request.volumes)
		if request.volumes is not None:
			for vol in request.volumes:
				if not isinstance(vol, basestring):
					raise CommandError('DOMAIN_UNDEFINE', _('volumes[] != string: %(volume)s'), volume=vol)
			logger.debug('DOMAIN_UNDEFINE %s#%s [%s]', request.uri, request.domain, ','.join(request.volumes))
		else:
			logger.debug('DOMAIN_UNDEFINE %s#%s None (-> all volumes will be removed)', request.uri, request.domain)
		try:
			node.domain_undefine(request.uri, request.domain, request.volumes)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_UNDEFINE', ex)

	@staticmethod
	def DOMAIN_MIGRATE(server, request):
		"""Migrate a domain from node to the target node."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_MIGRATE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_MIGRATE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.target_uri, basestring):
			raise CommandError('DOMAIN_MIGRATE', _('target_uri != string: %(uri)s'), uri=request.target_uri)
		if not isinstance(request.mode, int):
			raise CommandError('DOMAIN_MIGRATE', _('mode != int: %(mode)s'), mode=request.mode)
		logger.debug('DOMAIN_MIGRATE %s#%s %s %d', request.uri, request.domain, request.target_uri, request.mode)
		try:
			node.domain_migrate(request.uri, request.domain, request.target_uri, request.mode)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_MIGRATE', ex)

	@staticmethod
	def DOMAIN_SNAPSHOT_CREATE(server, request):
		"""Create new snapshot of domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_CREATE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_CREATE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.snapshot, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_CREATE', _('snapshot != string: %(snapshot)s'), snapshot=request.snapshot)
		logger.debug('DOMAIN_SNAPSHOT_CREATE %s#%s %s', request.uri, request.domain, request.snapshot)
		try:
			node.domain_snapshot_create(request.uri, request.domain, request.snapshot)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_SNAPSHOT_CREATE', ex)

	@staticmethod
	def DOMAIN_SNAPSHOT_REVERT(server, request):
		"""Revert to snapshot of domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_REVERT', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_REVERT', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.snapshot, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_REVERT', _('snapshot != string: %(snapshot)s'), snapshot=request.snapshot)
		logger.debug('DOMAIN_SNAPSHOT_REVERT %s#%s %s', request.uri, request.domain, request.snapshot)
		try:
			node.domain_snapshot_revert(request.uri, request.domain, request.snapshot)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_SNAPSHOT_REVERT', ex)

	@staticmethod
	def DOMAIN_SNAPSHOT_DELETE(server, request):
		"""Delete snapshot of domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_DELETE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_DELETE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.snapshot, basestring):
			raise CommandError('DOMAIN_SNAPSHOT_DELETE', _('snapshot != string: %(snapshot)s'), snapshot=request.snapshot)
		logger.debug('DOMAIN_SNAPSHOT_DELETE %s#%s %s', request.uri, request.domain, request.snapshot)
		try:
			node.domain_snapshot_delete(request.uri, request.domain, request.snapshot)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_SNAPSHOT_DELETE', ex)

	@staticmethod
	def DOMAIN_UPDATE(server, request):
		"""Trigger update of domain."""
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_UPDATE', _('domain != string: %(domain)s'), domain=request.domain)
		logger.debug('DOMAIN_UPDATE %s' % request.domain)
		try:
			node.domain_update(request.domain)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_UPDATE', ex)

	@staticmethod
	def DOMAIN_CLONE(server, request):
		"""Clone a domain."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_CLONE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_CLONE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.name, basestring):
			raise CommandError('DOMAIN_CLONE', _('name != string: %(name)s'), name=request.name)
		if not isinstance(request.subst, dict):
			raise CommandError('DOMAIN_CLONE', _('subst != dict: %(subst)s'), subst=request.subst)
		for key, value in request.subst.items():
			if not isinstance(key, basestring):
				raise CommandError('DOMAIN_CLONE', _('subst[] != string: %(subst)s'), subst=key)
			if not (value is None or isinstance(value, basestring)):
				raise CommandError('DOMAIN_CLONE', _('subst[] != string: %(subst)s'), subst=value)
		logger.debug('DOMAIN_CLONE %s#%s %s %r', request.uri, request.domain, request.name, request.subst)
		try:
			uuid, warnings = node.domain_clone(request.uri, request.domain, request.name, request.subst)
			res = protocol.Response_DUMP()
			res.data = uuid
			res.messages = warnings
			return res
		except node.NodeError as ex:
			raise CommandError('DOMAIN_CLONE', ex)

	@staticmethod
	def DOMAIN_TARGETHOST_ADD(server, request):
		"""Add a migration target host."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_TARGETHOST_ADD', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_TARGETHOST_ADD', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.targethost, basestring):
			raise CommandError('DOMAIN_TARGETHOST_ADD', _('targethost != string: %(targethost)s'), domain=request.targethost)
		logger.debug('DOMAIN_TARGETHOST_ADD %s: add %s', request.domain, request.targethost)
		try:
			node.domain_targethost_add(request.uri, request.domain, request.targethost)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_TARGETHOST_ADD', ex)

	@staticmethod
	def DOMAIN_TARGETHOST_REMOVE(server, request):
		"""Remove a migration target host."""
		if not isinstance(request.uri, basestring):
			raise CommandError('DOMAIN_TARGETHOST_REMOVE', _('uri != string: %(uri)s'), uri=request.uri)
		if not isinstance(request.domain, basestring):
			raise CommandError('DOMAIN_TARGETHOST_REMOVE', _('domain != string: %(domain)s'), domain=request.domain)
		if not isinstance(request.targethost, basestring):
			raise CommandError('DOMAIN_TARGETHOST_REMOVE', _('targethost != string: %(targethost)s'), domain=request.targethost)
		logger.debug('DOMAIN_TARGETHOST_REMOVE %s: remove %s', request.domain, request.targethost)
		try:
			node.domain_targethost_remove(request.uri, request.domain, request.targethost)
		except node.NodeError as ex:
			raise CommandError('DOMAIN_TARGETHOST_REMOVE', ex)

	@staticmethod
	def STORAGE_POOLS(server, request):
		"""List all pools."""
		if not isinstance(request.uri, basestring):
			raise CommandError('STORAGE_POOLS', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('STORAGE_POOLS %s', request.uri)
		try:
			node_stat = node.node_query(request.uri)
			pools = storage.storage_pools(node_stat)
			res = protocol.Response_DUMP()
			res.data = pools
			return res
		except node.NodeError as ex:
			raise CommandError('STORAGE_POOLS', ex)

	@staticmethod
	def STORAGE_VOLUMES(server, request):
		"""List all volumes in a pool."""
		if not isinstance(request.uri, basestring):
			raise CommandError('STORAGE_VOLUMES', _('uri != string: %(uri)s'), uri=request.uri)
		logger.debug('STORAGE_VOLUMES %s]' % request.uri)
		try:
			node_stat = node.node_query(request.uri)
			volumes = storage.get_storage_volumes(node_stat, request.pool, request.type)
			res = protocol.Response_DUMP()
			res.data = volumes
			return res
		except node.NodeError as ex:
			raise CommandError('STORAGE_VOLUMES', ex)
		except storage.StorageError as ex:
			raise CommandError('STORAGE_VOLUMES', ex)

	@staticmethod
	def STORAGE_VOLUMES_DESTROY(server, request):
		"""Destroy all given volumes in a pool."""
		if not isinstance(request.uri, basestring):
			raise CommandError('STORAGE_VOLUMES_DESTROY', _('uri != string: %(uri)s'), uri=request.uri)
		for vol in request.volumes:
			if not isinstance(vol, basestring):
				raise CommandError('STORAGE_VOLUMES_DESTROY', _('volumes[] != string: %(volume)s'), volume=vol)
		logger.debug('STORAGE_VOLUMES_DESTROY %s]' % request.uri)
		try:
			n = node.node_query(request.uri)
			storage.destroy_storage_volumes(n.conn, request.volumes, ignore_error=True)
			res = protocol.Response_OK()
			return res
		except node.NodeError as ex:
			raise CommandError('STORAGE_VOLUMES_DESTROY', ex)

	@staticmethod
	def STORAGE_VOLUME_USEDBY(server, request):
		"""Return list of domains using the given volume."""
		if not isinstance(request.volume, basestring):
			raise CommandError('STORAGE_VOLUME_USEDBY', _('volume != string: %(volume)s'), volume=request.volume)
		logger.debug('STORAGE_VOLUME_USEDBY %s]' % request.volume)
		res = protocol.Response_DUMP()
		res.data = storage.storage_volume_usedby(node.nodes, request.volume)
		return res

	def __getitem__(self, cmd):
		if cmd.startswith('_'):
			raise CommandError(cmd, _('Command "%(command)s" is restricted'))
		try:
			return getattr(self, cmd)
		except AttributeError:
			raise CommandError(cmd, _('Unknown command "%(command)s"'))


commands = _Commands()
