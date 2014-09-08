# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UVMM cloud commands
#
# Copyright 2014 Univention GmbH
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
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import SearchSanitizer, ChoicesSanitizer
from univention.uvmm.uvmm_ldap import ldap_cloud_types

from notifier import Callback
from urlparse import urldefrag

_ = Translation('univention-management-console-modules-uvmm').translate


class Cloud(object):
	"""
	Handle cloud connections and instances.
	"""

	@sanitize(nodePattern=SearchSanitizer(default='*'))
	def cloud_query(self, request):
		"""
		Searches clouds by the given pattern

		options: {'nodePattern': <cloud pattern>}

		return: [{
			'id': <cloud name>,
			'label': <cloud name>,
			'group': 'cloudconnection',
			'type': 'cloud',
			'available': (True|False),
			}, ...]
		"""
		self.required_options(request, 'nodePattern')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			clouds = []
			success, data = result

			if success:
				for d in data:
					clouds.append({
						'id': d.name,
						'label': d.name,
						'group': _('Cloud connection'),
						'type': 'cloud',
						'available': d.last_update_try == d.last_update,
						})

				MODULE.info('success: %s, data: %s' % (success, clouds))
				self.finished(request.id, clouds)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_LIST',
				Callback(_finished, request),
				pattern=request.options['nodePattern']
				)

	@sanitize(domainPattern=SearchSanitizer(default='*'))
	def instance_query(self, request):
		"""
		Returns a list of instances matching domainPattern on the clouds matching nodePattern.

		options: {
			['nodePattern': <cloud pattern>,]
			['domainPattern': <instance pattern>,]
			}

		return: [{
			'node_available': True,
			'extra': {
				'key_name': None,
				'disk_config': 'MANUAL',
				'flavorId': '1',
				'availability_zone': 'nova',
				'password': None,
				'metadata': {}
			},
			'label': 'automagic-997898',
			'type': 'instance',
			'id': 'myCloud2#e2c8e274-2e17-499c-a3f9-620fb249578c',
			'nodeName': 'myCloud2'
		}, ... ]
		"""

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_INSTANCE_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			instances = []
			success, data = result

			if success:
				for conn_name, insts in data.items():
					for inst in insts:
						instance_uri = '%s#%s' % (conn_name, inst.id)
						instances.append({
							'id': instance_uri,
							'label': inst.name,
							'nodeName': conn_name,
							'state': inst.state,
							'type': 'instance',
							'suspended': None,  # FIXME
							'description': '%s [%s]' % (inst.u_size_name, inst.state),
							'node_available': inst.available,
							'extra': inst.extra,
						})
				MODULE.info('success: %s, data: %s' % (success, instances))
				self.finished(request.id, instances)
			else:
				self.finished(
						request.id,
						None,
						str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_INSTANCE_LIST',
				Callback(_finished, request),
				conn_name=request.options.get('nodePattern', ''),
				pattern=request.options['domainPattern']
				)

	@sanitize(state=ChoicesSanitizer(choices=('RUN', 'RESTART', 'SOFTRESTART')))
	def instance_state(self, request):
		"""
		Set the state a instance instance_id on cloud conn_name.

		options: {
			'uri': <conn_name#instance_id>,
			'state': (RUN|RESTART|SOFTRESTART),
			}

		return:
		"""
		self.required_options(request, 'uri', 'state')

		conn_name, instance_id = urldefrag(request.options['uri'])
		state = request.options['state']

		self.uvmm.send(
				'L_CLOUD_INSTANCE_STATE',
				Callback(self._thread_finish, request),
				conn_name=conn_name,
				instance_id=instance_id,
				state=state,
				)

	def instance_remove(self, request):
		"""
		Removes a instance.

		options: {
			'domainURI': <domain uri>
			}

		return:
		"""
		self.required_options(request, 'domainURI')
		conn_name, instance_id = urldefrag(request.options['domainURI'])

		self.uvmm.send(
				'L_CLOUD_INSTANCE_TERMINATE',
				Callback(self._thread_finish, request),
				conn_name=conn_name,
				instance_id=instance_id
				)

	def cloudtype_get(self, request):
		"""
		Returns a list of all cloudtypes from ldap.
		"""
		cloudtypes = []
		for item in ldap_cloud_types():
			cloudtypes.append({
				'id': item['name'],
				'label': item['name']
				})

		self.finished(request.id, cloudtypes)
