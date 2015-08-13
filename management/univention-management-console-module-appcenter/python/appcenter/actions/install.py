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

from tempfile import NamedTemporaryFile

from univention.config_registry import ConfigRegistry

from univention.appcenter.actions import Abort
from univention.appcenter.actions.install_base import InstallRemoveUpgrade
from univention.appcenter.actions.remove import Remove
from univention.appcenter.udm import search_objects

class ControlScriptException(Exception):
	pass

class Install(InstallRemoveUpgrade):
	'''Installs an application from the Univention App Center.'''
	help='Install an app'

	pre_readme = 'readme_install'
	post_readme = 'readme_post_install'

	def setup_parser(self, parser):
		super(Install, self).setup_parser(parser)
		parser.add_argument('--only-master-packages', action='store_true', help='Install only master packages')
		parser.add_argument('--do-not-install-master-packages-remotely', action='store_false', dest='install_master_packages_remotely', help='Do not install master packages on DC master and DC backup systems')

	def main(self, args):
		self.do_it(args)

	def _install_only_master_packages(self, args):
		return args.only_master_packages

	def _do_it(self, app, args):
		if self._install_only_master_packages(args):
			self._install_master_packages(app)
		else:
			self._register_files(app)
			self.percentage = 5
			self._register_app(app, args)
			self.percentage = 10
			self._install_app(app, args)
			self.percentage = 80
			self._call_join_script(app, args)

	def _install_master_packages(self, app, percentage_end=100):
		self._register_component(app)
		self._apt_get('install', app.default_packages_master, percentage_end)
		self._register_component(app, force=False)

	def _install_only_master_packages_remotely(self, app, host, is_master, args):
		if args.install_master_packages_remotely:
			self.log('Installing some packages of %s on %s' % (app.id, host))
		else:
			self.warn('Not installing packages on %s. Please make sure that these packages are installed by calling "univention-app install "%s=%s" --only-master-packages" on the host' % (host, app.id, app.version))
			return
		username = 'root@%s' % host
		try:
			if args.noninteractive:
				raise Abort()
			password = self._get_password_for(username)
			with self._get_password_file(password=password) as password_file:
				if not password_file:
					raise Abort()
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

	def _find_hosts_for_master_packages(self, args):
		lo, pos = self._get_ldap_connection(args, allow_machine_connection=True)
		ucr = ConfigRegistry()
		ucr.load()
		hosts = []
		for host in search_objects('computers/domaincontroller_master', lo, pos):
			hosts.append((host.info.get('fqdn'), True))
		for host in search_objects('computers/domaincontroller_backup', lo, pos):
			hosts.append((host.info.get('fqdn'), False))
		try:
			local_fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
			local_is_master = ucr.get('server/role') == 'domaincontroller_master'
			hosts.remove((local_fqdn, local_is_master))
		except ValueError:
			# not in list
			pass
		return hosts

	def _install_app(self, app, args):
		ucr = ConfigRegistry()
		ucr.load()
		self._register_component(app)
		install_master = False
		if app.default_packages_master:
			if ucr.get('server/role') == 'domaincontroller_master':
				self._install_master_packages(app, 30)
				install_master = True
			for host, is_master in self._find_hosts_for_master_packages(args):
				self._install_only_master_packages_remotely(app, host, is_master, args)
			if ucr.get('server/role') == 'domaincontroller_backup':
				self._install_master_packages(app, 30)
				install_master = True
		self._apt_get('install', app.default_packages, 80, update=not install_master)

	def _revert(self, app, args):
		try:
			Remove.call(app=app, noninteractive=args.noninteractive, username=args.username, pwdfile=args.pwdfile, send_info=False, skip_checks=[])
		except Exception:
			pass

	def _call_prescript(self, app, **kwargs):
		ext = 'preinst'
		with NamedTemporaryFile('r+b') as error_file:
			kwargs['version'] = app.version
			kwargs['error_file'] = error_file.name
			success = self._call_cache_script(app, ext, **kwargs)
			if success is None:
				# no preinst
				success = True
			if not success:
				for line in error_file:
					self.warn(line)
			return success

