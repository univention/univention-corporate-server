# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2017-2019 Univention GmbH
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

from urlparse import urldefrag

from univention.lib.i18n import Translation


_ = Translation('univention-management-console-modules-uvmm').translate


class Targethosts(object):

	"""
	UMC functions for UVMM migration target hosts handling.
	"""

	def targethost_query(self, request):
		"""
		Returns a list of migration target hosts of a domain

		options: {'domainURI': <domain URI>}

		return: [{
			'id': <string: id>,
			'label': <string: targethost name>,
			}, ...]
		"""
		self.required_options(request, 'domainURI')

		def _finished(data):
			"""
			Process asynchronous UVMM DOMAIN_INFO answer.
			"""
			targethost_list = []
			if data.targethosts is not None:
				for name in data.targethosts:
					targethost = {
						'id': name,
						'label': name,
					}
					targethost_list.append(targethost)

			return targethost_list

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_INFO',
			self.process_uvmm_response(request, _finished),
			uri=node_uri,
			domain=domain_uuid
		)

	def targethost_add(self, request):
		"""
		Add a migration targethost for a domain

		options: {
			'domainURI': <domain URI>,
			'targethostName': <targethost name>,
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'targethostName')

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_TARGETHOST_ADD',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			targethost=request.options['targethostName']
		)

	def targethost_remove(self, request):
		"""
		Remove a targethost from a domain

		options: {
			'domainURI': <domain URI>,
			'targethostName': <targethost name>,
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'targethostName')

		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_TARGETHOST_REMOVE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			targethost=request.options['targethostName']
		)
