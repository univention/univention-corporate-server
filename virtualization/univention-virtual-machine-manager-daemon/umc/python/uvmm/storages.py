# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
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

import os

from univention.lib.i18n import Translation

from univention.management.console.modules import UMC_Error

from univention.uvmm.protocol import Disk
from univention.uvmm.storage import POOLS_RW

from urlparse import urldefrag

from .tools import object2dict

_ = Translation('univention-management-console-modules-uvmm').translate


class Storages(object):

	"""
	UMC functions for UVMM storage pool handling.
	"""

	def __init__(self):
		self.storage_pools = {}

	def storage_pool_query(self, request):
		"""
		Query function for storage pools.

		options: {
			'nodeURI': <node uri>,
			}

		return: [{
			'active': <boolean>,
			'available': <int: size in B>,
			'capacity': <int: size in B>,
			'name': <string: pool name>,
			'path': <string: directory>,
			'type': (dir|disk|fs|iscsi|logical|mpath|netfs|scsi|...),
			'uuid': <string: pool UUID>,
			}, ...]
		"""
		self.required_options(request, 'nodeURI')
		uri = request.options['nodeURI']
		if uri in self.storage_pools:
			self.finished(request.id, self.storage_pools[uri].values())
			return

		def _finished(data):
			"""
			Process asynchronous UVMM STORAGE_POOLS answer.
			"""
			self.storage_pools[uri] = dict([
				(pool.name, object2dict(pool))
				for pool in data
			])
			return self.storage_pools[uri].values()

		self.uvmm.send(
			'STORAGE_POOLS',
			self.process_uvmm_response(request, _finished),
			uri=uri
		)

	def storage_volume_query(self, request):
		"""
		Returns a list of volumes located in the given pool.

		options: {
			'nodeURI': <node uri>,
			'pool': <pool name>,
			['type': (disk|cdrom|floppy)],
			}

		return: [{
			'device': (cdrom|disk),
			'driver': None,
			'driver_cache': (default|...),
			'driver_type': (iso|raw|qcow2|...),
			'pool': <string: pool name>,
			'readonly': <boolean>,
			'size': <int: size in B>,
			'source': <string: path>,
			'volumeFilename': <string: base-filename>,
			'target_bus': None,
			'target_dev': '',
			'type': (file|block|...),
			}, ...]
		"""
		self.required_options(request, 'nodeURI', 'pool')

		def _finished(data):
			"""
			Process asynchronous UVMM STORAGE_VOLUMES answer.
			"""
			volume_list = []
			for vol in data:
				vol = object2dict(vol)
				vol['volumeFilename'] = os.path.basename(vol.get('source', ''))
				volume_list.append(vol)
			return volume_list

		drive_type = request.options.get('type', None)
		if drive_type == 'floppy':  # not yet supported
			drive_type = 'disk'
		self.uvmm.send(
			'STORAGE_VOLUMES',
			self.process_uvmm_response(request, _finished),
			uri=request.options['nodeURI'],
			pool=request.options['pool'],
			type=drive_type
		)

	def storage_volume_remove(self, request):
		"""
		Removes a list of volumes.

		options: {
			'nodeURI': <node uri>,
			'volumes': [{source: <file name>}, ...]
			}

		return:
		"""
		self.required_options(request, 'nodeURI', 'volumes')
		volume_list = [vol['source'] for vol in request.options['volumes']]
		self.uvmm.send(
			'STORAGE_VOLUMES_DESTROY',
			self.process_uvmm_response(request),
			uri=request.options['nodeURI'],
			volumes=volume_list
		)

	def storage_volume_deletable(self, request):
		"""
		Returns a list of domains that use the given volume.

		options: [{
			'domainURI': <domain URI>,
			'pool': <pool name>,
			'source': <file name>
			}, ...]

		return: [{
			'domainURI': <domain URI>,
			'pool': <pool name>,
			'source': <file name>
			'deletable': (True|False|None)
			}, ...]

		where 'deletebale' is
			True: disk can be deleted
			False: disk is shared and should not be deleted
			None: disk can not be deleted
		"""
		_tmp_cache = {}

		for volume in request.options:
			# safe default: not deletable
			volume['deletable'] = None

			node_uri, domain_uuid = urldefrag(volume['domainURI'])
			# Must be in a pool
			pool = self.get_pool(node_uri, volume['pool'])
			if not pool:
				continue
			# Pool must be modifiable
			if pool['type'] not in POOLS_RW:
				continue
			# Pool must be mapped to the file system
			pool_path = pool['path']
			if not pool_path:
				continue
			volume_path = volume['source']

			# check if volume is used by any other domain
			success, result = self.uvmm.send(
				'STORAGE_VOLUME_USEDBY',
				None,
				volume=volume_path
			)
			if not success:
				raise UMC_Error(
					_('Failed to check if the drive is used by any other virtual instance')
				)

			if len(result) > 1:  # is used by at least one other domain
				volume['deletable'] = False
				continue

			try:
				domain = _tmp_cache[volume['domainURI']]
			except LookupError:
				success, domain = self.uvmm.send(
					'DOMAIN_INFO',
					None,
					uri=node_uri,
					domain=domain_uuid
				)
				if not success:
					raise UMC_Error(
						_('Could not retrieve details for domain %s') % domain_uuid
					)
				_tmp_cache[volume['domainURI']] = domain

			drive = None
			for disk in domain.disks:
				if disk.source == volume_path:
					drive = disk
					break
			else:
				continue

			volume['deletable'] = drive.device == Disk.DEVICE_DISK

		self.finished(request.id, request.options)

	# helper functions

	def get_pool(self, node_uri, pool_name):
		"""
		Returns a pool object or None if the pool could not be found.
		"""
		try:
			pools = self.storage_pools[node_uri]
		except LookupError:
			success, data = self.uvmm.send(
				'STORAGE_POOLS',
				None,
				uri=node_uri
			)
			if not success:
				return None
			pools = dict([(pool.name, object2dict(pool)) for pool in data])
			self.storage_pools[node_uri] = pools
		return pools.get(pool_name)
