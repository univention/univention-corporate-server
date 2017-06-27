#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app mixin for dockerized actions
#
# Copyright 2015-2017 Univention GmbH
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

import shutil
import os.path
import re
import time

from ldap.dn import explode_dn

from univention.appcenter.docker import Docker
from univention.appcenter.database import DatabaseConnector, DatabaseError
from univention.appcenter.actions import Abort, get_action, AppCenterErrorContainerStart
from univention.appcenter.actions.service import Start, Stop
from univention.appcenter.utils import mkdir  # get_locale
from univention.appcenter.ucr import ucr_keys, ucr_get


BACKUP_DIR = '/var/lib/univention-appcenter/backups'


class DockerActionMixin(object):

	@classmethod
	def _get_docker(cls, app):
		if not app.docker:
			return
		return Docker(app, cls.logger)

	def _store_data(self, app):
		if app.docker_script_store_data:
			process = self._execute_container_script(app, 'store_data', _credentials=False)
			if not process or process.returncode != 0:
				self.fatal('Image upgrade script (pre) failed')
				return False
		return True

	def _backup_container(self, app, backup_data=False):
		docker = self._get_docker(app)
		if docker.exists():
			if not Start.call(app=app):
				self.fatal('Starting the container for %s failed' % app)
				return False
			if not self._store_data(app):
				self.fatal('Storing data for %s failed' % app)
				return False
			image_name = 'appcenter-backup-%s:%d' % (app.id, time.time())
			if backup_data == 'copy':
				shutil.copytree(app.get_data_dir(), os.path.join(BACKUP_DIR, image_name, 'data'), symlinks=True)
				shutil.copytree(app.get_conf_dir(), os.path.join(BACKUP_DIR, image_name, 'conf'), symlinks=True)
			elif backup_data == 'move':
				shutil.move(app.get_data_dir(), os.path.join(BACKUP_DIR, image_name, 'data'))
				shutil.move(app.get_conf_dir(), os.path.join(BACKUP_DIR, image_name, 'conf'))
			if not Stop.call(app=app):
				self.fatal('Stopping the container for %s failed' % app)
				return False
			image_id = docker.commit(image_name)
			self.log('Backed up %s as %s. ID: %s' % (app, image_name, image_id))
			return image_id
		else:
			self.fatal('No container found. Unable to backup')

	def _execute_container_script(self, _app, _interface, _args=None, _credentials=True, _output=False, **kwargs):
		self.log('Executing interface %s for %s' % (_interface, _app.id))
		docker = self._get_docker(_app)
		interface = getattr(_app, 'docker_script_%s' % _interface)
		if not interface:
			self.log('No interface defined')
			return None
		remote_interface_script = _app.get_cache_file(_interface)
		container_interface_script = docker.path(interface)
		if os.path.exists(remote_interface_script):
			self.log('Copying App Center\'s %s to container\'s %s' % (_interface, interface))
			mkdir(os.path.dirname(container_interface_script))
			shutil.copy2(remote_interface_script, container_interface_script)
			os.chmod(container_interface_script, 0o755)  # -rwxr-xr-x
		if not os.path.exists(container_interface_script):
			self.warn('Interface script %s not found!' % interface)
			return None
		with docker.tmp_file() as error_file:
			with docker.tmp_file() as password_file:
				if _credentials:
					self._get_ldap_connection(_args)  # to get a working username/password
					username = self._get_username(_args)
					password = self._get_password(_args)
					with open(password_file.name, 'w') as f:
						f.write(password)
					kwargs['username'] = username
					kwargs['password_file'] = password_file.container_path
				kwargs['error_file'] = error_file.container_path
				kwargs['app'] = _app.id
				kwargs['app_version'] = _app.version
				# locale = get_locale()
				# if locale:
				#	kwargs['locale'] = locale
				if _output:
					return docker.execute_with_output(interface, **kwargs)
				else:
					process = docker.execute(interface, **kwargs)
					if process.returncode != 0:
						with open(error_file.name, 'r+b') as error_handle:
							for line in error_handle:
								self.fatal(line)
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

		self.log('Downloading app image %s' % docker.image)
		docker.pull()

		self.log('Initializing app image')
		hostname = explode_dn(hostdn, 1)[0]
		set_vars = (args.set_vars or {}).copy()
		configure = get_action('configure')
		for variable in configure.list_config(app):
			if variable['value'] is not None and variable['id'] not in set_vars:
				set_vars[variable['id']] = variable['value']  # default
		set_vars['docker/host/name'] = '%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
		set_vars['ldap/hostdn'] = hostdn
		set_vars['server/role'] = app.docker_server_role
		set_vars['update/warning/releasenotes'] = 'no'
		ucr_keys_list = list(ucr_keys())
		for var in ['nameserver.*', 'repository/online/server', 'repository/app_center/server', 'update/secure_apt', 'appcenter/index/verify', 'ldap/master.*', 'locale.*', 'domainname']:
			for key in ucr_keys_list:
				if re.match(var, key):
					set_vars[key] = ucr_get(key)
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
				raise Abort(str(exc))

		container = docker.create(hostname, set_vars)
		self.log('Preconfiguring container %s' % container)
		autostart = 'yes'
		if not Start.call(app=app):
			raise Abort('Unable to start the container!')
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
{resolvconfpath}""".format(
				app=app, container=docker.container,
				clogs='\n'.join(clogs), dlogs='\n'.join(dlogs),
				state=inspect.get('State'),
				resolvconfpath=inspect.get('ResolvConfPath')
			)
			raise AppCenterErrorContainerStart(msg)
		if password:
			with open(docker.path('/etc/machine.secret'), 'w+b') as f:
				f.write(password)
		self._copy_files_into_container(app, '/etc/timezone', '/etc/localtime', database_password_file)
		configure.call(app=app, autostart=autostart, set_vars=set_vars)
