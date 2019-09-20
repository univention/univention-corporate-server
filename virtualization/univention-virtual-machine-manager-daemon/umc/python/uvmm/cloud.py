# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UVMM cloud commands
#
# Copyright 2014-2019 Univention GmbH
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
from univention.management.console.modules.sanitizers import SearchSanitizer, ChoicesSanitizer
from univention.uvmm.uvmm_ldap import ldap_cloud_types, ldap_cloud_connection_add

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

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_LIST answer.
			"""
			return [{
				'id': d.name,
				'label': d.name,
				'group': _('Cloud connection'),
				'type': 'cloud',
				'cloudtype': d.cloudtype,
				'available': d.available,
				'last_error_message': d.last_error_message,
				'dn': d.dn,
				'search_pattern': d.search_pattern,
				'ucs_images': d.ucs_images,
			} for d in data]

		self.uvmm.send(
			'L_CLOUD_LIST',
			self.process_uvmm_response(request, _finished),
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
		def _finished(data):
			# add cloud to ldap
			ldap_cloud_connection_add(cloudtype, name, parameter, ucs_images, search_pattern, preselected_images)
			return data

		self.required_options(request, 'cloudtype', 'name', 'parameter', 'testconnection')
		cloudtype = request.options.get('cloudtype')
		name = request.options.get('name')
		testconnection = request.options.get('testconnection')
		parameter = request.options.get('parameter', {})
		search_pattern = parameter.pop('search_pattern', '')
		preselected_images = parameter.pop('preselected_images', [])
		ucs_images = parameter.pop('ucs_images', True)

		# add cloud to uvmm
		args = parameter.copy()
		args['name'] = name
		args['type'] = cloudtype
		args['search_pattern'] = search_pattern
		args['preselected_images'] = preselected_images
		args['ucs_images'] = ucs_images

		self.uvmm.send(
			'L_CLOUD_ADD',
			self.process_uvmm_response(request, _finished),
			args=args,
			testconnection=testconnection
		)

	def cloud_list_keypair(self, request):
		"""
		Returns a list of keypair for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_KEYPAIR_LIST answer.
			"""
			return [
				{'id': item.name, 'label': item.name}
				for conn_name, images in data.items()
				for item in images
			]

		self.uvmm.send(
			'L_CLOUD_KEYPAIR_LIST',
			self.process_uvmm_response(request, _finished),
			conn_name=conn_name
		)

	def cloud_list_size(self, request):
		"""
		Returns a list of hardware sizes for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_SIZE_LIST answer.
			"""
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

			return size_list

		self.uvmm.send(
			'L_CLOUD_SIZE_LIST',
			self.process_uvmm_response(request, _finished),
			conn_name=conn_name
		)

	@sanitize(pattern=SearchSanitizer(default='*'))
	def cloud_list_image(self, request):
		"""
		Returns a list of images by a pattern for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_IMAGE_LIST answer.
			"""
			return [
				{'id': item.id, 'label': item.name}
				for conn_name, images in data.items()
				for item in images
			]

		self.uvmm.send(
			'L_CLOUD_IMAGE_LIST',
			self.process_uvmm_response(request, _finished),
			conn_name=conn_name
		)

	def cloud_list_secgroup(self, request):
		"""
		Returns a list of security groups for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')
		network_id = request.options.get('network_id')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_SECGROUP_LIST answer.
			"""
			return [
				{'id': item.id, 'label': item.name}
				for conn_name, images in data.items()
				for item in images if network_id in ('default', item.network_id)
			]

		self.uvmm.send(
			'L_CLOUD_SECGROUP_LIST',
			self.process_uvmm_response(request, _finished),
			conn_name=conn_name
		)

	def cloud_list_network(self, request):
		"""
		Returns a list of networks for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_NETWORK_LIST answer.
			"""
			return [
				{
					'id': item.id,
					'label': '%s %s' % (item.name, item.cidr or "")
				}
				for conn_name, images in data.items()
				for item in images
			]

		self.uvmm.send(
			'L_CLOUD_NETWORK_LIST',
			self.process_uvmm_response(request, _finished),
			conn_name=conn_name
		)

	def cloud_list_subnet(self, request):
		"""
		Returns a list of subnet for the given cloud conn_name.
		"""
		self.required_options(request, 'conn_name')
		conn_name = request.options.get('conn_name')
		network_id = request.options.get('network_id')

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_SUBNET_LIST answer.
			"""
			return [
				{
					'id': item.id,
					'label': '%s %s' % (item.name, item.cidr or "")
				}
				for conn_name, images in data.items()
				for item in images if network_id == item.network_id
			]

		self.uvmm.send(
			'L_CLOUD_SUBNET_LIST',
			self.process_uvmm_response(request, _finished),
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

		def _finished(data):
			"""
			Process asynchronous UVMM L_CLOUD_INSTANCE_LIST answer.
			"""
			instances = []
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
			return instances

		self.uvmm.send(
			'L_CLOUD_INSTANCE_LIST',
			self.process_uvmm_response(request, _finished),
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
			self.process_uvmm_response(request),
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
			self.process_uvmm_response(request),
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
			self.process_uvmm_response(request),
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
