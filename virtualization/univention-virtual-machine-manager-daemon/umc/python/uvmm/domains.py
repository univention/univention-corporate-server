#
# -*- coding: utf-8 -*-
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
import socket
import re

from univention.lib.i18n import Translation

from univention.management.console.config import ucr
from univention.management.console.modules import UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import SearchSanitizer

from univention.uvmm.protocol import Data_Domain, Disk, Graphic, Interface
from univention.uvmm.storage import POOLS_TYPE

from urlparse import urlsplit, urldefrag

from .tools import object2dict

_ = Translation('univention-management-console-modules-uvmm').translate


class Domains(object):

	"""
	UMC functions for UVMM domain handling.
	"""

	STATES = ('NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED', 'PMSUSPENDED')
	TARGET_STATES = ('RUN', 'PAUSE', 'SHUTDOWN', 'SHUTOFF', 'RESTART', 'SUSPEND')

	RE_VNC = re.compile(r'^(IPv[46])(?: (.+))?$|^(?:NAME(?: (.+=.*))?)$')
	SOCKET_FAMILIES = {
		'IPv4': socket.AF_INET,
		'IPv6': socket.AF_INET6,
	}
	SOCKET_FORMATS = {
		socket.AF_INET: '%s',
		socket.AF_INET6: '[%s]',
	}

	@sanitize(
		domainPattern=SearchSanitizer(default='*')
	)
	def domain_query(self, request):
		"""
		Returns a list of domains matching domainPattern on the nodes matching nodePattern.

		options: {
			['nodePattern': <node name pattern>,]
			['domainPattern': <domain pattern>,]
			}

		return: [{
			'cpuUsage': <float>,
			'description': <string>,
			'id': <domain uri>,
			'label': <name>,
			'mem': <ram>,
			'nodeName': <node>,
			'node_available': <boolean>,
			'state': <state>,
			'reason': <reason>,
			'suspended': <boolean>,
			'type': 'domain',
			'vnc': <boolean>,
			'vnc_port': <int>,
			'migration': <dict>,
			}, ...]
		"""

		def _finished(data):
			"""
			Process asynchronous UVMM DOMAIN_LIST answer.
			"""
			domain_list = []
			for node_uri, domains in data.items():
				uri = urlsplit(node_uri)
				for domain in domains:
					domain_uri = '%s#%s' % (node_uri, domain['uuid'])
					domain_list.append({
						'id': domain_uri,
						'label': domain['name'],
						'nodeName': uri.netloc,
						'state': domain['state'],
						'reason': domain['reason'],
						'type': 'domain',
						'mem': domain['mem'],
						'cpuUsage': domain['cpu_usage'],
						'vnc': domain['vnc'],
						'vnc_port': domain['vnc_port'],
						'suspended': bool(domain['suspended']),
						'description': domain['description'],
						'node_available': domain['node_available'],
						'error': domain['error'],
						'migration': domain['migration'],
					})
			return domain_list

		self.uvmm.send(
			'DOMAIN_LIST',
			self.process_uvmm_response(request, _finished),
			uri=request.options.get('nodePattern', ''),
			pattern=request.options['domainPattern']
		)

	def domain_get(self, request):
		"""
		Returns details about a domain domainUUID.

		options: {'domainURI': <domain uri>}

		return: {...}
		"""
		def _finished(data):
			"""
			Process asynchronous UVMM DOMAIN_INFO answer.
			Convert UVMM protocol to JSON.
			"""
			node_uri = urlsplit(request.options['domainURI'])
			uri, _uuid = urldefrag(request.options['domainURI'])
			json = object2dict(data)

			# re-arrange a few attributes for the frontend
			# annotations
			for key in json['annotations']:
				if key == 'uuid':
					continue
				json[key] = json['annotations'][key]

			# STOP here if domain is not available
			if not json['available']:
				MODULE.info('Domain is not available: %s' % (json,))
				self.finished(request.id, json)
				return

			# interfaces (fake the special type network:<source>)
			for iface in json['interfaces']:
				if iface['type'] == Interface.TYPE_NETWORK:
					iface['type'] = 'network:' + iface['source']

			# disks
			for disk in json['disks']:
				disk['volumeFilename'] = os.path.basename(disk['source']) if disk['pool'] else disk['source']
				disk['paravirtual'] = disk['target_bus'] in ('virtio',)
				disk['volumeType'] = disk['type']

			# graphics
			if json['graphics']:
				try:
					gfx = json['graphics'][0]
					json['vnc'] = True
					json['vnc_host'] = None
					json['vnc_port'] = None
					json['kblayout'] = gfx['keymap']
					json['vnc_remote'] = gfx['listen'] == '0.0.0.0'
					json['vnc_password'] = gfx['passwd']
					# vnc_password will not be send to frontend
					port = int(json['graphics'][0]['port'])
					if port == -1:
						raise ValueError(json['graphics'][0]['port'])
					host = node_uri.netloc
					vnc_link_format = ucr.get('uvmm/umc/vnc/host', 'IPv4') or ''
					match = Domains.RE_VNC.match(vnc_link_format)
					if match:
						family, pattern, substs = match.groups()
						if family:  # IPvX
							family = Domains.SOCKET_FAMILIES[family]
							regex = re.compile(pattern or '.*')
							addrs = socket.getaddrinfo(
								host,
								port,
								family,
								socket.SOCK_STREAM,
								socket.SOL_TCP
							)
							for (family, _socktype, _proto, _canonname, sockaddr) in addrs:
								host, port = sockaddr[:2]
								if regex.search(host):
									break
							else:
								raise LookupError(pattern)
							host = Domains.SOCKET_FORMATS[family] % (host,)
						elif substs:  # NAME
							for subst in substs.split():
								old, new = subst.split('=', 1)
								host = host.replace(old, new)
					elif vnc_link_format:  # overwrite all hosts with fixed host
						host = vnc_link_format
					json['vnc_host'] = host
					json['vnc_port'] = port
				except re.error as ex:  # port is not valid
					MODULE.warn('Invalid VNC regex: %s' % (ex,))
				except socket.gaierror as ex:
					MODULE.warn('Invalid VNC host: %s' % (ex,))
				except (ValueError, LookupError) as ex:  # port is not valid
					MODULE.warn('Failed VNC lookup: %s' % (ex,))

			# profile (MUST be after mapping annotations)
			profile_dn = json.get('profile')
			profile = self.profiles.get(profile_dn, None)
			if profile:
					json['profileData'] = profile

			MODULE.info('Got domain description: %s' % (json,))
			return json

		self.required_options(request, 'domainURI')
		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_INFO',
			self.process_uvmm_response(request, _finished),
			uri=node_uri,
			domain=domain_uuid
		)

	def _create_disk(self, node_uri, disk, domain_info, profile=None):
		"""
		Convert single disk from JSON to Python UVMM Disk object.
		"""
		uri = urlsplit(node_uri)

		driver_pv = disk.get('paravirtual', False)  # by default no paravirtual devices

		drive = Disk()
		drive.device = disk['device']
		drive.driver_type = disk['driver_type']
		drive.driver_cache = disk.get('driver_cache', 'default')
		drive.driver = disk.get('driver', None)
		drive.target_bus = disk.get('target_bus', 'ide')
		drive.target_dev = disk.get('target_dev', None)

		pool_name = disk.get('pool')
		if pool_name:
			pool = self.get_pool(node_uri, pool_name)
		else:
			pool = {}

		if disk.get('source', None) is None:
			# new drive
			drive.size = disk['size']
			if not pool:
				raise ValueError('Pool "%s" not found' % (pool_name,))
			drive.source = os.path.join(pool['path'], disk['volumeFilename'])

			if profile:
				if drive.device == Disk.DEVICE_DISK:
					driver_pv = profile.get('pvdisk', False)
				elif drive.device == Disk.DEVICE_CDROM:
					driver_pv = profile.get('pvcdrom', False)
		else:
			# old drive
			drive.source = disk['source']

		MODULE.info('Creating a %s drive' % (
			'paravirtual' if driver_pv else 'emulated',
		))

		try:
			pool_type = pool['type']
			drive.type = POOLS_TYPE[pool_type]
		except LookupError:
			if drive.source.startswith('/dev/'):
				drive.type = Disk.TYPE_BLOCK
			elif not drive.source:
				# empty CDROM or floppy device
				drive.type = Disk.TYPE_BLOCK
			else:
				drive.type = Disk.TYPE_FILE

		if drive.device == Disk.DEVICE_DISK:
			drive.readonly = disk.get('readonly', False)
		elif drive.device == Disk.DEVICE_CDROM:
			drive.driver_type = 'raw'  # ISOs need driver/@type='raw'
			drive.readonly = disk.get('readonly', True)
		elif drive.device == Disk.DEVICE_FLOPPY:
			drive.readonly = disk.get('readonly', True)
		else:
			raise ValueError('Invalid drive-type "%s"' % drive.device)

		if uri.scheme.startswith('qemu'):
			drive.driver = 'qemu'
			if drive.device == Disk.DEVICE_FLOPPY:
				drive.target_bus = 'fdc'
			elif driver_pv:
				drive.target_bus = 'virtio'
			elif disk.get('paravirtual', None) is False:
				drive.target_bus = 'ide'
			else:
				pass  # keep
		else:
			raise ValueError('Unknown virt-tech "%s"' % (node_uri,))

		return drive

	def domain_add(self, request):
		"""
		Creates a new domain on nodeURI.

		options: {
			'nodeURI': <node uri>,
			'domain': {...},
			}

		return:
		"""
		self.required_options(request, 'nodeURI', 'domain')

		domain = request.options.get('domain')

		domain_info = Data_Domain()
		# when we edit a domain there must be a UUID
		if 'domainURI' in domain:
			_node_uri, domain_uuid = urldefrag(domain['domainURI'])
			domain_info.uuid = domain_uuid

		# annotations & profile
		profile = None
		if not domain_info.uuid:
			profile_dn = domain.get('profile')
			try:
				profile = self.profiles[profile_dn]
			except LookupError:
				raise UMC_Error(_('Unknown profile %s') % (profile_dn,))
			domain_info.annotations['profile'] = profile_dn
			MODULE.info('Creating new domain using profile %s' % (profile,))
			domain_info.annotations['os'] = profile.get('os', '')
		else:
			domain_info.annotations['os'] = domain.get('os', '')
		domain_info.annotations['contact'] = domain.get('contact', '')
		domain_info.annotations['description'] = domain.get('description', '')

		domain_info.name = domain['name']
		if 'arch' in domain:
			domain_info.arch = domain['arch']
		elif profile:
			domain_info.arch = profile['arch']
		else:
			raise UMC_Error(_('Could not determine architecture for domain'), status=500)

		if domain_info.arch == 'automatic':
			success, node_list = self.uvmm.send(
				'NODE_LIST',
				None,
				group='default',
				pattern=request.options['nodeURI']
			)
			if not success:
				raise UMC_Error(_('Failed to retrieve details for the server %(nodeURI)s') % request.options, status=500)
			if not node_list:
				raise UMC_Error(_('Unknown physical server %(nodeURI)s') % request.options, status=500)
			archs = set([t.arch for t in node_list[0].capabilities])
			if 'x86_64' in archs:
				domain_info.arch = 'x86_64'
			else:
				domain_info.arch = 'i686'

		domain_info.domain_type = 'kvm'
		domain_info.os_type = 'hvm'
		domain_info.maxMem = domain['maxMem']

		domain_info.autostart = domain['autostart']

		# CPUs
		try:
			domain_info.vcpus = int(domain['vcpus'])
		except ValueError:
			raise UMC_Error(_('vcpus must be a number'))
		domain_info.hyperv = domain.get('hyperv', True)
		domain_info.cpu_model = domain.get('cpu_model')

		# boot devices
		if 'boot' in domain:
			domain_info.boot = domain['boot']
		elif profile:
			domain_info.boot = profile['bootdev']
		else:
			raise UMC_Error(_('Could not determine the list of boot devices for domain'), status=500)

		# VNC
		if domain['vnc']:
			gfx = Graphic()
			if domain.get('vnc_remote', False):
				gfx.listen = '0.0.0.0'
			else:
				gfx.listen = None
			if 'kblayout' in domain:
				gfx.keymap = domain['kblayout']
			elif profile:
				gfx.keymap = profile['kblayout']
			else:
				raise UMC_Error(_('Could not determine the keyboard layout for the VNC access'), status=500)
			if domain.get('vnc_password', None):
				gfx.passwd = domain['vnc_password']

			domain_info.graphics = [gfx]

		# RTC offset
		if 'rtc_offset' in domain:
			domain_info.rtc_offset = domain['rtc_offset']
		elif profile:
			domain_info.rtc_offset = profile['rtcoffset']
		else:
			domain_info.rtc_offset = 'utc'

		# drives
		domain_info.disks = [
			self._create_disk(request.options['nodeURI'], disk, domain_info, profile)
			for disk in domain['disks']
		]

		# network interface
		domain_info.interfaces = []
		for interface in domain['interfaces']:
			iface = Interface()
			if interface.get('type', '').startswith('network:'):
				iface.type = 'network'
				iface.source = interface['type'].split(':', 1)[1]
			else:
				iface.type = interface.get('type', 'bridge')
				iface.source = interface['source']
			iface.model = interface['model']
			iface.mac_address = interface.get('mac_address', None)
			domain_info.interfaces.append(iface)

		def _finished(data):
			"""
			Process asynchronous UVMM DOMAIN_DEFINE answer.
			"""
			return object2dict(data)

		self.uvmm.send(
			'DOMAIN_DEFINE',
			self.process_uvmm_response(request, _finished),
			uri=request.options['nodeURI'],
			domain=domain_info
		)

	domain_put = domain_add

	def domain_state(self, request):
		"""
		Set the state a domain domainUUID on node nodeURI.

		options: {
			'domainURI': <domain uri>,
			'domainState': (RUN|SHUTDOWN|SHUTOFF|PAUSE|RESTART|SUSPEND),
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'domainState')
		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		MODULE.info('nodeURI: %s, domainUUID: %s' % (node_uri, domain_uuid))
		state = request.options['domainState']
		if state not in self.TARGET_STATES:
			raise UMC_Error(_('Invalid domain state: %s') % state)
		self.uvmm.send(
			'DOMAIN_STATE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			state=state,
		)

	def domain_migrate(self, request):
		"""
		Migrates a domain from sourceURI to targetURI.

		options: {
			'domainURI': <domain uri>,
			'targetNodeURI': <target node uri>,
			}

		return:
		"""
		self.required_options(request, 'domainURI')
		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		mode = request.options.get('mode', 0)
		if mode < 101 and mode > -1:
			self.required_options(request, 'targetNodeURI')
		target_uri = request.options.get('targetNodeURI', '')
		self.uvmm.send(
			'DOMAIN_MIGRATE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			target_uri=target_uri,
			mode=mode
		)

	def domain_clone(self, request):
		"""
		Clones an existing domain.

		options: {
			'domainURI': <domain uri>,
			'cloneName': <name of clone>,
			'macAddress' : (clone|auto),
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'cloneName')
		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		self.uvmm.send(
			'DOMAIN_CLONE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			name=request.options['cloneName'],
			subst={'mac': request.options.get('macAddress', 'clone')}
		)

	def domain_remove(self, request):
		"""
		Removes a domain. Optional a list of volumes can be specified that should be removed.

		options: {
			'domainURI': <domain uri>,
			'volumes': [<filename>...]
			}

		return:
		"""
		self.required_options(request, 'domainURI', 'volumes')
		node_uri, domain_uuid = urldefrag(request.options['domainURI'])
		volume_list = request.options['volumes']
		self.uvmm.send(
			'DOMAIN_UNDEFINE',
			self.process_uvmm_response(request),
			uri=node_uri,
			domain=domain_uuid,
			volumes=volume_list
		)
