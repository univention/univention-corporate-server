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
from univention.uvmm.uvmm_ldap import ldap_cloud_types, ldap_cloud_connection_add

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
						'cloudtype': d.cloudtype,
						'available': d.available,
						'last_error_message': d.last_error_message,
						'dn': d.dn,
						'search_image_enabled': d.search_image_enabled,
						'search_only_ucs_images': d.search_only_ucs_images,
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

	def cloud_add(self, request):
		"""
		Add a new cloud connection into ldap.
		options: {
			['cloudtype': <uvmm/cloudtype>,]
			['name': <new cloud name>,]
			['parameter': <key/value parameter>,]
			['testconnection': true (default) / false,]
			}

		return: []
		"""
		def _finished(thread, result, request):
			if self._check_thread_error(thread, result, request):
				return

			success, data = result

			if success:
				# add cloud to ldap
				ldap_cloud_connection_add(cloudtype, name, parameter, enable_search, ucs_images, preselected_images)

				self.finished(request.id, data)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)


		self.required_options(request, 'cloudtype', 'name', 'parameter', 'testconnection')
		cloudtype = request.options.get('cloudtype')
		name = request.options.get('name')
		testconnection = request.options.get('testconnection')
		parameter = request.options.get('parameter')

		# add cloud to uvmm
		args = parameter.copy()
		args['name'] = name
		args['type'] = cloudtype
		args['enable_search'] = request.options.get('enable_search', True)
		args['preselected_images'] = request.options.get('preselected_images', [])
		args['only_ucs_images'] = request.options.get('ucs_images', True)

		self.uvmm.send(
				'L_CLOUD_ADD',
				Callback(_finished, request),
				args=args,
				testconnection=testconnection
				)


	def cloud_list_keypair(self, request):
		"""
		Returns a list of keypair for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_KEYPAIR_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			success, data = result
			if success:
				keypair_list = [
						{'id': item.name, 'label': item.name}
						for conn_name, images in data.items()
						for item in images
						]

				self.finished(request.id, keypair_list)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_KEYPAIR_LIST',
				Callback(_finished, request),
				conn_name=conn_name
				)

	def cloud_list_size(self, request):
		"""
		Returns a list of hardware sizes for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_SIZE_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			success, data = result
			if success:
				size_list = []
				for conn_name, images in data.items():
					for item in images:
						size_list.append({
							'id': item.id,
							'label': item.u_displayname,
							'disk': item.disk,
							'ram': item.ram,
							'vcpus': item.vcpus,
						})

				self.finished(request.id, size_list)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_SIZE_LIST',
				Callback(_finished, request),
				conn_name=conn_name
				)

	@sanitize(pattern=SearchSanitizer(default='*'))
	def cloud_list_image(self, request):
		"""
		Returns a list of images by a pattern for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')
		pattern = request.options.get('pattern')
		only_preselected_images = request.options.get('onlypreselected')
		ucs_images = request.options.get('ucs_images')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_IMAGE_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			success, data = result
			if success:
				image_list = [
						{'id': item.id, 'label': item.name}
						for conn_name, images in data.items()
						for item in images
						]

				self.finished(request.id, image_list)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_IMAGE_LIST',
				Callback(_finished, request),
				conn_name=conn_name,
				pattern=pattern,
				only_preselected_images=only_preselected_images,
				only_ucs_images=ucs_images
				)

	def cloud_list_secgroup(self, request):
		"""
		Returns a list of security groups for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(thread, result, request):
			"""
			Process asynchronous UVMM L_CLOUD_SECGROUP_LIST answer.
			"""
			if self._check_thread_error(thread, result, request):
				return

			success, data = result
			if success:
				secgroup_list = [
						{'id': item.id, 'label': item.name}
						for conn_name, images in data.items()
						for item in images
						]

				self.finished(request.id, secgroup_list)
			else:
				self.finished(
						request.id,
						None,
						message=str(data),
						status=MODULE_ERR_COMMAND_FAILED
						)

		self.uvmm.send(
				'L_CLOUD_SECGROUP_LIST',
				Callback(_finished, request),
				conn_name=conn_name
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
							'public_ips': inst.public_ips,
							'private_ips': inst.private_ips,
							'u_size_name': inst.u_size_name,
							'u_connection_type': inst.u_connection_type,
							'keypair': inst.key_name,
							'image': inst.u_image_name,
							'securitygroup': inst.secgroups,
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

	@sanitize(state=ChoicesSanitizer(choices=('RUN', 'RESTART', 'SOFTRESTART', 'SHUTOFF', 'SHUTDOWN', 'SUSPEND', 'PAUSE', 'RESUME', 'UNPAUSE')))
	def instance_state(self, request):
		"""
		Set the state a instance instance_id on cloud conn_name.

		options: {
			'uri': <conn_name#instance_id>,
			'state': (RUN|RESTART|SOFTRESTART|SHUTOFF|SHUTDOWN|SUSPEND|RESUME|UNPAUSE),
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

	def instance_add(self, request):
		"""
		Create a new instance on cloud conn_name.

		options: {
			'conn_name': <cloud connection name>,
			'parameter': {...},
			}

		return:
		"""
		self.required_options(request, 'conn_name', 'name', 'parameter')
		conn_name = request.options.get('conn_name')
		name = request.options.get('name')
		parameter = request.options.get('parameter')

		args = parameter
		args['name'] = name
		args['security_group_ids'] = [parameter['security_group_ids']]

		self.uvmm.send(
				'L_CLOUD_INSTANCE_CREATE',
				Callback(self._thread_finish, request),
				conn_name=conn_name,
				args=args
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
