#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for setting up one's own app center
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

import os
import ConfigParser
import subprocess
import urllib2
import shutil
from glob import glob
from json import dumps
from datetime import date
import gzip
import tarfile
from tempfile import mkdtemp

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update

ucr = ConfigRegistry()
ucr.load()

from univention.appcenter.app import App
from univention.appcenter.actions import UniventionAppAction
from univention.appcenter.utils import get_md5_from_file, mkdir
from univention.appcenter.actions.update import Update

class LocalAppcenterAction(UniventionAppAction):
	def setup_parser(self, parser):
		parser.add_argument('--path', default='/var/www/', help='Path where the root of the App Center lives / shall live. Default: %(default)s')
		parser.add_argument('--ucs-version', default=ucr.get('version/version'), help='App Center is used for UCS_VERSION. Default: %(default)s')

	def copy_file(self, src, dst):
		if src == dst:
			return True
		try:
			shutil.copy2(src, dst)
		except IOError as exc:
			self.warn(exc)
			return False
		else:
			return True

class FileInfo(object):
	def __init__(self, app, name, url, filename):
		self.name = name
		self.url = url
		self.filename = filename
		self.md5 = get_md5_from_file(filename)
		self.archive_filename = '%s.%s' % (app.name, name)

class AppcenterApp(object):
	def __init__(self, name, ucs_version, meta_inf_dir, components_dir, server):
		self.name = name
		self.ucs_version = ucs_version
		self.meta_inf_dir = meta_inf_dir
		self.components_dir = components_dir
		if server.endswith('/'):
			server = server[:-1]
		self.server = server

	def get_metainf_url(self):
		return '%s/meta-inf/%s/' % (self.server, self.ucs_version)

	def get_repository_url(self):
		return '%s/univention-repository/%s/maintained/component/%s/' % (self.server, self.ucs_version, self.name)

	def _meta_url(self, filename):
		return urllib2.urlparse.urljoin(self.get_metainf_url(), filename)

	def _repository_url(self, filename):
		return urllib2.urlparse.urljoin(self.get_repository_url(), filename)

	def _components_dir(self, filename):
		return os.path.join(self.components_dir, self.name, filename)

	def _meta_inf_dir(self, filename):
		return os.path.join(self.meta_inf_dir, filename)

	def get_ini_file(self):
		return self._meta_inf_dir('%s.ini' % self.name)

	def get_ini_url(self):
		return self._meta_url('%s.ini' % self.name)

	def get_png_file(self):
		return self._meta_inf_dir('%s.png' % self.name)

	def get_png_url(self):
		return self._meta_url('%s.png' % self.name)

	def file_info(self, name, url, filename):
		return FileInfo(self, name, url, filename)

	def important_files(self):
		# Adding "special ini and png file
		for special_file in ['ini', 'png']:
			get_file_method = getattr(self, 'get_%s_file' % special_file.lower())
			get_url_method = getattr(self, 'get_%s_url' % special_file.lower())
			filename = get_file_method()
			url = get_url_method()
			if os.path.exists(filename):
				yield self.file_info(special_file, url, filename)

		# Adding LICENSE_AGREEMENT and localised versions like LICENSE_AGREEMENT_DE
		for readme_filename in glob(self._components_dir('LICENSE_AGREEMENT*')):
			basename = os.path.basename(readme_filename)
			url = self._repository_url(basename)
			yield self.file_info(basename, url, readme_filename)

		# Adding README, README_UPDATE, README_INSTALL, REAME_POST_UPDATE, README_POST_INSTALL
		#   and all the localised versions like README_DE and README_POST_INSTALL_EN (and even *_FR)
		for readme_filename in glob(self._components_dir('README*')):
			basename = os.path.basename(readme_filename)
			url = self._repository_url(basename)
			yield self.file_info(basename, url, readme_filename)

		# Adding ucr, schema, (un)joinscript, etc
		for ext in ['univention-config-registry-variables', 'schema', 'preinst', 'inst', 'init', 'prerm', 'uinst']:
			control_filename = self._components_dir(ext)
			if os.path.exists(control_filename):
				basename = os.path.basename(control_filename)
				url = self._repository_url(basename)
				yield self.file_info(ext, url, control_filename)

	def tar_files(self):
		for file_info in self.important_files():
			yield file_info.filename, file_info.archive_filename

	def to_index(self):
		index = {}
		for file_info in self.important_files():
			index[file_info.name] = {'url' : file_info.url, 'md5' : file_info.md5}
		return index

def check_ini_file(filename):
	name, ext = os.path.splitext(os.path.basename(filename))
	if ext == '.ini':
		return name

class DevRegenerateMetaInf(LocalAppcenterAction):
	'''Generate necessary cache files for the App Center server'''
	help = 'In order to work correctly as an App Center server, certain cache files need to be present for clients to download. These are (re)generated automatically by this function'

	def setup_parser(self, parser):
		super(DevRegenerateMetaInf, self).setup_parser(parser)
		parser.add_argument('--appcenter-host', default=ucr.get('repository/app_center/server'), help='The hostname of the new App Center. Default: %(default)s')

	def main(self, args):
		meta_inf_dir = os.path.join(args.path, 'meta-inf', args.ucs_version)
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component')
		with tarfile.open(os.path.join(meta_inf_dir, 'all.tar.gz'), 'w:gz') as archive:
			with gzip.open(os.path.join(meta_inf_dir, 'index.json.gz'), 'wb') as index_json:
				apps = {}
				for root, dirs, files in os.walk(meta_inf_dir):
					for filename in files:
						appname = check_ini_file(filename)
						if not appname:
							continue
						app = AppcenterApp(appname, args.ucs_version, meta_inf_dir, repo_dir, args.appcenter_host)
						apps[app.name] = app.to_index()
						for filename_in_directory, filename_in_archive in app.tar_files():
							archive.add(filename_in_directory, filename_in_archive)
				index_json.write(dumps(apps, sort_keys=True, indent=4))
		Update.call()

class DevPopulateAppcenter(LocalAppcenterAction):
	'''Add/update an app in the (local) App Center'''
	help = 'To be called after dev-setup-local-appcenter! Puts meta data (like ini file) and packages in the correct directories. Generates other meta files for the App Center to work'

	def setup_parser(self, parser):
		super(DevPopulateAppcenter, self).setup_parser(parser)
		version = ucr.get('version/version')
		arch = subprocess.check_output(['uname', '-m']).strip()
		group = parser.add_mutually_exclusive_group(required=True)
		group.add_argument('--new', action='store_true', help='Add a completely new (or a new version of an existing) app in the local App Center')
		group.add_argument('-c', '--component-id', help='The internal component ID for this (already existing) version of the App')
		parser.add_argument('-i', '--ini', help='Path to the ini file of the App')
		parser.add_argument('-l', '--logo', help='Path to the logo file of the App (50x50 transparent PNG)')
		parser.add_argument('-s', '--screenshot', help='Path to a screenshot. Needs to be mentioned in INI as Screenshot=...')
		parser.add_argument('--ucr', help='Path to a file describing Univention Config Registry variables')
		parser.add_argument('--schema', help='Path to an LDAP schema extension file')
		parser.add_argument('--preinst', help='Path to a preinst script that will be called by the App Center before installation')
		parser.add_argument('--join', help='Path to a join script that will be called by the App Center after installation')
		parser.add_argument('--prerm', help='Path to a prerm script that will be called by the App Center before uninstallation')
		parser.add_argument('--unjoin', help='Path to an unjoin script that will be called by the App Center after uninstallation')
		parser.add_argument('--init', help='Path to the init script that will be the entrypoint for a docker image (docker only)')
		parser.add_argument('-r', '--readme', nargs='+', help='Path to (multiple) README files like README_DE, README_POST_INSTALL, but also LICENSE_AGREEMENT, LICENSE_AGREEMENT_DE')
		parser.add_argument('-p', '--packages', nargs='+', help='Path to debian packages files for the app', metavar='PACKAGE')
		parser.add_argument('-u', '--unmaintained', nargs='+', help='Package names that exist in the unmaintained repository for UCS. ATTENTION: Only works for --ucs-version=%s; takes some time, but it is only needed once, so for further package updates of this very app version this is not need to be done again. ATTENTION: Only works for architecture %s.' % (version, arch), metavar='PACKAGE')
		parser.add_argument('-d', '--do-not-delete-duplicates', action='store_true', help=' If any PACKAGE already exist in the repository (e.g. another version), they are removed. Unless this option is set.')
		parser.add_argument('--appcenter-host', default=ucr.get('repository/app_center/server'), help='The hostname of the new App Center. Default: %(default)s')

	def main(self, args):
		component_id = args.component_id
		if args.new:
			component_id = self._create_new_repo(args)
		meta_inf_dir = os.path.join(args.path, 'meta-inf', args.ucs_version)
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component', component_id)
		if not os.path.exists(repo_dir):
			self.fatal('%s does not exist! --new must be called successfully' % repo_dir)
		if args.unmaintained:
			version = ucr.get('version/version')
			if args.ucs_version != version:
				self.fatal('Cannot easily set up unmaintained packages for %s (need %s). You need to download them into the repository manually. Sorry!' % (args.ucs_version, version))
			self._copy_unmaintained_packages(repo_dir, args)
		self._copy_meta_files(component_id, meta_inf_dir, repo_dir, args)
		if args.packages:
			app = App.from_ini(os.path.join(meta_inf_dir, '%s.ini' % component_id))
			self._handle_packages(app, repo_dir, args)
			self._generate_repo_index_files(repo_dir)
		self._generate_meta_index_files(args)
		self.log('Component is: %s' % component_id)

	def _create_new_repo(self, args):
		config = ConfigParser.ConfigParser()
		if not args.ini or not os.path.exists(args.ini):
			self.fatal('An ini file is needed for new apps')
		with open(args.ini, 'rb') as ini:
			config.readfp(ini)
		app_id = config.get('Application', 'ID')
		component_id = '%s_%s' % (app_id, date.today().strftime('%Y%m%d'))
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component', component_id)
		mkdir(os.path.join(repo_dir, 'all'))
		mkdir(os.path.join(repo_dir, 'i386'))
		mkdir(os.path.join(repo_dir, 'amd64'))
		return component_id

	def _copy_unmaintained_packages(self, repo_dir, args):
		unmaintained_ucr_var = 'repository/online/unmaintained'
		old_unmaintained = ucr.get(unmaintained_ucr_var)
		ucr_update(ucr, {unmaintained_ucr_var: 'yes'})
		try:
			old_debs = glob('*.deb')
			subprocess.call(['apt-get', 'update'])
			subprocess.call(['apt-get', 'download'] + args.unmaintained)
			new_debs = glob('*.deb')
			for deb in new_debs:
				if deb not in old_debs:
					args.packages = args.packages or []
					args.packages.append(deb)
		finally:
			ucr_update(ucr, {unmaintained_ucr_var: old_unmaintained})

	def _copy_meta_files(self, component_id, meta_inf_dir, repo_dir, args):
		if args.ini:
			self.copy_file(args.ini, os.path.join(meta_inf_dir, '%s.ini' % component_id))
		if args.logo:
			self.copy_file(args.logo, os.path.join(meta_inf_dir, '%s.png' % component_id))
		if args.screenshot:
			config = ConfigParser.ConfigParser()
			with open(os.path.join(meta_inf_dir, '%s.ini' % component_id), 'rb') as ini:
				config.readfp(ini)
			screenshot_filename = config.get('Application', 'Screenshot')
			self.copy_file(args.screenshot, os.path.join(meta_inf_dir, screenshot_filename))
		if args.readme:
			for readme in args.readme:
				self.copy_file(readme, repo_dir)
		if args.ucr:
			self.copy_file(args.ucr, os.path.join(repo_dir, 'univention-config-registry-variables'))
		if args.schema:
			self.copy_file(args.schema, os.path.join(repo_dir, 'schema'))
		if args.preinst:
			self.copy_file(args.preinst, os.path.join(repo_dir, 'preinst'))
		if args.join:
			self.copy_file(args.join, os.path.join(repo_dir, 'inst'))
		if args.prerm:
			self.copy_file(args.prerm, os.path.join(repo_dir, 'prerm'))
		if args.unjoin:
			self.copy_file(args.unjoin, os.path.join(repo_dir, 'uinst'))
		if args.init:
			self.copy_file(args.init, os.path.join(repo_dir, 'init'))

	def _handle_packages(self, app, repo_dir, args):
		dirname = mkdtemp()
		try:
			self._subprocess(['dpkg-name', '-k', '-s', dirname] + [os.path.abspath(pkg) for pkg in args.packages])
			args.packages = glob(os.path.join(dirname, '*.deb'))
			self._copy_packages(repo_dir, args)
		finally:
			shutil.rmtree(dirname)

	def _copy_packages(self, repo_dir, args):
		def _copy_package(pkg, arch, add_arch_ending=False):
			if not args.do_not_delete_duplicates:
				package_name, ext = os.path.splitext(os.path.basename(pkg))
				package_name = package_name.split('_', 2)[0]
				for existing_package in glob(os.path.join(repo_dir, arch, '%s_*' % package_name)):
					self.warn('Deleting already existing %s' % existing_package)
					os.unlink(existing_package)
			dst = os.path.join(repo_dir, arch)
			if add_arch_ending:
				package_name, _ = os.path.splitext(os.path.basename(pkg))
				dst = os.path.join(dst, '%s_%s.deb' % (package_name, arch))
			self.copy_file(pkg, dst)
		for package in args.packages:
			if not package.endswith('.deb'):
				self.warn('%s should end with .deb' % package)
				continue
			if package.endswith('_i386.deb'):
				_copy_package(package, 'i386')
			elif package.endswith('_amd64.deb'):
				_copy_package(package, 'amd64')
			elif package.endswith('_all.deb'):
				_copy_package(package, 'all')
			else:
				self.warn('Could not determine architecture from filename. Assuming _all.deb')
				_copy_package(package, 'all', add_arch_ending=True)

	def _generate_repo_index_files(self, repo_dir):
		mode = 'packages'
		for arch in ['i386', 'amd64', 'all']:
			filename = os.path.join(repo_dir, arch, 'Packages')
			for fname in glob('%s*' % filename):
				os.unlink(fname)
			with open(filename, 'wb') as packages:
				process = subprocess.Popen(['apt-ftparchive', mode, repo_dir], stdout=subprocess.PIPE)
				stdout, stderr = process.communicate()
				for line in stdout.splitlines():
					if line.startswith('Filename:'):
						path = line[len(os.path.dirname(repo_dir)) + 11:] # -"Filename: /var/www/.../maintained/component/"
						line = 'Filename: %s' % path
					packages.write('%s\n' % line)
			with open('%s.gz' % filename, 'wb') as gz:
				subprocess.Popen(['gzip', '--stdout', filename], stdout=gz)
			subprocess.call(['bzip2', '--keep', filename])

	def _generate_meta_index_files(self, args):
		DevRegenerateMetaInf.call(ucs_version=args.ucs_version, path=args.path, appcenter_host=args.appcenter_host)

class DevSetupLocalAppcenter(LocalAppcenterAction):
	'''Use this host as an App Center server'''
	help = 'Sets up this host as an App Center server and configures the App Center module to use it. WARNING: the actual app server is overwritten'

	def setup_parser(self, parser):
		super(DevSetupLocalAppcenter, self).setup_parser(parser)
		parser.add_argument('--appcenter-host', default=ucr.get('interfaces/eth0/address'), help='The hostname of the new App Center. Default: %(default)s')
		parser.add_argument('--revert', action='store_true', help='Reverts the changes of a previous dev-setup-local-appcenter')

	def main(self, args):
		meta_inf_dir = os.path.join(args.path, 'meta-inf', args.ucs_version)
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version)
		if args.revert:
			try:
				shutil.rmtree(meta_inf_dir)
			except OSError as exc:
				self.warn(exc)
			try:
				shutil.rmtree(repo_dir)
			except OSError as exc:
				self.warn(exc)
			ucr_update(ucr, {'repository/app_center/server': 'appcenter.software-univention.de', 'update/secure_apt': 'yes'})
			Update.call()
		else:
			mkdir(meta_inf_dir)
			mkdir(os.path.join(repo_dir, 'maintained', 'component'))
			server = 'http://%s' % args.appcenter_host
			ucr_update(ucr, {'repository/app_center/server': server, 'update/secure_apt': 'no'})
			DevRegenerateMetaInf.call(ucs_version=args.ucs_version, path=args.path, appcenter_host=server)
			self.log('Local App Center server is set up at %s.' % server)
			self.log('If this server should serve as an App Center server for other computers in the UCS domain, the following command has to be executed on each computer:')
			self.log('  ucr set repository/app_center/server="%s"' % server)

