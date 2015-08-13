#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for upgrading an app
#  (docker version)
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

from univention.appcenter.docker import Docker
from univention.appcenter.docker import rm as docker_rm
from univention.appcenter.actions import Abort
from univention.appcenter.actions.upgrade import Upgrade
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.docker_install import Install
from univention.appcenter.actions.docker_remove import Remove
from univention.appcenter.actions.service import Start, Stop
from univention.appcenter.actions.configure import Configure

class Upgrade(Upgrade, Install, DockerActionMixin):
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
		if not Start.call(app=self.old_app):
			self.fatal('Could not start the app container. It needs to be running to be upgraded!')
			raise Abort()
		mode = self._execute_container_script(self.old_app, 'update_available', _credentials=False, _output=True)
		if mode:
			mode = mode.strip()
		if mode != 'packages' and not mode.startswith('release:'):
			# packages and release first!
			if app > self.old_app:
				mode = 'app'
			if app.get_docker_image_name() != self.old_app.get_docker_image_name():
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
			self._do_it(app, args)
		else:
			self.log('Nothing to upgrade')

	def _upgrade_packages(self, app):
		process = self._execute_container_script(app, 'update_packages', _credentials=False)
		if not process or process.returncode != 0:
			self.fatal('Package upgrade script failed')
			raise Abort()

	def _upgrade_release(self, app, release):
		process = self._execute_container_script(app, 'update_release', _credentials=False, release=release)
		if not process or process.returncode != 0:
			self.fatal('Release upgrade script failed')
			raise Abort()

	def _upgrade_app(self, app, args):
		process = self._execute_container_script(app, 'update_app_version', args)
		if not process or process.returncode != 0:
			self.fatal('App upgrade script failed')
			raise Abort()
		self.old_app = app

	def _upgrade_image(self, app, args):
		docker = Docker(app, self.logger)
		docker.pull()
		self.log('Saving data from old container (%s)' % self.old_app)
		old_docker = Docker(self.old_app, self.logger)
		old_container = old_docker.container
		config = Configure.list_config(self.old_app)
		process = self._execute_container_script(self.old_app, 'store_data', _credentials=False)
		if not process or process.returncode != 0:
			self.fatal('Image upgrade script (pre) failed')
			raise Abort()
		self.log('Stopping old container')
		Stop.call(app=self.old_app)
		self.log('Setting up new container (%s)' % app)
		args.set_vars = dict((var['id'], var['value']) for var in config)
		self._install_new_app(app, args)
		self.log('Removing old container')
		if old_container:
			docker_rm(old_container)
		self.old_app = app
		self._had_image_upgrade = True

	def _revert(self, app, args):
		if self._had_image_upgrade:
			try:
				Remove.call(app=app, noninteractive=args.noninteractive, username=args.username, pwdfile=args.pwdfile, send_info=False, skip_checks=[], keep_data=False)
				Install.call(app=self.old_app, noninteractive=args.noninteractive, username=args.username, pwdfile=args.pwdfile, send_info=False, skip_checks=[])
			except Exception:
				pass
		else:
			Start.call(app=self.old_app)

