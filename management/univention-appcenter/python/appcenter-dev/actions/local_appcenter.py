#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for setting up one's own app center
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

import os
from ConfigParser import ConfigParser, NoOptionError
import subprocess
import urllib2
import shutil
from glob import glob
from json import dumps
from datetime import date
import gzip
import tarfile
from tempfile import mkdtemp
from distutils.version import LooseVersion


from univention.appcenter.app import App, AppManager, AppAttribute, _get_from_parser, _read_ini_file
from univention.appcenter.actions import UniventionAppAction, get_action, Abort
from univention.appcenter.utils import get_sha256_from_file, get_md5_from_file, mkdir, urlopen
from univention.appcenter.ucr import ucr_save, ucr_get


# re-include Screenshot for ini files targetting UCS < 4.1
_screenshot_attribute = AppAttribute(localisable=True)
_screenshot_attribute.set_name('screenshot')
App._attrs.append(_screenshot_attribute)


class LocalAppcenterAction(UniventionAppAction):
	def setup_parser(self, parser):
		parser.add_argument('--path', default='/var/www/', help='Path where the root of the App Center lives / shall live. Default: %(default)s')
		parser.add_argument('--ucs-version', default=ucr_get('version/version'), help='App Center is used for UCS_VERSION. Default: %(default)s')

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
		self.sha256 = get_sha256_from_file(filename)
		self.archive_filename = '%s.%s' % (app.name, name)


class AppcenterApp(object):
	def __init__(self, name, id, ucs_version, meta_inf_dir, components_dir, server):
		self.name = name
		self.id = id
		self.ucs_version = ucs_version
		self.meta_inf_dir = meta_inf_dir
		self.app_dir = ''
		if os.path.exists(os.path.join(self.meta_inf_dir, self.id)):
			# since UCS 4.1, each app has a separate subdirectory
			self.app_dir = self.id
		self.components_dir = components_dir
		if server.endswith('/'):
			server = server[:-1]
		self.server = server
		self.config = ConfigParser()
		self.config.read([self.get_ini_file(), self.get_meta_file()])

	def get_metainf_url(self):
		url = '%s/meta-inf/%s/' % (self.server, self.ucs_version)
		return url

	def get_repository_url(self):
		return '%s/univention-repository/%s/maintained/component/%s/' % (self.server, self.ucs_version, self.name)

	def _meta_url(self, filename, with_app_dir=True):
		path = filename
		if with_app_dir:
			path = os.path.join(self.app_dir, filename)
		return urllib2.urlparse.urljoin(self.get_metainf_url(), path)

	def _repository_url(self, filename):
		return urllib2.urlparse.urljoin(self.get_repository_url(), filename)

	def _components_dir(self, filename):
		return os.path.join(self.components_dir, self.name, filename)

	def _meta_inf_dir(self, filename, with_app_dir=True):
		path = self.meta_inf_dir
		if with_app_dir:
			path = os.path.join(path, self.app_dir)
		return os.path.join(path, filename)

	def get_meta_file(self):
		return self._meta_inf_dir('%s.meta' % self.id)

	def get_meta_url(self):
		return self._meta_url('%s.meta' % self.id)

	def get_ini_file(self):
		return self._meta_inf_dir('%s.ini' % self.name)

	def get_ini_url(self):
		return self._meta_url('%s.ini' % self.name)

	def get_png_file(self):
		# since UCS 4.1 deprecated
		return self._meta_inf_dir('%s.png' % self.name)

	def get_png_url(self):
		# since UCS 4.1 deprecated
		return self._meta_url('%s.png' % self.name)

	def file_info(self, name, url, filename):
		return FileInfo(self, name, url, filename)

	def important_files(self):
		# Adding "special ini and png file
		for special_file in ['ini', 'png', 'meta']:
			get_file_method = getattr(self, 'get_%s_file' % special_file.lower())
			get_url_method = getattr(self, 'get_%s_url' % special_file.lower())
			filename = get_file_method()
			url = get_url_method()
			if os.path.exists(filename):
				yield self.file_info(special_file, url, filename)

		# Adding logo files
		for ikey in ('Logo', 'LogoDetailPage'):
			if self.config.has_option('Application', ikey):
				basename = self.config.get('Application', ikey)
				filename = self._meta_inf_dir(basename)
				url = self._meta_url(basename)
				if os.path.isfile(filename):
					yield self.file_info(ikey.lower(), url, filename)

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
		for ext in ['univention-config-registry-variables', 'schema', 'preinst', 'inst', 'init', 'prerm', 'uinst', 'setup', 'store_data', 'restore_data_before_setup', 'restore_data_after_setup', 'update_available', 'update_packages', 'update_release', 'update_app_version', 'env']:
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
			index[file_info.name] = {'url': file_info.url, 'md5': file_info.md5, 'sha256': file_info.sha256}
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
		parser.add_argument('--appcenter-host', default=ucr_get('repository/app_center/server'), help='The hostname of the new App Center. Default: %(default)s')

	def main(self, args):
		meta_inf_dir = os.path.join(args.path, 'meta-inf', args.ucs_version)
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component')
		with tarfile.open(os.path.join(meta_inf_dir, 'all.tar.gz'), 'w:gz') as archive:
			with gzip.open(os.path.join(meta_inf_dir, 'index.json.gz'), 'wb') as index_json:
				apps = {}
				for root, dirs, files in os.walk(meta_inf_dir):
					for filename in files:
						path = os.path.join(root, filename)
						appname = check_ini_file(filename)
						if not appname:
							continue
						parser = _read_ini_file(path)
						appid = _get_from_parser(parser, 'Application', 'ID')
						if not appid:
							continue
						app = AppcenterApp(appname, appid, args.ucs_version, meta_inf_dir, repo_dir, args.appcenter_host)
						apps[app.name] = app.to_index()
						for filename_in_directory, filename_in_archive in app.tar_files():
							archive.add(filename_in_directory, filename_in_archive)
				index_json.write(dumps(apps, sort_keys=True, indent=4))
		if args.ucs_version == ucr_get('version/version'):
			update = get_action('update')
			update.call()


class DevPopulateAppcenter(LocalAppcenterAction):
	'''Add/update an app in the (local) App Center'''
	help = 'To be called after dev-setup-local-appcenter! Puts meta data (like ini file) and packages in the correct directories. Generates other meta files for the App Center to work'

	def setup_parser(self, parser):
		super(DevPopulateAppcenter, self).setup_parser(parser)
		version = ucr_get('version/version')
		arch = subprocess.check_output(['uname', '-m']).strip()
		parser.add_argument('--new', action='store_true', help='Add a completely new (or a new version of an existing) app in the local App Center')
		parser.add_argument('-c', '--component-id', help='The internal component ID for this version of the App')
		parser.add_argument('-i', '--ini', help='Path to the ini file of the App')
		parser.add_argument('-l', '--logo', help='Path to the logo file of the App (UCS 4.1: square SVG; UCS <= 4.0: 50x50 transparent PNG)')
		parser.add_argument('--logo-detail', dest='logo_detail_page', help='Path to the detail logo file of the App (4.1 only, elongated SVG)')
		parser.add_argument('-s', '--screenshot', nargs='+', help='Path to a screenshot (UCS < 4.1 only). Needs to be mentioned in INI as Screenshot=.... If the screenshot is localised (Screenshot= in [de]), two screenshots should be given. Superseded by THUMBNAILS in UCS 4.1')
		parser.add_argument('-t', '--thumbnails', nargs='+', help='Path to Thumbnails (UCS 4.1 only). Need to be mentioned in INI as Thumbnails=.... If the thumbnails are localised (Thumbnails= in [de]), first all [en], then all [de] Thumbnails should be given')
		parser.add_argument('--ucr', help='Path to a file describing Univention Config Registry variables')
		parser.add_argument('--schema', help='Path to an LDAP schema extension file')
		parser.add_argument('--preinst', help='Path to a preinst script that will be called by the App Center before installation')
		parser.add_argument('--join', help='Path to a join script that will be called by the App Center after installation')
		parser.add_argument('--prerm', help='Path to a prerm script that will be called by the App Center before uninstallation')
		parser.add_argument('--unjoin', help='Path to an unjoin script that will be called by the App Center after uninstallation')
		parser.add_argument('--init', help='Path to the init script that will be the entrypoint for a docker image (docker only)')
		parser.add_argument('--setup', help='Path to a script that sets up the app after the container has been initialized (docker only)')
		parser.add_argument('--store-data', help='Path to a script that stores data before the docker container is changed (docker only)')
		parser.add_argument('--restore-data-before-setup', help='Path to a script that restores data after the docker container is changed and before setup is run (docker only)')
		parser.add_argument('--restore-data-after-setup', help='Path to a script that restores data after the docker container is changed and after setup is run (docker only)')
		parser.add_argument('--update-available', help='Path to a script that finds out whether an update for the operating system in the container is available (docker only)')
		parser.add_argument('--update-packages', help='Path to a script that updates packages in the container (docker only)')
		parser.add_argument('--update-release', help='Path to a script that upgrades the operating system in the container (docker only)')
		parser.add_argument('--update-app-version', help='Path to a script that updates the app within the container (docker only)')
		parser.add_argument('--env', help='Path to a file containing (a part of) the docker environment (docker only)')
		parser.add_argument('-r', '--readme', nargs='+', help='Path to (multiple) README files like README_DE, README_POST_INSTALL')
		parser.add_argument('--license', nargs='+', help='Path to (multiple) LICENSE_AGREEMENT files like LICENSE_AGREEMENT, LICENSE_AGREEMENT_DE')
		parser.add_argument('-p', '--packages', nargs='+', help='Path to debian packages files for the app', metavar='PACKAGE')
		parser.add_argument('-u', '--unmaintained', nargs='+', help='Package names that exist in the unmaintained repository for UCS. ATTENTION: Only works for --ucs-version=%s; takes some time, but it is only needed once, so for further package updates of this very app version this is not need to be done again. ATTENTION: Only works for architecture %s.' % (version, arch), metavar='PACKAGE')
		parser.add_argument('-d', '--do-not-delete-duplicates', action='store_true', help=' If any PACKAGE already exist in the repository (e.g. another version), they are removed. Unless this option is set.')
		parser.add_argument('--appcenter-host', default=ucr_get('repository/app_center/server'), help='The hostname of the new App Center. Default: %(default)s')

	def main(self, args):
		component_id = args.component_id
		app_id = None
		if args.new:
			component_id, app_id = self._create_new_repo(args)
		meta_inf_dir = os.path.join(args.path, 'meta-inf', args.ucs_version)
		if LooseVersion(args.ucs_version) >= '4.1':
			if app_id is None:
				if args.ini:
					ini_file = args.ini
				else:
					for root, dirnames, filenames in os.walk(meta_inf_dir):
						for filename in filenames:
							if filename == '%s.ini' % component_id:
								ini_file = os.path.join(root, filename)
								break
						else:
							continue
						break
					else:
						raise Abort('Could not determine app id. Specify an --ini file!')
				app = App.from_ini(ini_file)
				app_id = app.id
			meta_inf_dir = os.path.join(meta_inf_dir, app_id)
		mkdir(meta_inf_dir)
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component', component_id)
		mkdir(repo_dir)
		if args.unmaintained:
			version = ucr_get('version/version')
			if args.ucs_version != version:
				self.fatal('Cannot easily set up unmaintained packages for %s (need %s). You need to download them into the repository manually. Sorry!' % (args.ucs_version, version))
			else:
				self._copy_unmaintained_packages(repo_dir, args)
		self._copy_meta_files(component_id, meta_inf_dir, repo_dir, args)
		if args.packages:
			app = App.from_ini(os.path.join(meta_inf_dir, '%s.ini' % component_id))
			self._handle_packages(app, repo_dir, args)
			self._generate_repo_index_files(repo_dir)
		self._generate_meta_index_files(args)
		self.log('Component is: %s' % component_id)

	def _create_new_repo(self, args):
		if not args.ini or not os.path.exists(args.ini):
			raise Abort('An ini file is needed for new apps')
		app = App.from_ini(args.ini)
		if not app:
			raise Abort('Cannot continue with flawed ini file')
		if args.component_id:
			component_id = args.component_id
		else:
			component_id = '%s_%s' % (app.id, date.today().strftime('%Y%m%d'))
		repo_dir = os.path.join(args.path, 'univention-repository', args.ucs_version, 'maintained', 'component', component_id)
		if not app.without_repository:
			mkdir(os.path.join(repo_dir, 'all'))
			mkdir(os.path.join(repo_dir, 'i386'))
			mkdir(os.path.join(repo_dir, 'amd64'))
		return component_id, app.id

	def _copy_unmaintained_packages(self, repo_dir, args):
		unmaintained_ucr_var = 'repository/online/unmaintained'
		old_unmaintained = ucr_get(unmaintained_ucr_var)
		ucr_save({unmaintained_ucr_var: 'yes'})
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
			ucr_save({unmaintained_ucr_var: old_unmaintained})

	def _copy_meta_files(self, component_id, meta_inf_dir, repo_dir, args):
		if args.ini:
			self.copy_file(args.ini, os.path.join(meta_inf_dir, '%s.ini' % component_id))
		ini_file = os.path.join(meta_inf_dir, '%s.ini' % component_id)
		app_en = App.from_ini(ini_file, 'en')
		app_de = App.from_ini(ini_file, 'de')
		if not app_en or not app_de:
			raise Abort('Cannot continue with flawed ini file')
		if args.logo:
			if LooseVersion(args.ucs_version) >= '4.1':
				parser = ConfigParser()
				parser.read(ini_file)
				try:
					logo_fname = parser.get('Application', 'Logo')
				except NoOptionError:
					self.fatal('No Logo specified in ini file!')
				else:
					self.copy_file(args.logo, os.path.join(meta_inf_dir, logo_fname))
			else:
				self.copy_file(args.logo, os.path.join(meta_inf_dir, '%s.png' % component_id))
		if args.logo_detail_page:
			parser = ConfigParser()
			parser.read(ini_file)
			try:
				logo_detail_fname = parser.get('Application', 'LogoDetailPage')
			except NoOptionError:
				self.fatal('No Logo specified in ini file!')
			self.copy_file(args.logo_detail_page, os.path.join(meta_inf_dir, logo_detail_fname))
		if args.screenshot:
			self.copy_file(args.screenshot[0], os.path.join(meta_inf_dir, app_en.screenshot))
			if len(args.screenshot) > 1:
				self.copy_file(args.screenshot[1], os.path.join(meta_inf_dir, app_de.screenshot))
		if args.thumbnails:
			thumbnails = []
			for thumbnail in app_en.thumbnails + app_de.thumbnails:
				if thumbnail in thumbnails:
					continue
				if thumbnail.startswith('http'):
					continue
				thumbnails.append(thumbnail)
			for i, thumbnail in enumerate(args.thumbnails):
				try:
					self.copy_file(thumbnail, os.path.join(meta_inf_dir, thumbnails[i]))
				except IndexError:
					raise Abort('The ini file must state as much Thumbnails= as --thumbnails are given')
		if args.readme:
			for readme in args.readme:
				self.copy_file(readme, repo_dir)
		if args.license:
			for license in args.license:
				self.copy_file(license, repo_dir)
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
		if args.setup:
			self.copy_file(args.setup, os.path.join(repo_dir, 'setup'))
		if args.store_data:
			self.copy_file(args.store_data, os.path.join(repo_dir, 'store_data'))
		if args.restore_data_before_setup:
			self.copy_file(args.restore_data_before_setup, os.path.join(repo_dir, 'restore_data_before_setup'))
		if args.restore_data_after_setup:
			self.copy_file(args.restore_data_after_setup, os.path.join(repo_dir, 'restore_data_after_setup'))
		if args.update_available:
			self.copy_file(args.update_available, os.path.join(repo_dir, 'update_available'))
		if args.update_packages:
			self.copy_file(args.update_packages, os.path.join(repo_dir, 'update_packages'))
		if args.update_release:
			self.copy_file(args.update_release, os.path.join(repo_dir, 'update_release'))
		if args.update_app_version:
			self.copy_file(args.update_app_version, os.path.join(repo_dir, 'update_app_version'))
		if args.env:
			self.copy_file(args.env, os.path.join(repo_dir, 'env'))

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
						path = line[len(os.path.dirname(repo_dir)) + 11:]  # -"Filename: /var/www/.../maintained/component/"
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
		parser.add_argument('--appcenter-host', default=ucr_get('interfaces/eth0/address'), help='The hostname of the new App Center. Default: %(default)s')
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
			ucr_save({'repository/app_center/server': 'appcenter.software-univention.de', 'update/secure_apt': 'yes', 'appcenter/index/verify': 'yes'})
			update = get_action('update')
			update.call()
		else:
			mkdir(meta_inf_dir)
			mkdir(os.path.join(repo_dir, 'maintained', 'component'))
			with open(os.path.join(meta_inf_dir, '..', 'categories.ini'), 'wb') as f:
				categories = urlopen('%s/meta-inf/categories.ini' % AppManager.get_server()).read()
				f.write(categories)
			with open(os.path.join(meta_inf_dir, '..', 'rating.ini'), 'wb') as f:
				rating = urlopen('%s/meta-inf/rating.ini' % AppManager.get_server()).read()
				f.write(rating)
			server = 'http://%s' % args.appcenter_host
			ucr_save({'repository/app_center/server': server, 'update/secure_apt': 'no', 'appcenter/index/verify': 'no'})
			DevRegenerateMetaInf.call(ucs_version=args.ucs_version, path=args.path, appcenter_host=server)
			self.log('Local App Center server is set up at %s.' % server)
			self.log('If this server should serve as an App Center server for other computers in the UCS domain, the following command has to be executed on each computer:')
			self.log('  ucr set repository/app_center/server="%s"' % server)
