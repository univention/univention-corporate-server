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

import sys

from univention.lib.i18n import Translation
from univention.management.console.modules import Base, UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import ChoicesSanitizer, StringSanitizer

from notifier import Callback

from univention.management.console.modules.uvmm.uvmmd import UVMM_RequestBroker
from univention.management.console.modules.uvmm.nodes import Nodes
from univention.management.console.modules.uvmm.profiles import Profiles
from univention.management.console.modules.uvmm.storages import Storages
from univention.management.console.modules.uvmm.domains import Domains
from univention.management.console.modules.uvmm.snapshots import Snapshots
from univention.management.console.modules.uvmm.cloud import Cloud
from univention.management.console.modules.uvmm.targethosts import Targethosts

_ = Translation('univention-management-console-modules-uvmm').translate


class Instance(Base, Nodes, Profiles, Storages, Domains, Snapshots, Cloud, Targethosts):

	"""
	UMC functions for UVMM handling.
	"""

	def __init__(self):
		Base.__init__(self)
		Storages.__init__(self)
		self.uvmm = UVMM_RequestBroker()

	def init(self):
		"""
		Initialize UVMM UMC module instance.
		"""
		self.read_profiles()

	def process_uvmm_response(self, request, callback=None):
		return Callback(self._process_uvmm_response, request, callback)

	def _process_uvmm_response(self, thread, result, request, callback=None):
		# this is a notifier thread callback. If this raises an exception the whole module process crashes!
		if isinstance(result, BaseException):
			self.thread_finished_callback(thread, result, request)
			return

		success, data = result
		MODULE.info('Got result from UVMMd: success: %s, data: %r' % (success, data))
		if not success:
			try:
				raise UMC_Error(str(data), status=500)
			except UMC_Error as result:
				thread._exc_info = sys.exc_info()
				self.thread_finished_callback(thread, result, request)
			return

		if callback:
			try:
				data = callback(data)
			except BaseException as result:
				thread._exc_info = sys.exc_info()
				self.thread_finished_callback(thread, result, request)
				return

		self.finished(request.id, data)

	@sanitize(
		type=ChoicesSanitizer(['group', 'node', 'domain', 'cloud', 'instance', 'targethost'], required=True),
		nodePattern=StringSanitizer(required=True),
		domainPattern=StringSanitizer(required=False),
	)
	def query(self, request):
		"""
		Meta query function for groups, nodes and domains.

		return: {
			'success': (True|False),
			'message': <details>
			}
		"""

		def group_root(request):
			self.finished(request.id, [{
				'id': 'default',
				'label': _('Physical servers'),
				'type': 'group',
				'icon': 'uvmm-group',
			}])
		method = {
			'node': self.node_query,
			'domain': self.domain_query,
			'cloud': self.cloud_query,
			'instance': self.instance_query,
			'group': group_root,
			'targethost': self.targethost_query,
		}[request.options['type']]
		return method(request)

	def group_query(self, request):
		"""
		Get server groups.
		"""
		self.uvmm.send('GROUP_LIST', self.process_uvmm_response(request))
