#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for upgrading an app
#  (docker version)
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

from univention.appcenter.app_cache import Apps
from univention.appcenter.actions import get_action
from univention.appcenter.exceptions import UpgradeStartContainerFailed, UpgradePackagesFailed, UpgradeReleaseFailed, UpgradeAppFailed, UpgradeBackupFailed
from univention.appcenter.actions.upgrade import Upgrade
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.docker_install import Install
from univention.appcenter.actions.service import Start
from univention.appcenter.ucr import ucr_save, ucr_get
from univention.appcenter.packages import update_packages


class Upgrade(Upgrade, Install, DockerActionMixin):

	def setup_parser(self, parser):
		super(Upgrade, self).setup_parser(parser)
		parser.add_argument('--do-not-pull-image', action='store_false', dest='pull_image', help='Do not pull the image of a Docker App. Instead, the image is assumed to be already in place')
		parser.add_argument('--do-not-backup', action='store_false', dest='backup', help='For docker apps, do not save a backup container')
		parser.add_argument('--do-not-remove-image', action='store_false', dest='remove_image', help='For docker apps, do not remove the leftover image after the upgrade')

	def __init__(self):
		super(Upgrade, self).__init__()
		self._had_image_upgrade = False
		self._last_mode = None

	def _app_too_old(self, current_app, specified_app):
		if not current_app.docker:
			return super(Upgrade, self)._app_too_old(current_app, specified_app)
		if current_app > specified_app:
			self.fatal('The app you specified is older than the currently installed app')
			return True
		return False

	def _install_new_app(self, app, args):
		return Install._do_it(self, app, args)

	def _docker_upgrade_mode(self, app):
		mode = None
		detail = None
		if self.old_app.docker and app.plugin_of:
			if app > self.old_app:
				mode, detail = 'app', app.version
			return mode, detail
		if not self.old_app.docker:
			return 'docker', None
		if not Start.call(app=self.old_app):
			raise UpgradeStartContainerFailed()
		# update proxy settings
		if app.docker:
			aucr = get_action('configure')()
			pvars = dict()
			for psetting in ['proxy/http', 'proxy/https', 'proxy/no_proxy']:
				pvars[psetting] = ucr_get(psetting)
			aucr._set_config_via_tool(app, pvars)
		result = self._execute_container_script(app, 'update_available', credentials=False, output=True)
		if result is not None:
			process, log = result
			if process.returncode != 0:
				self.fatal('%s: Searching for App upgrade failed!' % app)
				return None, None
			mode = '\n'.join(log.stdout())
			if mode:
				mode = mode.strip()
		else:
			mode = ''
		if mode.startswith('release:'):
			mode, detail = 'release', mode[8:].strip()
		if mode not in ['packages', 'release']:
			# packages and release first!
			if app > self.old_app:
				mode, detail = 'app', app.version
			if self.old_app.get_docker_image_name() not in app.get_docker_images():
				mode, detail = 'image', app.get_docker_image_name()
		return mode, detail

	def _do_it(self, app, args):
		if not app.docker:
			return super(Upgrade, self)._do_it(app, args)
		mode, detail = self._docker_upgrade_mode(app)
		if mode:
			self.log('Upgrading %s (%r)' % (mode, detail))
			if self._last_mode == (mode, detail):
				self.warn('Not again!')
				return
			if mode == 'packages':
				self._upgrade_packages(app, args)
			elif mode == 'release':
				self._upgrade_release(app, detail)
			elif mode == 'app':
				self._upgrade_app(app, args)
			elif mode == 'image':
				self._upgrade_image(app, args)
			elif mode == 'docker':
				self._upgrade_docker(app, args)
			else:
				self.fatal('Unable to process %r' % (mode,))
				return
			self._last_mode = mode, detail
			ucr_save({'appcenter/prudence/docker/%s' % app.id: None})
			self._do_it(app, args)
		else:
			self.log('Nothing to upgrade')

	def _upgrade_packages(self, app, args):
		process = self._execute_container_script(app, 'update_packages', args)
		if not process or process.returncode != 0:
			raise UpgradePackagesFailed()

	def _upgrade_release(self, app, release):
		process = self._execute_container_script(app, 'update_release', credentials=False, cmd_kwargs={'release': release})
		if not process or process.returncode != 0:
			raise UpgradeReleaseFailed()

	def _upgrade_app(self, app, args):
		process = self._execute_container_script(app, 'update_app_version', args)
		if not process or process.returncode != 0:
			raise UpgradeAppFailed()
		self._register_app(app, args)
		self._configure(app, args)
		self._call_join_script(app, args)
		self.old_app = app

	def _upgrade_image(self, app, args):
		docker = self._get_docker(app)

		self.log('Verifying Docker registry manifest for app image %s' % docker.image)
		docker.verify()
		self.log('Pulling Docker image %s' % docker.image)
		docker.backup_run_file()
		docker.pull()
		self.log('Saving data from old container (%s)' % self.old_app)
		Start.call(app=self.old_app)
		settings = self._get_configure_settings(self.old_app, filter_action=False)
		settings.update(args.set_vars or {})
		args.set_vars = settings
		old_docker = self._get_docker(self.old_app)
		old_docker.cp_from_container('/etc/machine.secret', app.secret_on_host)
		if self._backup_container(self.old_app) is False:
			raise UpgradeBackupFailed()
		self.log('Removing old container')
		if old_docker.container:
			old_docker.rm()
		self._had_image_upgrade = True
		self.log('Setting up new container (%s)' % app)
		ucr_save({app.ucr_image_key: None})
		old_configure = args.configure
		args.configure = False
		self._install_new_app(app, args)
		self._update_converter_service(app)
		args.configure = old_configure
		args.set_vars = settings
		self._configure(app, args)
		self._register_app(app, args)
		self._call_join_script(app, args)
		if args.remove_image:
			self.log('Trying to remove old image')
			try:
				if old_docker.rmi() != 0:
					self.log('Failed to remove old image. Continuing anyway...')
			except Exception as exc:
				self.warn('Error while removing old image: %s' % exc)
		self.old_app = app

	def _upgrade_docker(self, app, args):
		install = get_action('install')()
		action_args = install._build_namespace(_namespace=args, app=app, set_vars=self._get_configure_settings(self.old_app, filter_action=False), send_info=False, skip_checks=['must_not_be_installed'])
		if install.call_with_namespace(action_args):
			app_cache = Apps()
			for _app in app_cache.get_all_apps():
				if _app.plugin_of == app.id and _app.is_installed():
					_app = app_cache.find(_app.id, latest=True)
					if _app.docker:
						_old_app = self.old_app
						self._upgrade_docker(_app, args)
						self.old_app = _old_app
			remove = get_action('remove')()
			action_args = remove._build_namespace(_namespace=args, app=self.old_app, send_info=False, skip_checks=['must_not_be_depended_on'])
			remove._remove_app(self.old_app, action_args)
			if remove._unregister_component(self.old_app):
				update_packages()
			self._call_join_script(app, args)  # run again in case remove() called an installed unjoin script
			self.old_app = app

	def _revert(self, app, args):
		if self._had_image_upgrade:
			pass
			#try:
			#	remove = get_action('remove')
			#	install = get_action('install')
			#	password = self._get_password(args, ask=False)
			#	remove.call(app=app, noninteractive=args.noninteractive, username=args.username, password=password, send_info=False, skip_checks=[], backup=False)
			#	install.call(app=self.old_app, noninteractive=args.noninteractive, username=args.username, password=password, send_info=False, skip_checks=[])
			#except Exception:
			#	pass
		else:
			Start.call_safe(app=self.old_app)

	def dry_run(self, app, args):
		if not app.docker:
			return super(Upgrade, self).dry_run(app, args)
		self.log('%s is a Docker App. No sane dry run is implemented' % app)
