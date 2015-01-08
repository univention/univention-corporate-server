# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
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

import traceback

from univention.lib.i18n import Translation
from univention.management.console.modules import Base, UMC_OptionTypeError
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import MODULE_ERR_COMMAND_FAILED

from notifier import Callback

from univention.management.console.modules.uvmm.uvmmd import UVMM_RequestBroker
from univention.management.console.modules.uvmm.nodes import Nodes
from univention.management.console.modules.uvmm.profiles import Profiles
from univention.management.console.modules.uvmm.storages import Storages
from univention.management.console.modules.uvmm.domains import Domains
from univention.management.console.modules.uvmm.snapshots import Snapshots
from univention.management.console.modules.uvmm.cloud import Cloud

_ = Translation('univention-management-console-modules-uvmm').translate


class Instance(Base, Nodes, Profiles, Storages, Domains, Snapshots, Cloud):
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

	def _check_thread_error(self, thread, result, request):
		"""
		Checks if the thread returned an exception. In that case in
		error response is send and the function returns True. Otherwise
		False is returned.
		"""
		if not isinstance(result, BaseException):
			return False

		msg = '%s\n%s: %s\n' % (
				''.join(traceback.format_tb(thread.exc_info[2])),
				thread.exc_info[ 0 ].__name__,
				thread.exc_info[1],
				)
		MODULE.process('An internal error occurred: %s' % msg)
		self.finished(request.id, None, msg, False)
		return True

	def _thread_finish(self, thread, result, request):
		"""
		This method is invoked when a threaded request function is
		finished. The result is send back to the client. If the result
		is an instance of BaseException an error is returned.
		"""
		if self._check_thread_error(thread, result, request):
			return

		success, data = result
		MODULE.info('Got result from UVMMd: success: %s, data: %s' % (success, data))
		if not success:
			self.finished(
					request.id,
					None,
					message=data,
					status=MODULE_ERR_COMMAND_FAILED
					)
		else:
			self.finished(request.id, data)

	def _thread_finish_success(self, thread, result, request):
		"""
		This method is invoked when a threaded request function is
		finished. The result is send back to the client. If the result
		is an instance of BaseException an error is returned.
		"""
		if self._check_thread_error(thread, result, request):
			return

		success, data = result
		MODULE.info('Got result from UVMMd: success: %s, data: %s' % (success, data))
		self.finished(request.id, {'success' : success, 'data' : data})

	def query(self, request):
		"""
		Meta query function for groups, nodes and domains.

		options: {
			'type': (group|node|domain),
			'nodePattern': <node pattern>,
			['domainPattern': <domain pattern>]
			}

		return: {
			'success': (True|False),
			'message': <details>
			}
		"""
		self.required_options(request, 'type', 'nodePattern')

		if request.options['type'] == 'node':
			self.node_query(request)
		elif request.options['type'] == 'domain':
			self.domain_query(request)
		elif request.options['type'] == 'cloud':
			self.cloud_query(request)
		elif request.options['type'] == 'instance':
			self.instance_query(request)
		elif request.options['type'] == 'group':
			self.finished(request.id, [{
				'id': 'default',
				'label': _('Physical servers'),
				'type': 'group',
				'icon': 'uvmm-group',
				}])
		else:
			raise UMC_OptionTypeError(_('Unknown query type'))

	def group_query(self, request):
		"""
		Get server groups.
		"""
		self.uvmm.send(
				'GROUP_LIST',
				Callback(self._thread_finish, request)
				)
