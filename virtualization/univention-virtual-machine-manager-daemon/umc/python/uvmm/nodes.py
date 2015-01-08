# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UVMM node commands
#
# Copyright 2010-2015 Univention GmbH
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

from univention.lib.i18n import Translation

from univention.management.console.protocol.definitions import MODULE_ERR_COMMAND_FAILED
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import SearchSanitizer

from urlparse import urlsplit
from notifier import Callback

_ = Translation('univention-management-console-modules-uvmm').translate

class Nodes(object):
	"""
	UMC functions for UVMM node handling.
	"""

	def _node_thread_finished(self, thread, result, request, parent):
		"""
		This method is invoked when a threaded request for the
		navigation is finished. The result is send back to the
		client. If the result is an instance of BaseException an error
		is returned.
		"""
		if self._check_thread_error(thread, result, request):
			return

	@sanitize(nodePattern=SearchSanitizer(default='*'))
	def node_query(self, request):
		"""
		Searches nodes by the given pattern

		options: {'nodePattern': <pattern>}

		return: [{
			'id': <node URI>,
			'label': <node name>,
			'group': 'default',
			'type': 'node',
			'virtech': <virtualization technology>,
			'memUsed': <used amount of memory in B>,
			'memAvailable': <amount of physical memory in B>,
			'cpus': <number of CPUs>,
			'cpuUsage': <cpu usage in %>,
			'available': (True|False),
			'supports_suspend': (True|False),
			'supports_snapshot': (True|False)
			}, ...]
		"""
		self.required_options(request, 'nodePattern')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM NODE_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			nodes = []
			success, data = result
			if success:
				for node_pd in data:
					node_uri = urlsplit(node_pd.uri)
					nodes.append({
						'id': node_pd.uri,
						'label': node_pd.name,
						'group': _('Physical servers'),
						'type': 'node',
						'virtech': node_uri.scheme,
						'memUsed': node_pd.curMem,
						'memAvailable': node_pd.phyMem,
						'cpuUsage': (node_pd.cpu_usage or 0) / 10.0,
						'available': node_pd.last_try == node_pd.last_update,
						'cpus': node_pd.cpus,
						'supports_suspend': node_pd.supports_suspend,
						'supports_snapshot': node_pd.supports_snapshot,
						})

				self.finished(request.id, nodes)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'NODE_LIST',
				Callback(_finished, request),
				group='default',
				pattern=request.options['nodePattern']
				)
