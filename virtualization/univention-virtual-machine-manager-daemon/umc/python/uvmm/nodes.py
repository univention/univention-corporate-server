# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UVMM node commands
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

from univention.lib.i18n import Translation

from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import SearchSanitizer

from urlparse import urlsplit

_ = Translation('univention-management-console-modules-uvmm').translate


class Nodes(object):

	"""
	UMC functions for UVMM node handling.
	"""

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
			'memPhysical': <amount of physical memory in B>,
			'cpus': <number of CPUs>,
			'cpuUsage': <cpu usage in %>,
			'available': (True|False),
			}, ...]
		"""
		def _finished(data):
			"""
			Process asynchronous UVMM NODE_LIST answer.
			"""

			nodes = []
			for node_pd in data:
				node_uri = urlsplit(node_pd.uri)
				nodes.append({
					'id': node_pd.uri,
					'label': node_pd.name,
					'group': _('Physical servers'),
					'type': 'node',
					'virtech': node_uri.scheme,
					'memUsed': node_pd.curMem,
					'memPhysical': node_pd.phyMem,
					'cpuUsage': (node_pd.cpu_usage or 0),
					'available': node_pd.last_try == node_pd.last_update,
					'cpus': node_pd.cpus,
				})
			return nodes

		self.uvmm.send(
			'NODE_LIST',
			self.process_uvmm_response(request, _finished),
			group='default',
			pattern=request.options['nodePattern']
		)
