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

from datetime import datetime
from urlparse import urldefrag

from univention.lib.i18n import Translation


_ = Translation('univention-management-console-modules-uvmm').translate


class Snapshots(object):

	"""
	UMC functions for UVMM snapshot handling.
	"""

	def snapshot_query(self, request):
		"""
		Returns a list of snapshots of a domain

		options: {'domainURI': <domain URI>}

		return: [{
			'id': <string: snapshot name>,
			'label': <string: snapshot name>,
			'time': <string: creation time as ISO>,
			}, ...]
		"""
		self.required_options(request, 'domainURI')

		def _finished(data):
			"""
			Process asynchronous UVMM DOMAIN_INFO answer.
			"""
			snapshot_list = []
			if data.snapshots is not None:
				for name, info in data.snapshots.items():
					creation = datetime.fromtimestamp(info.ctime)
					snapshot = {
						'id': name,
						'label': name,
						'time': creation.isoformat(' '),
					}
					snapshot_list.append(snapshot)
			return snapshot_list

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_INFO',
			self.process_uvmm_response(request, _finished),
			uri=node_uri,
			domain=domain_uuid
		)

	def snapshot_create(self, request):
		"""
		Create a snapshot for a domain

		options: {
			'domainURI': <domain URI>,
			'snapshotName': <snapshot name>,
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'snapshotName')

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_SNAPSHOT_CREATE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			snapshot=request.options['snapshotName']
		)

	def snapshot_remove(self, request):
		"""
		Returns a list of snapshots of a domain

		options: {
			'domainURI': <domain URI>,
			'snapshotName': <snapshot name>,
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'snapshotName')

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_SNAPSHOT_DELETE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			snapshot=request.options['snapshotName']
		)

	def snapshot_revert(self, request):
		"""
		Returns a list of snapshots of a domain

		options: {
			'domainURI': <domain URI>,
			'snapshotName': <snapshot name>,
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'snapshotName')

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_SNAPSHOT_REVERT',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			snapshot=request.options['snapshotName']
		)
