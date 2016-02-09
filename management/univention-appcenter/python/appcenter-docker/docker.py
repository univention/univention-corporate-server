#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter docker glue
#
# Copyright 2015-2016 Univention GmbH
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
#

# standard library
import sys
from subprocess import check_output, call, CalledProcessError
import os
import os.path
import shlex
from json import loads
from StringIO import StringIO
from gzip import GzipFile
import requests
from hashlib import sha256

from univention.appcenter.utils import app_ports, call_process, shell_safe, _
from univention.appcenter.log import get_base_logger
from univention.appcenter.app import CACHE_DIR
from univention.appcenter.actions.update import Update
from univention.appcenter.actions import Abort
from univention.appcenter.ucr import ucr_save, ucr_is_false, ucr_get

_logger = get_base_logger().getChild('docker')

DOCKER_READ_USER_CRED = {
	'username': 'ucs',
	'password': 'readonly',
	}


class DockerImageVerificationFailedRegistryContact(Exception):

	def __init__(self, app_name, docker_image_manifest_url):
		reason_en_US = 'Error while contacting Docker registry server %s' % (docker_image_manifest_url,)
		reason_message = _('Error while contacting Docker registry server %s') % (docker_image_manifest_url,)

		_logger.error(reason_en_US)
		super(DockerImageVerificationFailedRegistryContact, self).__init__(reason_message)


class DockerImageVerificationFailedChecksum(Exception):
	def __init__(self, app_name):
		reason_en_US = 'Manifest checksum mismatch'
		reason_message = _('Manifest checksum mismatch')

		_logger.error(reason_en_US)
		super(DockerImageVerificationFailedChecksum, self).__init__(reason_message)


def inspect(name):
	out = check_output(['docker', 'inspect', name])
	return loads(out)[0]


def pull(image):
	try:
		hub, image_name = image.split('/', 1)
	except ValueError:
		pass
	else:
		cfg = {}
		dockercfg_file = os.path.expanduser('~/.dockercfg')
		if os.path.exists(dockercfg_file):
			with open(dockercfg_file) as dockercfg:
				cfg = loads(dockercfg.read())
		if hub not in cfg:
			retcode = call(['docker', 'login', '-e', 'invalid', '-u', DOCKER_READ_USER_CRED['username'], '-p', DOCKER_READ_USER_CRED['password'], hub])
			if retcode != 0:
				_logger.warn('Could not login to %s. You may not be able to pull the image from the repository!' % hub)
	call(['docker', 'pull', image])


def verify(app, image):
	index_json_gz_filename = '.index.json.gz'
	index_json_gz_path = os.path.join(CACHE_DIR, index_json_gz_filename)

	if os.path.exists(index_json_gz_path):
		with open(index_json_gz_path, 'rb') as f:
			index_json_gz = f.read()
		try:
			zipped = StringIO(index_json_gz)
			content = GzipFile(mode='rb', fileobj=zipped).read()
		except:
			_logger.error('Could not read "%s"' % index_json_gz_filename)
			raise
		try:
			json_apps = loads(content)
		except:
			_logger.error('JSON malformatted: %r' % content)
			raise
	else:
		upd = Update()
		upd._appcenter_server = None
		upd._get_server()
		json_apps = upd._load_index_json()

	try:
		appinfo = json_apps[app.component_id]
	except KeyError as exc:
		_logger.error('Warning: Cannot check DockerImage checksum because app is not in index.json: %s' % app.id)
		return  # Nothing we can do here, this is mainly for ucs-test apps

	try:
		appfileinfo = appinfo['ini']
		dockerimageinfo = appfileinfo['DockerImageManifestV2S1']
		appcenter_sha256sum = dockerimageinfo['sha256']
		docker_image_manifest_url = dockerimageinfo['url']
	except KeyError as exc:
		_logger.error('Error looking up DockerImage checksum for %s from index.json' % app.id)
		return  # Nothing we can do here, this is the case of ISV Docker repos

	https_request_auth = requests.auth.HTTPBasicAuth(DOCKER_READ_USER_CRED['username'], DOCKER_READ_USER_CRED['password'])
	https_request_answer = requests.get(docker_image_manifest_url, auth=https_request_auth)
	if not https_request_answer.ok:
		exc = DockerImageVerificationFailedRegistryContact(app.id, docker_image_manifest_url)
		raise exc

	docker_image_manifest = https_request_answer.content
	docker_image_manifest_hash = sha256(docker_image_manifest).hexdigest()

	# compare with docker registry
	if appcenter_sha256sum != docker_image_manifest_hash:
		exc = DockerImageVerificationFailedChecksum(app.id, docker_image_manifest_url)
		raise exc


def ps(only_running=True):
	args = ['docker', 'ps', '--no-trunc=true']
	if not only_running:
		args.append('--all')
	return check_output(args)


def execute_with_output(container, args, tty=None):
	docker_exec = ['docker', 'exec']
	if tty is None:
		tty = sys.stdin.isatty()
	if tty:
		docker_exec.append('-it')
	args = docker_exec + [container] + args
	return check_output(args)


def execute_with_process(container, args, logger=None, tty=None):
	if logger is None:
		logger = _logger
	docker_exec = ['docker', 'exec']
	if tty is None:
		tty = sys.stdin.isatty()
	if tty:
		docker_exec.append('-it')
	args = docker_exec + [container] + args
	return call_process(args, logger)


def create(image, command, hostname=None, env=None, ports=None, volumes=None, env_file=None):
	args = []
	if hostname:
		args.extend(['--hostname', hostname])
	if env:
		for key, value in env.iteritems():
			args.extend(['-e', '%s=%s' % (shell_safe(key), value)])
			args.extend(['-e', '%s=%s' % (shell_safe(key).upper(), value)])
	if env_file:
		args.extend(['--env-file', env_file])
	if ports:
		for port in ports:
			args.extend(['-p', port])
	for volume in volumes:
		args.extend(['-v', volume])
	return check_output(['docker', 'create'] + args + [image] + command).strip()


def rm(container):
	return call(['docker', 'rm', container])


def stop(container):
	return call(['docker', 'stop', container])


def commit(container, new_base_image):
	return check_output(['docker', 'commit', container, new_base_image])


class Docker(object):
	def __init__(self, app, logger=None):
		self.app = app
		self.logger = logger or _logger
		self.container = ucr_get(self.app.ucr_container_key)

	def inspect_image(self):
		return inspect(self.image)

	def inspect_container(self):
		return inspect(self.container)

	@property
	def image(self):
		return self.app.get_docker_image_name()

	def exists(self):
		return self._find_container(only_running=False)

	def is_running(self):
		return self._find_container(only_running=True)

	def _find_container(self, only_running):
		if self.container:
			try:
				out = ps(only_running=only_running)
			except CalledProcessError:
				return False
			else:
				for line in out.splitlines():
					if line.startswith(self.container):
						return True
		return False

	def pull(self):
		return pull(self.image)

	def verify(self):
		if ucr_is_false('appcenter/index/verify'):
			return
		try:
			verify(self.app, self.image)
		except Exception as exc:
			self.logger.fatal(str(exc))
			raise Abort()

	def execute_with_output(self, *args, **kwargs):
		args = list(args)
		for key, value in kwargs.iteritems():
			args.extend(['--%s' % key, value])
		return execute_with_output(self.container, args)

	def execute(self, *args, **kwargs):
		args = list(args)
		logger = kwargs.pop('_logger', self.logger)
		logger = logger.getChild('container.%s' % self.container[:4])
		logger.debug('Using container.%s for container %s' % (self.container[:4], self.container))
		for key, value in kwargs.iteritems():
			args.extend(['--%s' % key.replace('_', '-'), value])
		return execute_with_process(self.container, args, logger=logger)

	def path(self, filename=''):
		if self.container is None:
			return
		if filename.startswith('/'):
			filename = filename[1:]
		return os.path.join('/var/lib/docker/overlay', self.container, 'merged', filename)

	def create(self, hostname, env):
		ports = []
		for app_id, container_port, host_port in app_ports():
			if app_id == self.app.id:
				ports.append('%d:%d' % (host_port, container_port))
		volumes = self.app.docker_volumes[:]
		for app_volume in [self.app.get_data_dir(), self.app.get_conf_dir()]:
			app_volume = '%s:%s' % (app_volume, app_volume)
			if app_volume not in volumes:
				volumes.append(app_volume)
		env_file = None
		if os.path.exists(self.app.get_cache_file('env')):
			env_file = self.app.get_cache_file('env')
		command = shlex.split(self.app.docker_script_init)
		container = create(self.image, command, hostname, env, ports, volumes, env_file)
		ucr_save({self.app.ucr_container_key: container})
		self.container = container
		return container

	def commit(self, new_image_name):
		return commit(self.container, new_image_name)

	def stop(self):
		return stop(self.container)

	def rm(self):
		return rm(self.container)
