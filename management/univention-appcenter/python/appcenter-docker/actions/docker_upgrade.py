#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for upgrading an app
#  (docker version)
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

from univention.appcenter.docker import rm as docker_rm
from univention.appcenter.actions import Abort, get_action
from univention.appcenter.actions.upgrade import Upgrade
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.docker_install import Install
from univention.appcenter.actions.service import Start
from univention.appcenter.actions.configure import Configure, StoreConfigAction
from univention.appcenter.ucr import ucr_save, ucr_keys, ucr_get


class Upgrade(Upgrade, Install, DockerActionMixin):
	def setup_parser(self, parser):
		super(Upgrade, self).setup_parser(parser)
		parser.add_argument('--set', nargs='+', action=StoreConfigAction, metavar='KEY=VALUE', dest='set_vars', help='Sets the configuration variable. Example: --set some/variable=value some/other/variable="value 2"')
		parser.add_argument('--do-not-backup', action='store_false', dest='backup', help='For docker apps, do not save a backup container')

	def __init__(self):
		super(Upgrade, self).__init__()
		self._had_image_upgrade = False

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
		if not self.old_app.docker:
			return 'docker'
		if not Start.call(app=self.old_app):
			raise Abort('Could not start the app container. It needs to be running to be upgraded!')
		mode = self._execute_container_script(self.old_app, 'update_available', _credentials=False, _output=True) or ''
		mode = mode.strip()
		if mode != 'packages' and not mode.startswith('release:'):
			# packages and release first!
			if app > self.old_app:
				mode = 'app'
			if self.old_app.get_docker_image_name() not in app.get_docker_images():
				mode = 'image'
		return mode

	def _do_it(self, app, args):
		if not app.docker:
			return super(Upgrade, self)._do_it(app, args)
		mode = self._docker_upgrade_mode(app)
		if mode:
			self.log('Upgrading %s' % mode)
			if mode == 'packages':
				self._upgrade_packages(app)
			elif mode.startswith('release:'):
				release = mode[8:].strip()
				self._upgrade_release(app, release)
			elif mode == 'app':
				self._upgrade_app(app, args)
			elif mode == 'image':
				self._upgrade_image(app, args)
			elif mode == 'docker':
				self._upgrade_docker(app, args)
			else:
				self.warn('Unable to process %r' % (mode,))
				return
			self._do_it(app, args)
		else:
			self.log('Nothing to upgrade')

	def _upgrade_packages(self, app):
		process = self._execute_container_script(app, 'update_packages', _credentials=False)
		if not process or process.returncode != 0:
			raise Abort('Package upgrade script failed')

	def _upgrade_release(self, app, release):
		process = self._execute_container_script(app, 'update_release', _credentials=False, release=release)
		if not process or process.returncode != 0:
			raise Abort('Release upgrade script failed')

	def _upgrade_app(self, app, args):
		process = self._execute_container_script(app, 'update_app_version', args)
		if not process or process.returncode != 0:
			raise Abort('App upgrade script failed')
		self._register_app(app, args)
		self.old_app = app

	def _get_config(self, app, args):
		config = Configure.list_config(app)
		set_vars = dict((var['id'], var['value']) for var in config)
		if args.set_vars:
			set_vars.update(args.set_vars)
		return set_vars

	def _upgrade_image(self, app, args):
		docker = self._get_docker(app)

		self.log('Verifying Docker registry manifest for app image %s' % docker.image)
		docker.verify()

		docker.pull()
		self.log('Saving data from old container (%s)' % self.old_app)
		old_docker = self._get_docker(self.old_app)
		old_container = old_docker.container
		if self._backup_container(self.old_app, backup_data='copy') is False:
			raise Abort('Could not backup container!')
		self.log('Setting up new container (%s)' % app)
		ucr_save({app.ucr_image_key: None})
		args.set_vars = self._get_config(self.old_app, args)
		self._install_new_app(app, args)
		self.log('Removing old container')
		if old_container:
			docker_rm(old_container)
		self._register_app(app, args)
		self.old_app = app
		self._had_image_upgrade = True

	def _upgrade_docker(self, app, args):
		install = get_action('install')()
		action_args = install._build_namespace(_namespace=args, app=app, set_vars=self._get_config(app, args), send_info=False, skip_checks=['must_not_be_installed'])
		install.call_with_namespace(action_args)
		ucr_app_values = {}
		for key in ucr_keys():
			if key.startswith('appcenter/apps/%s/' % app.id):
				value = ucr_get(key)
				ucr_app_values[key] = value
		remove = get_action('remove')()
		action_args = remove._build_namespace(_namespace=args, app=self.old_app, send_info=False)
		remove.call_with_namespace(action_args)
		ucr_save(ucr_app_values)
		self._register_app(app, args)
		self.old_app = app

	def _revert(self, app, args):
		if self._had_image_upgrade:
			try:
				remove = get_action('remove')
				install = get_action('install')
				password = self._get_password(args, ask=False)
				remove.call(app=app, noninteractive=args.noninteractive, username=args.username, password=password, send_info=False, skip_checks=[], backup=False)
				install.call(app=self.old_app, noninteractive=args.noninteractive, username=args.username, password=password, send_info=False, skip_checks=[])
			except Exception:
				pass
		else:
			Start.call(app=self.old_app)
