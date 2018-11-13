#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter docker glue
#
# Copyright 2015-2018 Univention GmbH
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
import shutil
from json import loads
from tempfile import NamedTemporaryFile
from contextlib import contextmanager

import ruamel.yaml as yaml

from univention.appcenter.utils import app_ports_with_protocol, app_ports, call_process, call_process2, shell_safe, get_sha256, mkdir, unique, _
from univention.appcenter.log import get_base_logger
from univention.appcenter.exceptions import DockerVerificationFailed, DockerImagePullFailed
from univention.appcenter.ucr import ucr_save, ucr_is_false, ucr_get, ucr_run_filter, ucr_is_true

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


def verify(app, image):
	from univention.appcenter.actions import get_action
	update = get_action('update')()
	appinfo = update.get_app_info(app)

	if not appinfo:
		_logger.error('Warning: Cannot check DockerImage checksum because app is not in index.json: %s' % app.id)
		return  # Nothing we can do here, this is mainly for ucs-test apps

	try:
		appfileinfo = appinfo['ini']
		dockerimageinfo = appfileinfo['DockerImageManifestV2S1']
		appcenter_sha256sum = dockerimageinfo['sha256']
		docker_image_manifest_url = dockerimageinfo['url']
	except KeyError:
		_logger.error('Error looking up DockerImage checksum for %s from index.json' % app.id)
		return  # Nothing we can do here, this is the case of ISV Docker repos

	import requests
	https_request_auth = requests.auth.HTTPBasicAuth(DOCKER_READ_USER_CRED['username'], DOCKER_READ_USER_CRED['password'])
	https_request_answer = requests.get(docker_image_manifest_url, auth=https_request_auth)
	if not https_request_answer.ok:
		raise DockerImageVerificationFailedRegistryContact(app.id, docker_image_manifest_url)

	docker_image_manifest_hash = get_sha256(https_request_answer.content)

	# compare with docker registry
	if appcenter_sha256sum != docker_image_manifest_hash:
		raise DockerImageVerificationFailedChecksum(app.id, docker_image_manifest_url)


def ps(only_running=True):
	args = ['docker', 'ps', '--no-trunc=true']
	if not only_running:
		args.append('--all')
	return check_output(args)


def execute_with_output(container, args, tty=None):
	docker_exec = ['docker', 'exec', '-u', 'root']
	if tty is None:
		tty = sys.stdin.isatty()
	if tty:
		docker_exec.append('-it')
	args = docker_exec + [container] + args
	return check_output(args)


def execute_with_process(container, args, logger=None, tty=None):
	if logger is None:
		logger = _logger
	docker_exec = ['docker', 'exec', '-u', 'root']
	if tty is None:
		tty = sys.stdin.isatty()
	if tty:
		docker_exec.append('-it')
	args = docker_exec + [container] + args
	return call_process(args, logger)


def create(image, command, hostname=None, ports=None, volumes=None, env_file=None, args=None):
	_args = []
	if hostname:
		_args.extend(['--hostname', hostname])
	if env_file:
		_args.extend(['--env-file', env_file])
	if ports:
		for port in ports:
			_args.extend(['-p', port])
	for volume in volumes:
		_args.extend(['-v', volume])
	if args:
		_args.extend(args)
	_args.append(image)
	if command:
		_args.extend(command)
	args = ['docker', 'create'] + _args
	_logger.debug('Creating a new Docker Container:')
	_logger.debug(' '.join(args))
	return check_output(args).strip()


def rmi(image):
	return call(['docker', 'rmi', image])


def rm(container):
	return call(['docker', 'rm', container])


def stop(container):
	return call(['docker', 'stop', container])


def commit(container, new_base_image):
	return check_output(['docker', 'commit', container, new_base_image])


def docker_logs(container, logger=None):
	args = ['docker', 'logs', container]
	ret, out = call_process2(args, logger=logger)
	return out


def dockerd_logs(logger=None):
	args = ['journalctl', '-n', '20', '-o', 'short', '/usr/bin/dockerd']
	ret, out = call_process2(args, logger=logger)
	return out


def docker_cp(src, dest, logger=None, followlink=False):
	args = ['docker', 'cp']
	if followlink is True:
		args.append('-L')
	args.append(src)
	args.append(dest)
	return call_process2(args, logger=logger)


class Docker(object):

	def __init__(self, app, logger=None):
		self.app = app
		self.logger = logger or _logger
		self.container = ucr_get(self.app.ucr_container_key)
		self._root_dir = None

	def inspect_image(self):
		return inspect(self.image)

	def inspect_container(self):
		return inspect(self.container)

	@property
	def root_dir(self):
		if self._root_dir is None:
			try:
				self._root_dir = self.inspect_container()['GraphDriver']['Data']['MergedDir']
			except KeyError:
				# old docker (4.1). maybe containers are still running?
				self._root_dir = os.path.join('/var/lib/docker/overlay', self.container, 'merged')
		return self._root_dir

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
		try:
			hub, image_name = self.image.split('/', 1)
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
		ret, out = call_process2(['docker', 'pull', self.image], logger=_logger)
		if ret != 0:
			raise DockerImagePullFailed(self.image, out)

	def verify(self):
		if ucr_is_false('appcenter/index/verify'):
			return
		try:
			verify(self.app, self.image)
		except Exception as exc:
			self.logger.fatal(str(exc))
			raise DockerVerificationFailed()

	@contextmanager
	def tmp_file(self):
		path = self.path()
		if not path:
			yield None
		else:
			tmp_dir = os.path.join(path, 'var', 'univention', 'tmp')
			if not os.path.isdir(tmp_dir):
				os.makedirs(tmp_dir)
			tmp_file = NamedTemporaryFile(dir=tmp_dir)
			os.chmod(tmp_file.name, 0622)  # world writable for containers not using root as user
			tmp_file.container_path = tmp_file.name[len(path) - 1:]
			try:
				yield tmp_file
			finally:
				tmp_file.close()

	def execute_with_output(self, *args, **kwargs):
		args = list(args)
		for key, value in kwargs.iteritems():
			args.extend(['--%s' % key, value])
		return execute_with_output(self.container, args)

	def execute(self, *args, **kwargs):
		args = list(args)
		logger = kwargs.pop('_logger', self.logger)
		logger = logger.getChild('container.%s' % self.container[:4])
		tty = kwargs.pop('_tty', None)
		logger.debug('Using container.%s for container %s' % (self.container[:4], self.container))
		for key, value in kwargs.iteritems():
			args.extend(['--%s' % key.replace('_', '-'), value])
		return execute_with_process(self.container, args, logger=logger, tty=tty)

	def path(self, filename=''):
		if self.container is None:
			return
		if filename.startswith('/'):
			filename = filename[1:]
		return os.path.join(self.root_dir, filename)

	def ucr_filter_env_file(self, env):
		env_file = os.path.join(self.app.get_data_dir().rstrip('data'), self.app.id + '.env')
		# remove old env file
		try:
			os.remove(env_file)
		except OSError:
			pass
		# create new env file
		fd = os.open(env_file, os.O_RDWR | os.O_CREAT)
		os.chmod(env_file, 0400)
		with os.fdopen(fd, 'w') as outfile:
			# appcenter env file
			if os.path.exists(self.app.get_cache_file('env')):
				with open(self.app.get_cache_file('env'), 'r') as infile:
					outfile.write(ucr_run_filter(infile.read()))
					outfile.write('\n')
			# env variables from appcenter
			for key, value in env.iteritems():
				outfile.write('%s=%s\n' % (shell_safe(key), value))
				outfile.write('%s=%s\n' % (shell_safe(key).upper(), value))
		return env_file

	def create(self, hostname, env):
		ports = []
		for app_id, container_port, host_port, protocol in app_ports_with_protocol():
			if app_id == self.app.id:
				port_definition = '%d:%d/%s' % (host_port, container_port, protocol)
				ports.append(port_definition)
		volumes = set(self.app.docker_volumes[:])
		for app_volume in [self.app.get_data_dir(), self.app.get_conf_dir()]:
			app_volume = '%s:%s' % (app_volume, app_volume)
			volumes.add(app_volume)
		if self.app.host_certificate_access:
			cert_dir = '/etc/univention/ssl/%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
			cert_volume = '%s:%s:ro' % (cert_dir, cert_dir)
			volumes.add(cert_volume)
		volumes.add('/sys/fs/cgroup:/sys/fs/cgroup:ro')                     # systemd
		if ucr_is_true('appcenter/docker/container/proxy/settings', default=True):
			if os.path.isfile('/etc/apt/apt.conf.d/80proxy'):
				volumes.add('/etc/apt/apt.conf.d/80proxy:/etc/apt/apt.conf.d/80proxy:ro')  # apt proxy
		env_file = self.ucr_filter_env_file(env)
		command = None
		if self.app.docker_script_init:
			command = shlex.split(self.app.docker_script_init)
		args = shlex.split(ucr_get(self.app.ucr_docker_params_key, ''))
		for tmpfs in ("/run", "/run/lock"):                                 # systemd
			args.extend(["--tmpfs", tmpfs])
		seccomp_profile = "/etc/docker/seccomp-systemd.json"
		args.extend(["--security-opt", "seccomp:%s" % seccomp_profile])     # systemd
		args.extend(["-e", "container=docker"])                             # systemd
		container = create(self.image, command, hostname, ports, volumes, env_file, args)
		ucr_save({self.app.ucr_container_key: container})
		self.container = container
		return container

	def commit(self, new_image_name):
		return commit(self.container, new_image_name)

	def stop(self):
		return stop(self.container)

	def rm(self):
		return rm(self.container)

	def logs(self):
		return docker_logs(self.container, logger=self.logger)

	def dockerd_logs(self):
		return dockerd_logs(logger=self.logger)

	def cp_to_container(self, src, dest, **kwargs):
		logger = kwargs.pop('_logger', self.logger)
		return docker_cp(src, self.container + ':' + dest, logger=logger, **kwargs)

	def cp_from_container(self, src, dest, **kwargs):
		logger = kwargs.pop('_logger', self.logger)
		return docker_cp(self.container + ':' + src, dest, logger=logger, **kwargs)


class MultiDocker(Docker):
	def verify(self):
		return True

	def pull(self):
		self._setup_yml(False)
		ret, out = call_process2(['docker-compose', '-p', self.app.id, 'pull'], cwd=self.app.get_compose_dir(), logger=_logger)
		if ret != 0:
			raise DockerImagePullFailed(self.image, out)

	def _app_volumes(self):
		volumes = self.app.docker_volumes[:]
		for app_volume in [self.app.get_data_dir(), self.app.get_conf_dir()]:
			app_volume = '%s:%s' % (app_volume, app_volume)
			volumes.append(app_volume)
		if self.app.host_certificate_access:
			cert_dir = '/etc/univention/ssl/%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
			cert_volume = '%s:%s:ro' % (cert_dir, cert_dir)
			volumes.append(cert_volume)
		volumes.append('/sys/fs/cgroup:/sys/fs/cgroup:ro')                     # systemd
		if ucr_is_true('appcenter/docker/container/proxy/settings', default=True):
			if os.path.isfile('/etc/apt/apt.conf.d/80proxy'):
				volumes.append('/etc/apt/apt.conf.d/80proxy:/etc/apt/apt.conf.d/80proxy:ro')  # apt proxy
		return unique(volumes)

	def _setup_yml(self, recreate):
		yml_file = self.app.get_compose_file('docker-compose.yml')
		template_file = '%s.template' % yml_file
		if os.path.exists(yml_file):
			if not recreate:
				return
		else:
			mkdir(self.app.get_compose_dir())
			shutil.copy2(self.app.get_cache_file('compose'), template_file)
		with open(template_file) as fd:
			template = fd.read()
			content = ucr_run_filter(template)
		with open(yml_file, 'wb') as fd:
			fd.write(content)
		content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
		container_def = content['services'][self.app.docker_main_service]
		volumes = container_def.get('volumes', [])
		for volume in self._app_volumes():
			if volume not in volumes:
				volumes.append(volume)
		container_def['volumes'] = volumes
		exposed_ports = {}
		used_ports = {}
		for service_name, service in content['services'].iteritems():
			exposed_ports[service_name] = (int(port) for port in service.get('expose', []))
			used_ports[service_name] = {}
			for port in service.get('ports', []):
				try:
					_port = int(port)
				except ValueError:
					host_port, container_port = (int(_port) for _port in port.split(':'))
					used_ports[service_name][container_port] = host_port
				else:
					used_ports[service_name][_port] = _port
		for app_id, container_port, host_port in app_ports():
			if app_id != self.app.id:
				continue
			for service_name, ports in exposed_ports.iteritems():
				if container_port in ports:
					used_ports[service_name][container_port] = host_port
					break
			else:
				for service_name, ports in used_ports.iteritems():
					if container_port in ports:
						used_ports[service_name][container_port] = host_port
						break
				else:
					used_ports[self.app.docker_main_service][container_port] = host_port
		for service_name, ports in used_ports.iteritems():
			content['services'][service_name]['ports'] = ['%s:%s' % (host_port, container_port) for container_port, host_port in ports.iteritems()]
		with open(yml_file, 'wb') as fd:
			yaml.dump(content, fd, Dumper=yaml.RoundTripDumper, encoding='utf-8', allow_unicode=True)

	def create(self, hostname, set_vars):
		self._setup_yml(True)
		call_process(['docker-compose', '-p', self.app.id, 'create'], cwd=self.app.get_compose_dir())
		try:
			out = ps(only_running=False)
		except CalledProcessError:
			return False
		else:
			yml_file = self.app.get_compose_file('docker-compose.yml')
			content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
			docker_image = content['services'][self.app.docker_main_service]['image']
			for line in out.splitlines():
				try:
					container, image = line.split()[:2]
				except ValueError:
					pass
				else:
					if image == docker_image:
						ucr_save({self.app.ucr_container_key: container})
						self.container = container
						return container

	def up(self):
		return call_process(['docker-compose', '-p', self.app.id, 'up', '-d'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0

	def stop(self):
		return call_process(['docker-compose', '-p', self.app.id, 'down'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0

	def rm(self):
		return self.stop()
