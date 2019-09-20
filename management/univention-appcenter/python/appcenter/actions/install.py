#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for installing an app
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

from univention.admindiary.client import write_event
from univention.admindiary.events import APP_INSTALL_START, APP_INSTALL_SUCCESS, APP_INSTALL_FAILURE

from univention.appcenter.app_cache import Apps
from univention.appcenter.actions import get_action
from univention.appcenter.exceptions import Abort, InstallMasterPackagesPasswordError, InstallMasterPackagesNoninteractiveError, InstallFailed, InstallNonDockerVersionError, InstallWithoutPermissionError
from univention.appcenter.actions.install_base import InstallRemoveUpgrade
from univention.appcenter.ucr import ucr_get, ucr_save
from univention.appcenter.utils import find_hosts_for_master_packages
from univention.appcenter.packages import update_packages, install_packages_dry_run, install_packages, dist_upgrade_dry_run


class ControlScriptException(Exception):
	pass


class Install(InstallRemoveUpgrade):

	'''Installs an application from the Univention App Center.'''
	help = 'Install an app'

	prescript_ext = 'preinst'
	pre_readme = 'readme_install'
	post_readme = 'readme_post_install'

	def setup_parser(self, parser):
		super(Install, self).setup_parser(parser)
		parser.add_argument('--do-not-revert', action='store_false', dest='revert', help='Do not revert the installation when it fails. May leave the system in an undesired state')
		parser.add_argument('--only-master-packages', action='store_true', help='Install only master packages')
		parser.add_argument('--do-not-install-master-packages-remotely', action='store_false', dest='install_master_packages_remotely', help='Do not install master packages on DC master and DC backup systems')

	def main(self, args):
		app = args.app
		apps = Apps().get_all_apps_with_id(app.id)
		if app._docker_prudence_is_true():
			apps = [_app for _app in apps if not _app.docker]
			if apps:
				app = sorted(apps)[-1]
				self.warn('Using %s instead of %s because docker is to be ignored' % (app, args.app))
			else:
				raise InstallNonDockerVersionError(args.app)
		if not app.install_permissions_exist():
			apps = [_app for _app in apps if not _app.install_permissions]
			if apps:
				app = sorted(apps)[-1]
				self.warn('Using %s instead of %s because of lacking install permissions' % (app, args.app))
			else:
				raise InstallWithoutPermissionError()
		args.app = app
		return self.do_it(args)

	def _write_start_event(self, app, args):
		return write_event(APP_INSTALL_START, {'name': app.name, 'version': app.version}, username=self._get_username(args))

	def _write_success_event(self, app, context_id, args):
		return write_event(APP_INSTALL_SUCCESS, {'name': app.name, 'version': app.version}, username=self._get_username(args), context_id=context_id)

	def _write_fail_event(self, app, context_id, status, args):
		return write_event(APP_INSTALL_FAILURE, {'name': app.name, 'version': app.version, 'error_code': str(status)}, username=self._get_username(args), context_id=context_id)

	def _install_only_master_packages(self, args):
		return args.only_master_packages

	def _do_it(self, app, args):
		if self._install_only_master_packages(args):
			self._install_master_packages(app, unregister_if_uninstalled=True)
		else:
			self._register_files(app)
			self.percentage = 5
			self._register_app(app, args)
			self.percentage = 10
			self._register_database(app)
			self.percentage = 15
			if not hasattr(args, 'register_attributes') or args.register_attributes:
				self._register_attributes(app, args)
			self.percentage = 25
			if self._install_app(app, args):
				self._configure(app, args)
				self._update_certificates(app, args)
				self.percentage = 80
				self._call_join_script(app, args)
				self._register_listener(app)
				ucr_save({'appcenter/prudence/docker/%s' % app.id: 'yes'})
			else:
				raise InstallFailed()

	def _install_packages(self, packages):
		return install_packages(packages)

	def _install_master_packages(self, app, unregister_if_uninstalled=False):
		old_app = Apps().find(app.id)
		was_installed = old_app.is_installed()
		if self._register_component(app):
			update_packages()
		ret = self._install_packages(app.default_packages_master)
		if was_installed:
			if old_app != app:
				self.log('Re-registering component for %s' % old_app)
				if self._register_component(old_app):
					update_packages()
		elif unregister_if_uninstalled:
			self.log('Unregistering component for %s' % app)
			if self._unregister_component(app):
				update_packages()
		return ret

	def _install_only_master_packages_remotely(self, app, host, is_master, args):
		if args.install_master_packages_remotely:
			self.log('Installing some packages of %s on %s' % (app.id, host))
		else:
			self.warn('Not installing packages on %s. Please make sure that these packages are installed by calling "univention-app install "%s=%s" --only-master-packages" on the host' % (host, app.id, app.version))
			return
		username = 'root@%s' % host
		try:
			if args.noninteractive:
				raise InstallMasterPackagesNoninteractiveError()
			password = self._get_password_for(username)
			with self._get_password_file(password=password) as password_file:
				if not password_file:
					raise InstallMasterPackagesPasswordError()
				# TODO: fallback if univention-app is not installed
				process = self._subprocess(['/usr/sbin/univention-ssh', password_file, username, 'univention-app', 'install', '%s=%s' % (app.id, app.version), '--only-master-packages', '--noninteractive', '--do-not-send-info'])
				if process.returncode != 0:
					self.warn('Installing master packages for %s on %s failed!' % (app.id, host))
		except Abort:
			if is_master:
				self.fatal('This is the DC master. Cannot continue!')
				raise
			else:
				self.warn('This is a DC backup. Continuing anyway, please rerun univention-app install %s --only-master-packages there later!' % (app.id))

	def _install_app(self, app, args):
		if self._register_component(app):
			update_packages()
		if app.default_packages_master:
			if ucr_get('server/role') == 'domaincontroller_master':
				self._install_master_packages(app)
				self.percentage = 30
			for host, is_master in find_hosts_for_master_packages():
				self._install_only_master_packages_remotely(app, host, is_master, args)
			if ucr_get('server/role') == 'domaincontroller_backup':
				self._install_master_packages(app)
				self.percentage = 30
		ret = self._install_packages(app.get_packages())
		self.percentage = 80
		return ret

	def _revert(self, app, args):
		if not args.revert:
			return
		try:
			password = self._get_password(args, ask=False)
			remove = get_action('remove')
			remove.call(app=app, noninteractive=args.noninteractive, username=args.username, password=password, send_info=False, skip_checks=[], backup=False)
		except Exception:
			pass

	def _dry_run(self, app, args):
		return self._install_packages_dry_run(app, args, with_dist_upgrade=False)

	def _install_packages_dry_run(self, app, args, with_dist_upgrade):
		original_app = Apps().find(app.id)
		if original_app.is_installed():
			was_installed = True
		else:
			was_installed = False
		self.log('Dry run for %s' % app)
		if self._register_component(app):
			self.debug('Updating packages')
			update_packages()
		self.debug('Component %s registered' % app.component_id)
		pkgs = self._get_packages_for_dry_run(app, args)
		self.debug('Dry running with %r' % pkgs)
		ret = install_packages_dry_run(pkgs)
		if with_dist_upgrade:
			upgrade_ret = dist_upgrade_dry_run()
			ret['install'] = sorted(set(ret['install']).union(set(upgrade_ret['install'])))
			ret['remove'] = sorted(set(ret['remove']).union(set(upgrade_ret['remove'])))
			ret['broken'] = sorted(set(ret['broken']).union(set(upgrade_ret['broken'])))
		if args.install_master_packages_remotely:
			# TODO: should test remotely
			self.log('Not testing package changes of remote packages!')
			pass
		if args.dry_run or ret['broken']:
			if was_installed:
				if self._register_component(original_app):
					self.debug('Updating packages')
					update_packages()
				self.debug('Component %s reregistered' % original_app.component_id)
			else:
				if self._unregister_component(app):
					self.debug('Updating packages')
					update_packages()
				self.debug('Component %s unregistered' % app.component_id)
		return ret

	def _get_packages_for_dry_run(self, app, args):
		if args.only_master_packages:
			return app.default_packages_master
		else:
			return app.get_packages(additional=True)
