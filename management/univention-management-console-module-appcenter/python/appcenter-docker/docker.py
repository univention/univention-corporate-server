#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  appcenter docker glue
#
# Copyright 2015 Univention GmbH
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

from subprocess import check_output, call, CalledProcessError
import os.path
import shlex
from json import loads
import time

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update

from univention.appcenter.utils import app_ports, call_process, mkdir, shell_safe
from univention.appcenter.log import get_base_logger

CONTAINER_SCRIPTS_PATH = '/usr/share/univention-docker-container-mode/'

_logger = get_base_logger().getChild('docker')

class ImageDown(Exception):
	pass

def inspect(name):
	out = check_output(['docker', 'inspect', name])
	return loads(out)[0]

def pull(image):
	call(['docker', 'pull', image])

def ps(only_running=True):
	args = ['docker', 'ps', '--no-trunc=true']
	if not only_running:
		args.append('--all')
	return check_output(args)

def execute_with_output(container, args):
	args = ['docker', 'exec', container] + args
	return check_output(args)

def execute_with_process(container, args, logger=None):
	if logger is None:
		logger = _logger

	args = ['docker', 'exec', container] + args
	return call_process(args, logger)

def create(image, command, hostname=None, env=None, ports=None, volumes=None):
	args = []
	if hostname:
		args.extend(['--hostname', hostname])
	if env:
		for key, value in env.iteritems():
			args.extend(['-e', '%s=%s' % (shell_safe(key), value)])
			args.extend(['-e', '%s=%s' % (shell_safe(key).upper(), value)])
	if ports:
		for port in ports:
			args.extend(['-p', port])
	for volume in volumes:
		args.extend(['-v', volume])
	return check_output(['docker', 'create'] + args + [image] + command).strip()

def wait_for_runlevel2(container):
	i = 0
	while i < 30:
		try:
			run_level = execute_with_output(container, ['runlevel'])
		except CalledProcessError:
			pass
		else:
			if run_level.endswith('2\n'):
				break
		time.sleep(1)
		i += 1
	else:
		raise ImageDown(container)

def rm(container):
	return call(['docker', 'rm', container])

def commit(container, new_base_image):
	return call(['docker', 'commit', container, new_base_image])

class Docker(object):
	def __init__(self, app, logger=None):
		self.app = app
		ucr = ConfigRegistry()
		ucr.load()
		self.logger = logger or _logger
		self.container = ucr.get(self.app.ucr_container_key)

	def inspect_image(self):
		return inspect(self.image)

	def inspect_container(self):
		return inspect(self.container)

	@property
	def image(self):
		return self.app.get_docker_image_name()

	def is_running(self):
		if self.container:
			out = ps(only_running=True)
			for line in out.splitlines():
				if line.startswith(self.container):
					return True
		return False

	def pull(self):
		return pull(self.image)

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
		return os.path.join('/var/lib/docker/aufs/mnt', self.container, filename)

	def path_not_running(self, filename='', create=True):
		if self.container is None:
			return
		if filename.startswith('/'):
			filename = filename[1:]
		fname = os.path.join('/var/lib/docker/aufs/diff', self.container, filename)
		if create:
			mkdir(os.path.dirname(fname))
		return fname

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
		command = shlex.split(self.app.docker_script_init)
		container = create(self.image, command, hostname, env, ports, volumes)
		ucr = ConfigRegistry()
		ucr_update(ucr, {self.app.ucr_container_key: container})
		self.container = container
		return container

	def commit(self, new_image_name):
		return commit(self.container, new_image_name)

	def rm(self):
		return rm(self.container)

