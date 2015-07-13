#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for installing an app
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

import os.path
from getpass import getuser, getpass

from univention.appcenter.actions import UniventionAppAction, StoreAppAction

from univention.config_registry import ConfigRegistry
from univention.lib.package_manager import PackageManager
from univention.updater import UniventionUpdater

class Install(UniventionAppAction):
	'''Installs or upgrades an application from the Univention App Center.'''
	help='Install/upgrade an app'

	_package_manager = None

	def __init__(self):
		super(Install, self).__init__()
		self._username = None
		self._password = None

	def setup_parser(self, parser):
		parser.add_argument('--noninteractive', action='store_true', help='Do not prompt for anything, just agree or skip')
		parser.add_argument('--username', help='The username used for registering the app. Defaults to the current user, but "root" is not viable. If in doubt, use "Administrator"')
		parser.add_argument('--pwdfile', help='Filename containing the password for registering the app. See --username')
		parser.add_argument('app', nargs='+', action=StoreAppAction, help='The ID of the app that shall be installed')

	def _get_username(self, args):
		if self._username is not None:
			return self._username
		if args.username:
			return args.username
		username = getuser()
		if username == 'root':
			# root is not appropriate for LDAP
			username = None
			if not args.noninteractive:
				username = raw_input('Username [Administrator]: ') or 'Administrator'
				self._username = username
		return username

	def _get_password(self, args):
		username = self._get_username(args)
		if not username:
			return None
		if self._password is not None:
			return self._password
		if args.pwdfile:
			return open(args.pwdfile).read()
		if not args.noninteractive:
			password = getpass('Password for %s: ' % username)
			self._password = password

	def _send_as_function(self):
		return 'install'

	@classmethod
	def _get_package_manager(cls):
		if cls._package_manager is None:
			cls._package_manager = PackageManager(info_handler=cls.log, error_handler=cls.warn)
			cls._package_manager.set_finished() # currently not working. accepting new tasks
		return cls._package_manager

	def _install_app_deb(self, app, args):
		from univention.management.console.modules.appcenter.util import ComponentManager
		ucr = ConfigRegistry()
		ucr.load()
		send_as = self._send_as_function()
		package_manager = self._get_package_manager()
		uu = UniventionUpdater(False)
		component_manager = ComponentManager(ucr, uu)
		username = self._get_username(args)
		password = self._get_password(args)
		app.install(package_manager, component_manager, send_as=send_as, username=username, password=password)

	def _show_license(self, app, args):
		return self._show_file(app, 'licenseagreement', args, agree=True) is not False

	def _show_readme_install(self, app, args):
		self._show_file(app, 'readmeinstall', args, confirm=True)

	def _show_readme_postinstall(self, app, args):
		self._show_file(app, 'readmepostinstall', args, confirm=True)

	def _show_file(self, app, attr, args, confirm=False, agree=False):
		filename = app.get('%s_file' % attr)
		if not filename or not os.path.exists(filename):
			return None
		self._subprocess(['elinks', '-dump', filename], 'readme')
		if not args.noninteractive:
			if agree:
				aggreed = raw_input('Do you agree [y/N]?')
				return aggreed.lower()[:1] in ['y', 'j']
			elif confirm:
				raw_input('Press [ENTER] to continue')
				return True
		return True

	def _check_app(self, app, args):
		package_manager = self._get_package_manager()
		hard, soft = app.check_invokation(self._send_as_function(), package_manager)
		can_continue = True
		if hard:
			self.fatal('Unable to install %s: %r. For a user friendly explanation, use the UMC module App Center' % (app.id, list(hard)))
			can_continue = False
		elif soft:
			self.warn('Not recommended to install %s: %r. For a user friendly explanation, use the UMC module App Center' % (app.id, list(soft)))
			if not args.noninteractive:
				override = raw_input('Do you want to continue anyway [y/N]?')
				can_continue = override.lower()[:1] == 'y'
		return can_continue

	def main(self, args):
		success = True
		app = args.app
		if not self._check_app(app, args):
			return
		status = 200
		try:
			if not self._show_license(app, args):
				raise KeyboardInterrupt()
			self._show_readme_install(app, args)
			self._install_app_deb(app, args)
			self._show_readme_postinstall(app, args)
		except KeyboardInterrupt:
			status = 401
			self.fatal('Chose to not install %s. Aborting...' % app.id)
		except Exception as e:
			status = 500
			self.log_exception(e)
		finally:
			success = success and status in [200, 401]
		return success

