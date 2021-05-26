#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter docker glue
#
# Copyright 2015-2021 Univention GmbH
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
#

import sys
from subprocess import check_output, call, CalledProcessError
import os
import os.path
import shlex
import shutil
from json import loads
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
import ssl
from base64 import b64encode
from ipaddress import IPv4Network, IPv4Address
import time

from six.moves import urllib_request, http_client, urllib_error
import ruamel.yaml as yaml

from univention.appcenter.utils import app_ports_with_protocol, app_ports, call_process, call_process2, shell_safe, mkdir, unique, urlopen
from univention.appcenter.app_cache import Apps
from univention.appcenter.log import get_base_logger
from univention.appcenter.exceptions import DockerImagePullFailed, DockerCouldNotStartContainer
from univention.appcenter.ucr import ucr_save, ucr_get, ucr_run_filter, ucr_is_true

_logger = get_base_logger().getChild('docker')

DOCKER_READ_USER_CRED = {
	'username': 'ucs',
	'password': 'readonly',
}


class DockerImageVerificationFailedChecksum(Exception):
	def __init__(self, appcenter_hash, manifest_hash):
		reason = 'Manifest checksum mismatch: %r != %r' % (appcenter_hash, manifest_hash)
		super(DockerImageVerificationFailedChecksum, self).__init__(reason)


def inspect(name):
	out = check_output(['docker', 'inspect', str(name)])
	out = out.decode('utf-8')
	return loads(out)[0]


def login(hub, with_license):
	if with_license:
		username = password = ucr_get('uuid/license')
	else:
		username, password = DOCKER_READ_USER_CRED['username'], DOCKER_READ_USER_CRED['password']
	return call(['docker', 'login', '-u', username, '-p', password, hub])


def access(image):
	if '/' not in image:
		return True
	hub, image_name = image.split('/', 1)
	if ':' in image_name:
		image_name, image_tag = image_name.split(':', 1)
	else:
		image_tag = 'latest'
	url = 'https://%s/v2/%s/manifests/%s' % (hub, image_name, image_tag)
	username = password = ucr_get('uuid/license')
	auth = b64encode(('%s:%s' % (username, password)).encode('utf-8')).decode('ascii')
	request = urllib_request.Request(url, headers={'Authorization': 'Basic %s' % auth})
	try:
		urlopen(request)
	except urllib_error.HTTPError as exc:
		if exc.getcode() == 401:
			return False
		else:
			return False  # TODO
	except (urllib_error.URLError, ssl.CertificateError, http_client.BadStatusLine):
		return False  # TODO
	else:
		return True


def ps(only_running=True):
	args = ['docker', 'ps', '--no-trunc=true']
	if not only_running:
		args.append('--all')
	out = check_output(args)
	return out.decode('utf-8')


def execute_with_output(container, args, tty=None):
	docker_exec = ['docker', 'exec', '-u', 'root']
	if tty is None:
		tty = sys.stdin.isatty()
	if tty:
		docker_exec.append('-it')
	args = docker_exec + [container] + args
	out = check_output(args)
	return out.decode('utf-8')


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
	return call_process2(args)


def rmi(*images):
	_logger.debug('Removing image: %s' % ', '.join(images))
	return call(['docker', 'rmi'] + list(images))


def rm(container):
	return call(['docker', 'rm', container])


def stop(container):
	return call(['docker', 'stop', container])


def commit(container, new_base_image):
	args = ['docker', 'commit', container, new_base_image]
	out = check_output(args)
	return out.decode('utf-8')


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
		self.env_file_created = None

	def inspect_image(self):
		return inspect(self.image)

	def inspect_container(self):
		if self.container:
			return inspect(self.container)
		return None

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
		self.logger.info('Downloading app image %s' % self.image)
		try:
			hub, image_name = self.image.split('/', 1)
		except ValueError:
			pass
		else:
			if '.' in hub:
				retcode = login(hub, with_license=self.app.install_permissions)
				if retcode != 0:
					_logger.warn('Could not login to %s. You may not be able to pull the image from the repository!' % hub)
		ret, out = call_process2(['docker', 'pull', self.image], logger=_logger)
		if ret != 0:
			raise DockerImagePullFailed(image=self.image, out=out, code=ret)

	def setup_docker_files(self):
		# only needed for MultiDocker
		pass

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
			os.chmod(tmp_file.name, 0o622)  # world writable for containers not using root as user
			tmp_file.container_path = tmp_file.name[len(path) - 1:]
			try:
				yield tmp_file
			finally:
				tmp_file.close()

	def execute_with_output(self, *args, **kwargs):
		args = list(args)
		for key, value in kwargs.items():
			args.extend(['--%s' % key, value])
		return execute_with_output(self.container, args)

	def execute(self, *args, **kwargs):
		args = list(args)
		logger = kwargs.pop('_logger', self.logger)
		logger = logger.getChild('container.%s' % self.container[:4])
		tty = kwargs.pop('_tty', None)
		logger.debug('Using container.%s for container %s' % (self.container[:4], self.container))
		for key, value in kwargs.items():
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
		os.chmod(env_file, 0o400)
		with os.fdopen(fd, 'w') as outfile:
			# appcenter env file
			if os.path.exists(self.app.get_cache_file('env')):
				with open(self.app.get_cache_file('env'), 'r') as infile:
					outfile.write(ucr_run_filter(infile.read()))
					outfile.write('\n')
			# env variables from appcenter
			for key, value in env.items():
				if value is None:
					continue
				if self.app.docker_ucr_style_env:
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
				volumes.add('/etc/apt/apt.conf.d/80proxy:/etc/apt/apt.conf.d/81proxy:ro')  # apt proxy
		env_file = self.ucr_filter_env_file(env)
		command = None
		if self.app.docker_script_init:
			command = shlex.split(ucr_run_filter(self.app.docker_script_init))
		args = shlex.split(ucr_get(self.app.ucr_docker_params_key, ''))
		for tmpfs in ("/run", "/run/lock"):                                 # systemd
			args.extend(["--tmpfs", tmpfs])
		seccomp_profile = "/etc/docker/seccomp-systemd.json"
		args.extend(["--security-opt", "seccomp:%s" % seccomp_profile])     # systemd
		args.extend(["-e", "container=docker"])                             # systemd
		ret, out = create(self.image, command, hostname, ports, volumes, env_file, args)
		if ret != 0:
			raise DockerCouldNotStartContainer(str(out))
		container = out.strip()
		if not container:
			raise DockerCouldNotStartContainer(str(out))
		ucr_save({self.app.ucr_container_key: container})
		self.container = container
		return container

	def commit(self, new_image_name):
		return commit(self.container, new_image_name)

	def stop(self):
		if self.container:
			return stop(self.container)

	def rm(self):
		if self.container:
			return rm(self.container)

	def rmi(self):
		image = self.image
		if image:
			return rmi(image)

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

	def _get_app_network(self):
		_logger.debug('Getting network for %s' % self.app)
		network = ucr_get(self.app.ucr_ip_key)
		if network and '/' in network:
			_logger.debug('Found %s' % network)
			try:
				network = IPv4Network(u'%s' % (network,), False)
			except ValueError as exc:
				_logger.warn('Error using the network %s: %s' % (network, exc))
				return None
			else:
				return network
		docker0_net = IPv4Network(u'%s' % (ucr_get('appcenter/docker/compose/network', '172.16.1.1/16'),), False)
		gateway, netmask = docker0_net.exploded.split('/', 1)  # '172.16.1.1', '16'
		used_docker_networks = []
		for _app in Apps().get_all_apps():  # TODO: find container not managed by the App Center?
			if _app.id == self.app.id:
				continue
			ip = ucr_get(_app.ucr_ip_key)
			try:
				app_network = IPv4Network(u'%s' % (ip,), False)
			except ValueError:
				continue
			else:
				used_docker_networks.append(app_network)
		prefixlen_diff = 24 - int(netmask)
		if prefixlen_diff <= 0:
			_logger.warn('Cannot get a subnet big enough')  # maybe I could... but currently, I only work with 24-netmasks
			return None
		for network in docker0_net.subnets(prefixlen_diff):  # 172.16.1.1/24, 172.16.2.1/24, ..., 172.16.255.1/24
			_logger.debug('Testing %s' % network)
			if IPv4Address(u'%s' % (gateway,)) in network:
				_logger.debug('Refusing due to "main subnet"')
				continue
			if any(app_network.overlaps(network) for app_network in used_docker_networks):
				_logger.debug('Refusing due to range already used')
				continue
			return network
		_logger.warn('Cannot find any viable subnet')

	def backup_run_file(self):
		pass


class MultiDocker(Docker):
	def pull(self):
		self.setup_docker_files()
		self.logger.info('Downloading app images')
		ret, out = call_process2(['docker-compose', '-p', self.app.id, 'pull'], cwd=self.app.get_compose_dir(), logger=_logger)
		if ret != 0:
			raise DockerImagePullFailed(image=self.image, out=out, code=ret)

	def setup_docker_files(self):
		self._setup_env()
		self._setup_yml(recreate=True)

	def _app_volumes(self):
		volumes = self.app.docker_volumes[:]
		for app_volume in [self.app.get_data_dir(), self.app.get_conf_dir()]:
			app_volume = '%s:%s' % (app_volume, app_volume)
			volumes.append(app_volume)
		if self.app.host_certificate_access:
			cert_dir = '/etc/univention/ssl/%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
			cert_volume = '%s:%s:ro' % (cert_dir, cert_dir)
			volumes.append(cert_volume)
		return unique(volumes)

	def _setup_yml(self, recreate, env=None):
		env = env or {}
		yml_file = self.app.get_compose_file('docker-compose.yml')
		yml_run_file = '%s.run' % yml_file
		if not recreate:
			if os.path.exists(yml_file):
				return
			elif os.path.exists(yml_run_file):
				shutil.move(yml_run_file, yml_file)
				return
		template_file = '%s.template' % yml_file
		mkdir(self.app.get_compose_dir())
		shutil.copy2(self.app.get_cache_file('compose'), template_file)
		with open(template_file) as fd:
			template = fd.read()
			content = ucr_run_filter(template, env)
		with open(yml_file, 'w') as fd:
			os.chmod(yml_file, 0o600)
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
		prots = {}
		ip_addresses = None
		if 'networks' not in content:
			network = self._get_app_network()
			if network:
				content['networks'] = {
					'appcenter_net': {
						'ipam': {
							'driver': 'default',
							'config': [{'subnet': network.compressed}]
						}
					}
				}
				ucr_save({self.app.ucr_ip_key: str(network)})
				ip_addresses = network.hosts()  # iterator!
				next(ip_addresses)  # first one for docker gateway
		for service_name, service in content['services'].items():
			exposed_ports[service_name] = (int(port) for port in service.get('expose', []))
			used_ports[service_name] = {}
			for port in service.get('ports', []):
				prot = None
				if '/' in str(port):
					port, prot = port.split('/', 1)
				try:
					_port = int(port)
				except ValueError:
					host_port, container_port = (int(_port) for _port in port.split(':'))
					used_ports[service_name][container_port] = host_port
					if prot:
						prots[container_port] = prot
				else:
					used_ports[service_name][_port] = _port
					if prot:
						prots[_port] = prot
			if ip_addresses and not service.get('networks') and service.get('network_mode') != 'bridge':
				service['networks'] = {'appcenter_net': {'ipv4_address': str(next(ip_addresses))}}
		if 'environment' not in container_def:
			container_def['environment'] = {}
		if isinstance(container_def['environment'], list):
			for key, val in env.items():
				container_def['environment'].append('{}={}'.format(key, val))
		else:
			container_def['environment'].update(env)
		for app_id, container_port, host_port in app_ports():
			if app_id != self.app.id:
				continue
			for service_name, ports in exposed_ports.items():
				if container_port in ports:
					used_ports[service_name][container_port] = host_port
					break
			else:
				for service_name, ports in used_ports.items():
					if container_port in ports:
						used_ports[service_name][container_port] = host_port
						break
				else:
					used_ports[self.app.docker_main_service][container_port] = host_port
		for service_name, ports in used_ports.items():
			content['services'][service_name]['ports'] = list()
			for container_port, host_port in ports.items():
				if prots.get(container_port):
					container_port = '{}/{}'.format(container_port, prots[container_port])
				content['services'][service_name]['ports'].append('{}:{}'.format(host_port, container_port))

		if self.env_file_created and self.app.docker_inject_env_file is not None:
			for service_name, service in content['services'].items():
				if (self.app.docker_inject_env_file == 'main' and service_name == self.app.docker_main_service) or (self.app.docker_inject_env_file == 'all'):
					if service.get('env_file'):
						if self.env_file_created not in service['env_file']:
							service['env_file'].append(self.env_file_created)
					else:
						service['env_file'] = list()
						service['env_file'].append(self.env_file_created)
		with open(yml_file, 'w') as fd:
			yaml.dump(content, fd, Dumper=yaml.RoundTripDumper, encoding='utf-8', allow_unicode=True)
		shutil.copy2(yml_file, yml_run_file)  # "backup"

	def _setup_env(self, env=None):
		if os.path.exists(self.app.get_cache_file('env')) and self.app.docker_inject_env_file:
			mkdir(self.app.get_compose_dir())
			env_file_name = '{}.env'.format(self.app.id)
			env_file = os.path.join(self.app.get_compose_dir(), env_file_name)
			# remove old env file
			try:
				os.remove(env_file)
			except OSError:
				pass
			# create new env file
			fd = os.open(env_file, os.O_RDWR | os.O_CREAT)
			os.chmod(env_file, 0o400)
			with os.fdopen(fd, 'w') as outfile:
				with open(self.app.get_cache_file('env'), 'r') as infile:
					outfile.write(ucr_run_filter(infile.read(), env))
					outfile.write('\n')
			self.env_file_created = env_file_name

	def _get_main_service_container_id(self):
		name = None
		yml_file = self.app.get_compose_file('docker-compose.yml')
		content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
		# name from yaml
		if content['services'][self.app.docker_main_service].get('container_name'):
			name = content['services'][self.app.docker_main_service]['container_name']
		else:
			# name from docker-compose ps
			ps = str()
			for i in range(3):
				try:
					# by using a pipe to 'bash -s' COLUMNS is unset and the terminal and the table
					# is never line-wrapped.
					ps = check_output(['bash', '-s']
						input=str.encode(
						    ' '.join(['echo', 'docker-compose', '-p', self.app.id, 'ps'])
						), cwd=self.app.get_compose_dir()
					)
					break
				except Exception as e:
					_logger.warn('docker-compose ps for app {} failed: {}'.format(self.app.id, e))
					time.sleep(5)
			for line in ps.splitlines():
				line = line.decode('utf-8')
				c_name = line.split(' ', 1)[0]
				if '_{}_'.format(self.app.docker_main_service) in c_name:
					name = c_name
		# default
		if name is None:
			name = '{}_{}_1'.format(self.app.id, self.app.docker_main_service)
		# get containert id
		for i in range(3):
			try:
				insp = inspect(name)
				return insp['Id']
			except Exception as e:
				_logger.warn('Inspect for main service container {} failed: {}'.format(name, e))
				time.sleep(5)
		return None

	def create(self, hostname, env):
		env = {k: yaml.scalarstring.DoubleQuotedScalarString(v) for k, v in env.items() if v is not None}
		if self.app.docker_ucr_style_env:
			env.update({shell_safe(k).upper(): v for k, v in env.items()})
		else:
			env = {shell_safe(k).upper(): v for k, v in env.items()}
		self._setup_env(env=env)
		self._setup_yml(recreate=True, env=env)
		ret, out_up = call_process2(['docker-compose', '-p', self.app.id, 'up', '-d', '--no-build', '--no-recreate'], cwd=self.app.get_compose_dir())
		if ret != 0:
			raise DockerCouldNotStartContainer(out_up)
		self.container = self._get_main_service_container_id()
		if self.container is None:
			try:
				out_ps = ps(only_running=True)
			except Exception as e:
				out_ps = str(e)
			raise DockerCouldNotStartContainer('could not find container for service %s! docker-ps: %s docker-compose: %s)' % (self.app.docker_main_service, out_ps, out_up))
		else:
			ucr_save({self.app.ucr_container_key: self.container})
			return self.container

	def start(self):
		self._setup_yml(recreate=False)
		return call_process(['docker-compose', '-p', self.app.id, 'start'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0

	def stop(self):
		self._setup_yml(recreate=False)
		return call_process(['docker-compose', '-p', self.app.id, 'stop'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0

	def restart(self):
		self._setup_yml(recreate=False)
		return call_process(['docker-compose', '-p', self.app.id, 'restart'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0

	def rm(self):
		ret = self.stop()
		ret = ret and call_process(['docker-compose', '-p', self.app.id, 'down', '--remove-orphans'], logger=self.logger, cwd=self.app.get_compose_dir()).returncode == 0
		return ret

	def rmi(self):
		images = []
		yml_file = self.app.get_compose_file('docker-compose.yml.bak')
		content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
		services = content.get('services', {})
		for service in services.values():
			image = service.get('image')
			if image not in images:
				images.append(image)
		if images:
			return rmi(*images)

	def backup_run_file(self):
		try:
			yml_file = self.app.get_compose_file('docker-compose.yml')
			yml_bak_file = '%s.bak' % yml_file
			shutil.copy2(yml_file, yml_bak_file)
		except EnvironmentError as exc:
			_logger.warn('Could not backup docker-compose.yml: %s' % exc)
