#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app mixin for dockerized actions
#
# Copyright 2015-2019 Univention GmbH
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

import shutil
import os.path
import re
import time

from ldap.dn import explode_dn

from univention.appcenter.docker import Docker, MultiDocker
from univention.appcenter.database import DatabaseConnector, DatabaseError
from univention.appcenter.actions import get_action
from univention.appcenter.exceptions import DockerCouldNotStartContainer, DatabaseConnectorError, AppCenterErrorContainerStart
from univention.appcenter.actions.service import Start, Stop, Status
from univention.appcenter.utils import mkdir  # get_locale
from univention.appcenter.ucr import ucr_keys, ucr_get, ucr_is_true
from univention.appcenter.log import LogCatcher, get_logfile_logger


BACKUP_DIR = '/var/lib/univention-appcenter/backups'


class DockerActionMixin(object):

	@classmethod
	def _get_docker(cls, app):
		if not app.docker:
			return
		if app.uses_docker_compose():
			return MultiDocker(app, cls.logger)
		return Docker(app, cls.logger)

	def _store_data(self, app):
		if app.docker_script_store_data:
			process = self._execute_container_script(app, 'store_data', credentials=False)
			if not process or process.returncode != 0:
				self.fatal('Image upgrade script (pre) failed')
				return False
		return True

	def _backup_container(self, app, remove=False):
		docker = self._get_docker(app)
		if docker.exists():
			if not Start.call(app=app):
				self.fatal('Starting the container for %s failed' % app)
				return False
			if not self._store_data(app):
				self.fatal('Storing data for %s failed' % app)
				return False
			if not Stop.call(app=app):
				self.fatal('Stopping the container for %s failed' % app)
				return False
			if remove:
				# New backup
				image_repo = 'appcenter-backup-%s' % app.id
				image_name = '%s:%d' % (image_repo, time.time())
				shutil.move(app.get_conf_dir(), os.path.join(BACKUP_DIR, image_name, 'conf'))
		else:
			self.fatal('No container found. Unable to run store_data!')

	def _execute_container_script(self, app, interface, args=None, credentials=True, output=False, cmd_args=None, cmd_kwargs=None):
		cmd_args = cmd_args or []
		cmd_kwargs = cmd_kwargs or {}
		self.log('Executing interface %s for %s' % (interface, app.id))
		docker = self._get_docker(app)
		interface_file = getattr(app, 'docker_script_%s' % interface)
		if not interface_file:
			self.log('No interface defined')
			return None
		remote_interface_script = app.get_cache_file(interface)
		container_interface_script = docker.path(interface_file)
		if os.path.exists(remote_interface_script):
			self.log('Copying App Center\'s %s to container\'s %s' % (interface, interface_file))
			mkdir(os.path.dirname(container_interface_script))
			shutil.copy2(remote_interface_script, container_interface_script)
			os.chmod(container_interface_script, 0o755)  # -rwxr-xr-x
		if not os.path.exists(container_interface_script):
			self.warn('Interface script %s not found!' % interface_file)
			return None
		with docker.tmp_file() as error_file:
			with docker.tmp_file() as password_file:
				if credentials:
					self._get_ldap_connection(args, allow_machine_connection=False, allow_admin_connection=False)  # to get a working username/password
					username = self._get_username(args)
					password = self._get_password(args)
					with open(password_file.name, 'w') as f:
						f.write(password)
					cmd_kwargs['username'] = username
					cmd_kwargs['password_file'] = password_file.container_path
				cmd_kwargs['error_file'] = error_file.container_path
				cmd_kwargs['app'] = app.id
				cmd_kwargs['app_version'] = app.version
				# locale = get_locale()
				# if locale:
				#	cmd_kwargs['locale'] = locale
				cmd_kwargs['_tty'] = False
				if output:
					logger = LogCatcher(self.logger)
					cmd_kwargs['_logger'] = logger
				process = docker.execute(interface_file, *cmd_args, **cmd_kwargs)
				if process.returncode != 0:
					with open(error_file.name, 'r+b') as error_handle:
						for line in error_handle:
							self.fatal(line)
				if output:
					return process, logger
				return process

	def _copy_files_into_container(self, app, *filenames):
		docker = self._get_docker(app)
		for filename in filenames:
			if filename:
				self.debug('Copying %s into container' % filename)
				shutil.copy2(filename, docker.path(filename))

	def _start_docker_image(self, app, hostdn, password, args):
		docker = self._get_docker(app)
		if not docker:
			return

		self.log('Verifying Docker registry manifest for app image %s' % docker.image)
		docker.verify()

		if args.pull_image:
			docker.pull()

		self.log('Initializing app image')
		hostname = explode_dn(hostdn, 1)[0]
		set_vars = (args.set_vars or {}).copy()
		after_image_configuration = {}
		for setting in app.get_settings():
			if setting.should_go_into_image_configuration(app):
				if setting.name not in set_vars:
					set_vars[setting.name] = setting.get_initial_value(app)
			else:
				try:
					after_image_configuration[setting.name] = set_vars.pop(setting.name)
				except KeyError:
					after_image_configuration[setting.name] = setting.get_initial_value(app)
		set_vars['docker/host/name'] = '%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
		set_vars['ldap/hostdn'] = hostdn
		if app.docker_env_ldap_user:
			set_vars[app.docker_env_ldap_user] = hostdn
		set_vars['server/role'] = app.docker_server_role
		set_vars['update/warning/releasenotes'] = 'no'
		ucr_keys_list = list(ucr_keys())
		for var in ['nameserver.*', 'repository/online/server', 'repository/app_center/server', 'update/secure_apt', 'appcenter/index/verify', 'ldap/base', 'ldap/server.*', 'ldap/master.*', 'locale.*', 'domainname']:
			for key in ucr_keys_list:
				if re.match(var, key):
					set_vars[key] = ucr_get(key)
		if ucr_is_true('appcenter/docker/container/proxy/settings', default=True):
			if ucr_get('proxy/http'):
				set_vars['proxy/http'] = ucr_get('proxy/http')
				set_vars['http_proxy'] = ucr_get('proxy/http')
			if ucr_get('proxy/https'):
				set_vars['proxy/https'] = ucr_get('proxy/https')
				set_vars['https_proxy'] = ucr_get('proxy/https')
			if ucr_get('proxy/no_proxy'):
				set_vars['proxy/no_proxy'] = ucr_get('proxy/no_proxy')
				set_vars['no_proxy'] = ucr_get('proxy/no_proxy')
		set_vars['updater/identify'] = 'Docker App'
		database_connector = DatabaseConnector.get_connector(app)
		database_password_file = None
		if database_connector:
			try:
				database_password = database_connector.get_db_password()
				database_password_file = database_connector.get_db_password_file()
				if database_password:
					set_vars[app.docker_env_database_host] = database_connector.get_db_host()
					db_port = database_connector.get_db_port()
					if db_port:
						set_vars[app.docker_env_database_port] = db_port
					set_vars[app.docker_env_database_name] = database_connector.get_db_name()
					set_vars[app.docker_env_database_user] = database_connector.get_db_user()
					if app.docker_env_database_password_file:
						set_vars[app.docker_env_database_password_file] = database_password_file
					else:
						set_vars[app.docker_env_database_password] = database_password
				autostart_variable = database_connector.get_autostart_variable()
				if autostart_variable:
					set_vars[autostart_variable] = 'no'
			except DatabaseError as exc:
				raise DatabaseConnectorError(str(exc))

		container = docker.create(hostname, set_vars)
		self.log('Preconfiguring container %s' % container)
		autostart = 'yes'
		if not Start.call(app=app):
			raise DockerCouldNotStartContainer(str(Status.get_status(app)))
		time.sleep(3)
		if not docker.is_running():
			dlogs = docker.dockerd_logs()
			clogs = docker.logs()
			inspect = docker.inspect_container()
			msg = """
The container for {app} could not be started!

docker logs {container}:
{clogs}

dockerd logs:
{dlogs}

docker inspect:
{state}
{graphdriver}""".format(
				app=app, container=docker.container,
				clogs=clogs, dlogs=dlogs,
				state=inspect.get('State'),
				graphdriver=inspect.get('GraphDriver')
			)
			raise AppCenterErrorContainerStart(msg)
		# copy password files
		if os.path.isfile(app.secret_on_host):
			# we can not use docker-cp here, as we support read-only containers too :-(
			f_name = docker.path('/etc/machine.secret')
			f_dir = os.path.dirname(f_name)
			# if the container start takes a little longer the f_dir may not exist yet
			# so wait max 60s
			for i in xrange(0, 12):
				if os.path.isdir(f_dir):
					break
				time.sleep(5)
			try:
				with open(f_name, 'w+b') as f:
					os.chmod(f_name, 0o600)
					f.write(password)
			except Exception as exc:
				raise DockerCouldNotStartContainer('Could not copy machine.secret to container: %s (%s)' % (str(exc), docker.logs()))
		if database_password_file:
			docker.cp_to_container(database_password_file, database_password_file)
		# update timezone in container
		logfile_logger = get_logfile_logger('docker.base')
		docker.execute('rm', '-f', '/etc/timezone', '/etc/localtime', _logger=logfile_logger)
		docker.cp_to_container('/etc/timezone', '/etc/timezone', _logger=logfile_logger)
		docker.cp_to_container('/etc/localtime', '/etc/localtime', _logger=logfile_logger)
		# configure app
		after_image_configuration.update(set_vars)
		configure = get_action('configure')
		configure.call(app=app, autostart=autostart, run_script='no', set_vars=after_image_configuration)
