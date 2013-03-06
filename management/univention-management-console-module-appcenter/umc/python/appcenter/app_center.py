#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management / app center
#
# Copyright 2012 Univention GmbH
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

# standard library
import shutil
import time
from distutils.version import LooseVersion
from gzip import GzipFile
from StringIO import StringIO
import ConfigParser
import copy
import locale
import os.path
import re
from threading import Thread
from hashlib import md5
import traceback
import urllib
import urllib2
from glob import glob
import cgi
from urlparse import urlsplit, urlunsplit, urljoin
from datetime import datetime
from PIL import Image
from httplib import HTTPException
from socket import error as SocketError

# related third party
import ldif
from simplejson import loads

# univention
from univention.management.console.log import MODULE
from univention.config_registry import ConfigRegistry, handler_commit
import univention.uldap as uldap
import univention.management.console as umc

# local application
from util import urlopen, get_current_ram_available, component_registered, UMCConnection, get_master, get_all_backups

LOGFILE = '/var/log/univention/appcenter.log' # UNUSED! see /var/log/univention/management-console-module-appcenter.log
CACHE_DIR = '/var/cache/univention-management-console/appcenter'
FRONTEND_ICONS_DIR = '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons'
ucr = ConfigRegistry()
ucr.load()

_ = umc.Translation('univention-management-console-module-appcenter').translate

class License(object):
	def __init__(self):
		self.uuid = None
		self.reload()

	def reload(self, force=False):
		if self.uuid is not None and not force:
			# license with uuid has already been found
			return
		self.uuid = None
		# last time we checked, no uuid was found
		# but maybe the user installed a new license?
		try:
			_lo = uldap.getMachineConnection(ldap_master=False)
			data = _lo.search('objectClass=univentionLicense')
			del _lo
			self.uuid = data[0][1]['univentionLicenseKeyID'][0]
		except Exception as e:
			# no licensing available
			MODULE.warn('Failed to load license information: %s' % e)

	def dump_data(self):
		# we could return infos we have in this object itself.
		# but dont be too clever here. just dump
		# everything we have in LDAP.
		try:
			_lo = uldap.getMachineConnection()
			data = _lo.search('objectClass=univentionLicense')
			del _lo
			# just one license (should be always the case)
			# return the dictionary without the dn
			data = ldif.CreateLDIF(data[0][0], data[0][1])
			return data
		except Exception as e:
			# no udm, no ldap, malformed return value, whatever
			MODULE.error('getting License from LDAP failed: %s' % e)
			return None

	def email_known(self):
		# at least somewhere at univention
		return self.uuid is not None

	def allows_using(self, email_required):
		return self.email_known() or not email_required

LICENSE = License()

class Application(object):
	_reg_comma = re.compile('\s*,\s*')
	_reg_component_id = re.compile(r'.*/(?P<id>[^/]+)\.ini')
	_all_applications = None
	_category_translations = None

	def __init__(self, ini_file, localize=True):
		# load config file
		self._options = {}
		config = ConfigParser.ConfigParser()
		with open(ini_file, 'rb') as fp:
			config.readfp(fp)
		self.raw_config = config
		url = urljoin('%s/' % self.get_metainf_url(), os.path.basename(ini_file))

		# copy values from config file
		for k, v in config.items('Application'):
			self._options[k] = cgi.escape(v)

		if localize:
			# overwrite english values with localized translations
			loc = locale.getlocale()[0]
			if isinstance(loc, basestring):
				if not config.has_section(loc):
					loc = loc.split('_')[0]
				if config.has_section(loc):
					for k, v in config.items(loc):
						self._options[k] = v

		# parse boolean values
		for ikey in ('notifyvendor', 'useractivationrequired'):
			if ikey in self._options:
				self._options[ikey] = config.getboolean('Application', ikey)
			else:
				self._options[ikey] = False

		# parse int values:
		for ikey in ('minphysicalram',):
			if ikey in self._options:
				self._options[ikey] = config.getint('Application', ikey)
			else:
				self._options[ikey] = 0

		# parse list values
		for ikey in ('categories', 'defaultpackages', 'conflictedsystempackages', 'defaultpackagesmaster', 'conflictedapps', 'serverrole'):
			ival = self.get(ikey)
			if ival:
				self._options[ikey] = self._reg_comma.split(ival)
			else:
				self._options[ikey] = []

		if localize:
			# localize the category names
			category_translations = self._get_category_translations()
			self._options['categories'] = [ category_translations.get(icat.lower()) or icat for icat in self.get('categories') ]

		# return a proper URL for local files
		for ikey in ('screenshot',):
			if self.get(ikey):
				self._options[ikey] = urljoin('%s/' % self.get_metainf_url(), self.get(ikey))

		# save important meta data
		self.id = self._options['id'] = self._options['id'].lower()
		self.name = self._options['name']
		self.version = self._options['version']

		# get the name of the component
		m = self._reg_component_id.match(url)
		self.component_id = 'unknown'
		if m:
			self.component_id = m.groupdict()['id']
		self.icon = self._options['icon'] = 'apps-%s' % self.component_id

		self._fetch_file('readme_en', 'README_EN')
		self._fetch_file('readme_de', 'README_DE')
		self._fetch_file('licenseagreement', 'LICENSE_AGREEMENT')
		self._fetch_file('readmeupdate', 'README_UPDATE')

		# candidate is for upgrading an already installed app
		# is set by all()
		self.candidate = None

	def get(self, key):
		'''Helper function to access configuration elements of the application's .ini
		file. If element is not given, returns (for string elements) an empty string.
		'''
		v = self._options.get(key.lower())
		if v is None:
			return ''
		return v

	def _fetch_file(self, key, file_ext):
		try:
			# open the license file
			filename = os.path.join(CACHE_DIR, '%s.%s' % (self.component_id, file_ext))
			with open(filename, 'rb') as fp:
				self._options[key] = ''.join(fp.readlines()).strip()
		except IOError:
			pass
			# MODULE.warn('No information for %s available (%s): %s' % (key, e, filename))

	@classmethod
	def get_appcenter_version(cls):
		''' Returns the version number of the App Center.
		As App Center within a domain may talk to each other it is necessary
		to ask whether they are compatible.
		The version number will rise whenever a change was made that may break compatibility.

		  1: initial app center 12/12 (not assigned, appcenter/version was not supported)
		  2: app center with remote installation 02/13 (not assigned, appcenter/version was not supported)
		  3: app center with version and only_dry_run 03/13
		'''
		return 3

	@classmethod
	def compatible_version(cls, other_version):
		''' Checks for compatibility with another version.
		For now we accept every other App Center and just warn
		in case of inequality.
		'''
		my_version = cls.get_appcenter_version()
		compatible = my_version == other_version
		if not compatible:
			MODULE.warn('App Center version check failed: %s != %s' % (my_version, other_version))
		return True

	@classmethod
	def get_server(cls, with_scheme=False):
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		if with_scheme:
			if not server.startswith('http'):
				server = 'https://%s' % server
		else:
			server = re.sub('https?://', '', server)
		return server

	def get_repository_url(self):
		# univention-repository/3.1/maintained/component/owncloud/all/
		return '%s/univention-repository/%s/maintained/component/%s' % (
			self.get_server(with_scheme=True),
			ucr.get('version/version', ''),
			self.component_id,
		)

	@classmethod
	def get_metainf_url(cls):
		return '%s/meta-inf/%s' % (
			cls.get_server(with_scheme=True),
			ucr.get('version/version', ''),
		)

	# regular expression to parse the apache HTML directory listing
	_reg_dir_listing = re.compile(""".*<td.*<a href="(?P<name>[^"/]+\.ini)">[^<]+</a>.*</td>.*""")

	@classmethod
	def find(cls, application_id):
		for application in cls.all():
			if application.id == application_id:
				return application

	@classmethod
	def _get_category_translations(cls, fake=False):
		if fake:
			cls._category_translations = {}
		if cls._category_translations is None:
			cls._category_translations = {}
			url = '%s/../categories.ini' % cls.get_metainf_url()
			try:
				# open .ini file
				MODULE.info('opening category translation file: %s' % url)
				fp = urlopen(url)
				config = ConfigParser.ConfigParser()
				config.readfp(fp)

				# get the translations for the current language
				loc = locale.getlocale()[0]
				if isinstance(loc, basestring):
					if not config.has_section(loc):
						loc = loc.split('_')[0]
					if config.has_section(loc):
						for k, v in config.items(loc):
							cls._category_translations[k] = v
			except (ConfigParser.Error, urllib2.HTTPError) as e:
				MODULE.warn('Could not load category translations from: %s\n%s' % (url, e))
			MODULE.info('loaded category translations: %s' % cls._category_translations)
		return cls._category_translations

	@classmethod
	def sync_with_server(cls):
		something_changed = False
		json_url = urljoin('%s/' % cls.get_metainf_url(), 'index.json.gz')
		MODULE.process('Downloading "%s"...' % json_url)
		try:
			zipped = StringIO(urlopen(json_url).read())
			content = GzipFile(mode='rb', fileobj=zipped).read()
		except:
			MODULE.error('Could not read "%s"' % json_url)
			raise
		try:
			json_apps = loads(content)
		except:
			MODULE.error('JSON malformatted: "%s"' % content)
			raise
		files_to_download = []
		files_in_json_file = []
		for appname, appinfo in json_apps.iteritems():
			for appfile, appfileinfo in appinfo.iteritems():
				filename = '%s.%s' % (appname, appfile)
				remote_md5sum = appfileinfo['md5']
				remote_url = appfileinfo['url']
				# compare with local cache
				cached_filename = os.path.join(CACHE_DIR, filename)
				files_in_json_file.append(cached_filename)
				local_md5sum = None
				m = md5()
				if os.path.exists(cached_filename):
					with open(cached_filename, 'r') as f:
						m.update(f.read())
						local_md5sum = m.hexdigest()
				if remote_md5sum != local_md5sum:
					# ask to re-download this file
					files_to_download.append((remote_url, filename))
					something_changed = True
		# remove those files that apparently do not exist on server anymore
		for cached_filename in glob(os.path.join(CACHE_DIR, '*')):
			if cached_filename not in files_in_json_file:
				MODULE.info('Deleting obsolete %s' % cached_filename)
				something_changed = True
				os.unlink(cached_filename)
		def _download(url, dest):
			MODULE.info('Downloading %s to %s' % (url, dest))
			try:
				urlcontent = urlopen(url)
			except Exception as e:
				MODULE.error('Error downloading %s: %s' % url, e)
			else:
				with open(dest, 'wb') as f:
					f.write(urlcontent.read())
		threads = []
		for filename_url, filename in files_to_download:
			# dont forget to quote: 'foo & bar.ini' -> 'foo%20&%20bar.ini'
			# but dont quote https:// -> https%3A//
			parts = list(urlsplit(filename_url))
			parts[2] = urllib2.quote(parts[2]) # 0 -> scheme, 1 -> netloc, 2 -> path
			filename_url = urlunsplit(parts)

			cached_filename = os.path.join(CACHE_DIR, filename)

			thread = Thread(target=_download, args=(filename_url, cached_filename))
			thread.start()
			threads.append(thread)
		for thread in threads:
			thread.join()
		if something_changed:
			# some variables could change apps.xml
			# e.g. Name, Description
			# TODO: changes take effect only after a restart of UMC
			#   and we cannot tell at the moment
			cls.update_conffiles()

			# TODO: would be nice if vendors provided ${app}16.png
			# special handling for icons
			for png in glob(os.path.join(FRONTEND_ICONS_DIR, '**', 'apps-*.png')):
				os.unlink(png)
			# images are created as -rw-------
			# change the mode to that every other image is installed with
			# (normally -rw-r--r--)
			template_png = glob(os.path.join(FRONTEND_ICONS_DIR, '**', '*.png'))[0]
			for png in glob(os.path.join(CACHE_DIR, '*.png')):
				app_id, ext = os.path.splitext(os.path.basename(png))
				# 50x50
				png_50 = os.path.join(FRONTEND_ICONS_DIR, '50x50', 'apps-%s.png' % app_id)
				shutil.copy2(png, png_50)
				shutil.copymode(template_png, png_50)
				# 16x16
				png_16 = os.path.join(FRONTEND_ICONS_DIR, '16x16', 'apps-%s.png' % app_id)
				image = Image.open(png)
				new_image = image.resize((16, 16))
				new_image.save(png_16)
				shutil.copymode(template_png, png_16)

	@classmethod
	def all_installed(cls, package_manager, force_reread=False, only_local=False, localize=True):
		applications = cls.all(force_reread=force_reread, only_local=only_local, localize=localize)
		return [app for app in applications if app.is_installed(package_manager)]

	@classmethod
	def all(cls, force_reread=False, only_local=False, localize=True):
		# reload ucr variables
		ucr.load()

		# load the first time the category translations
		cls._get_category_translations(fake=not localize)

		if force_reread:
			cls._all_applications = None

		if cls._all_applications is None:
			cls._all_applications = []
			# query all applications from the server
			ucr.load()
			if not only_local:
				cls.sync_with_server()
			for ini_file in glob(os.path.join(CACHE_DIR, '*.ini')):
				cls._all_applications.append(Application(ini_file, localize))

		# filter function
		def _included(the_list, app):
			if the_list == '*':
				return True
			the_list = map(str.lower, cls._reg_comma.split(the_list))
			if app.name.lower() in the_list:
				return True
			for category in app.get('categories'):
				if category.lower() in the_list:
					return True
			return False

		# filter blacklisted apps (by name and by category)
		filtered_applications = cls._all_applications
		blacklist = ucr.get('repository/app_center/blacklist')
		if blacklist:
			filtered_applications = [app for app in filtered_applications if not _included(blacklist, app)]

		# filter whitelisted apps (by name and by category)
		whitelist = ucr.get('repository/app_center/whitelist')
		if whitelist:
			# whitelist is stronger than blacklist: iterate over all_applications
			filtered_applications = [app for app in cls._all_applications if _included(whitelist, app) or app in filtered_applications]

		# group app entries by their ID
		app_map = {}
		for iapp in filtered_applications:
			if iapp.id not in app_map:
				app_map[iapp.id] = []
			app_map[iapp.id].append(iapp)

		# version string comparison
		def _version_cmp(iapp, japp):
			iver = LooseVersion(iapp.version)
			jver = LooseVersion(japp.version)
			return cmp(iver, jver)

		# pick the latest version of each app
		final_applications = []
		for iapps in app_map.itervalues():
			# sort apps after their version (latest first)
			iapps.sort(cmp=_version_cmp, reverse=True)

			used_app = iapps[0] # take newest one
			for iiapp in iapps:
				if component_registered(iiapp.component_id, ucr):
					if iiapp is not used_app:
						used_app = iiapp
						used_app.candidate = iapps[0]
						used_app.candidate.versions = iapps
					break
			# store all versions
			used_app.versions = iapps
			final_applications.append(used_app)

		return final_applications

	def to_dict(self, package_manager):
		ucr.load()
		res = copy.copy(self._options)
		res['component_id'] = self.component_id
		res['cannot_install_reason'], res['cannot_install_reason_detail'] = self.cannot_install_reason(package_manager)
		cannot_install_reason = res['cannot_install_reason']

		res['can_install'] = cannot_install_reason is None
		res['is_installed'] = res['can_uninstall'] = cannot_install_reason == 'installed'
		res['cannot_update_reason'], res['cannot_update_reason_detail'] = self.cannot_update_reason(package_manager)
		res['can_update'] = res['cannot_update_reason'] is None # faster than self.can_be_updated()
		res['allows_using'] = LICENSE.allows_using(self.get('notifyvendor'))
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['show_ldap_schema_confirmation'] = False # is done automatically
		#if res['is_master']:
		#	try:
		#		from univention.admin.handlers.computers import domaincontroller_backup
		#		lo = uldap.getMachineConnection()
		#		res['show_ldap_schema_confirmation'] = 0 < len(domaincontroller_backup.lookup(None, lo, None))
		#		del lo
		#	except (LDAPError, ImportError):
		#		res['show_ldap_schema_confirmation'] = True
		res['server'] = self.get_server()
		res['server_version'] = ucr.get('version/version')
		res['umc_module'] = 'apps'
		res['umc_flavor'] = self.id
		if self.candidate:
			# too expensive
			# res['candidate'] = self.candidate.to_dict(package_manager)
			res['candidate_version'] = self.candidate.version
			res['candidate_component_id'] = self.candidate.component_id
			res['candidate_server_role'] = self.candidate.get('serverrole')
			res['candidate_readmeupdate'] = self.candidate.get('readmeupdate')
		return res

	def cannot_update_reason(self, package_manager):
		if self.candidate:
			# check if installed. can have candidate without being installed
			#   e.g. only master packages installed
			if self.is_installed(package_manager):
				return self.candidate.cannot_install_reason(package_manager, check_is_installed=False)
			else:
				return 'not_installed', None
		else:
			return 'no_candidate', None

	def can_be_updated(self, package_manager):
		return self.cannot_update_reason(package_manager)[0] is None

	def cannot_install_reason(self, package_manager, check_is_installed=True):
		is_joined = os.path.exists('/var/univention-join/joined')
		server_role = ucr.get('server/role')
		if check_is_installed and self.is_installed(package_manager):
			return 'installed', None
		elif self.get('defaultpackagesmaster') and not is_joined:
			return 'not_joined', None
		elif self.get('serverrole') and server_role not in self.get('serverrole'):
			return 'wrong_serverrole', server_role
		elif self.get('minphysicalram') and get_current_ram_available() < self.get('minphysicalram'):
			return 'hardware_requirements', _('The application requires %d MB of free RAM but only %d MB are available.') % (self.get('minphysicalram'), get_current_ram_available())
		else:
			conflict_packages = []
			for package in self.get('conflictedsystempackages'):
				if package_manager.is_installed(package, reopen=False):
					conflict_packages.append(package)
			for app in self.all():
				if app.id in self.get('conflictedapps') or self.id in app.get('conflictedapps'):
					if any(package_manager.is_installed(package, reopen=False) for package in app.get('defaultpackages')):
						if app.name not in conflict_packages:
							# can conflict multiple times: conflicts with 
							# APP-1.1 and APP-1.2, both named APP
							conflict_packages.append(app.name)
			if conflict_packages:
				return 'conflict', conflict_packages
		return None, None

	def is_installed(self, package_manager):
		return all(package_manager.is_installed(package, reopen=False) for package in self.get('defaultpackages'))

	def can_be_installed(self, package_manager, check_is_installed=True):
		return not bool(self.cannot_install_reason(package_manager, check_is_installed)[0])

	def uninstall(self, package_manager, component_manager):
		# reload ucr variables
		ucr.load()

		try:
			# make sure that packages in 'defaultpackagesmaster' are never uninstalled
			is_master = ucr.get('server/role') in ('domaincontroller_master', 'domaincontroller_backup')
			to_keep = []
			if is_master and self.get('defaultpackagesmaster'):
				to_keep.extend(self.get('defaultpackagesmaster'))

			# remove all packages of the component
			package_manager.set_max_steps(200)
			package_manager.log('\n== UNINSTALLING %s AT %s ==\n' % (self.name, datetime.now()))
			package_manager.commit(remove=self.get('defaultpackages'), install=to_keep)
			package_manager.add_hundred_percent()

			# remove all dependencies
			package_manager.autoremove()
			package_manager.add_hundred_percent()

			# remove all existing component versions
			for iapp in self.versions:
				component_manager.remove_app(iapp)

			# update package information
			package_manager.update()
			self.update_conffiles()

			status = 200
		except:
			status = 500
		self._send_information('uninstall', status)
		return status == 200

	def install_dry_run(self, package_manager, component_manager, remove_component=True, username=None, password=None, only_master_packages=False, dont_remote_install=False, function='install', force=False):
		if self.candidate:
			return self.candidate.install_dry_run(package_manager, component_manager, remove_component, username, password, only_master_packages, dont_remote_install, function, force)
		MODULE.info('Invoke install_dry_run')
		result = None
		try:
			ucr.load()
			server_role = ucr.get('server/role')
			if function.startswith('update'):
				remote_function = 'update-schema'
			else:
				remote_function = 'install-schema'

			master_packages = self.get('defaultpackagesmaster')

			# connect to master/backups
			unreachable = []
			master_unreachable = False
			hosts_info = {}
			problems_with_hosts = False
			serious_problems_with_hosts = False
			if master_packages and not dont_remote_install:
				is_master = server_role == 'domaincontroller_master'
				hosts = self.find_all_hosts(is_master=is_master)
				for host, host_is_master in hosts:
					try:
						connection = UMCConnection(host)
						connection.auth(username, password)
					except HTTPException as e:
						MODULE.warn('%s: %s' % (host, e))
						unreachable.append(host)
						if host_is_master:
							master_unreachable = True
					else:
						host_info = {}
						try:
							host_version = connection.request('appcenter/version')
						except NotImplementedError:
							# command is not yet known (older app center)
							host_version = None
						host_info['compatible_version'] = Application.compatible_version(host_version)
						try:
							host_info['result'] = connection.request('appcenter/invoke_dry_run', {
								'function' : remote_function,
								'application' : self.id,
								'force' : force,
								'dont_remote_install' : True,
							})
						except NotImplementedError:
							# command is not yet known (older app center)
							host_info['result'] = {'can_continue' : False, 'serious_problems' : False}
						if not host_info['compatible_version'] or not host_info['result']['can_continue']:
							problems_with_hosts = True
							if host_info['result']['serious_problems'] or not host_info['compatible_version']:
								serious_problems_with_hosts = True
						hosts_info[host] = host_info

			# packages to install
			to_install = []
			if not only_master_packages:
				to_install.extend(self.get('defaultpackages'))
			MODULE.info('defaultpackages: %s' % (to_install, ))
			if server_role in ('domaincontroller_master', 'domaincontroller_backup', ):
				MODULE.info('Running on DC master or DC backup')
				if master_packages:
					to_install.extend(master_packages)

			# add the new component
			component_manager.put_app(self)
			package_manager.update()

			# get package objects
			to_install = package_manager.get_packages(to_install)

			# determine the changes
			# also check for changes from dist-upgrade (as it will
			#   be performed when installing).
			#   dry_run will throw away changes marked by upgrade
			package_manager.cache.upgrade(dist_upgrade=True)
			result = package_manager.mark(to_install, [], dry_run=True)
			result = dict(zip(['install', 'remove', 'broken'], result))
			MODULE.info('Package changes: %s' % (result, ))
			result['unreachable'] = unreachable
			result['master_unreachable'] = master_unreachable
			result['hosts_info'] = hosts_info
			result['problems_with_hosts'] = problems_with_hosts
			result['serious_problems_with_hosts'] = serious_problems_with_hosts

			if remove_component:
				# remove the newly added component
				MODULE.info('Remove component: %s' % (self.component_id, ))
				component_manager.remove_app(self)
				package_manager.update()
		except:
			MODULE.warn(traceback.format_exc())

		return result

	def uninstall_dry_run(self, package_manager):
		MODULE.info('Invoke uninstall_dry_run')
		package_manager.reopen_cache()
		to_uninstall = package_manager.get_packages(self.get('defaultpackages'))
		for package in to_uninstall:
			package.mark_delete()
		packages = [pkg.name for pkg in package_manager.packages() if pkg.is_auto_removable or pkg.marked_delete]
		package_manager.reopen_cache()
		return packages

	def install_master_packages_on_host(self, package_manager, function, host, username, password):
		if function == 'update':
			function = 'update-schema'
		else:
			function = 'install-schema'
		connection = UMCConnection(host, username, password)
		result = connection.request('appcenter/invoke', {'function' : function, 'application' : self.id, 'force' : True, 'dont_remote_install' : True})
		if result['can_continue']:
			all_errors = set()
			number_failures = 0
			number_failures_max = 20
			while True:
				try:
					result = connection.request('appcenter/progress')
				except (HTTPException, SocketError) as e:
					MODULE.warn('%s: appcenter/progress returned an error: %s' % (host, e))
					number_failures += 1
					if number_failures >= number_failures_max:
						MODULE.error('%s: Remote App Center cannot be contacted for more than %d seconds. Maybe just a long Apache Restart? Presume failure! Check logs on remote machine, maybe installation was successful.' % number_failures_max)
						return False
					time.sleep(1)
					continue
				else:
					# everything okay. reset "timeout"
					number_failures = 0
				MODULE.info('Result from %s: %r' % (host, result))
				info = result['info']
				steps = result['steps']
				errors = ['%s: %s' % (host, error) for error in result['errors']]
				if info:
					package_manager.progress_state.info(_('Output from %s: %s') % (host, info))
				if steps:
					steps = float(steps) # bug in package_manager in 3.1-0: int will result in 0 because of division and steps < max_steps
					package_manager.progress_state.percentage(steps)
				for error in errors:
					if error not in all_errors:
						package_manager.progress_state.error(error)
						all_errors.add(error)
				if result['finished'] is True:
					break
				time.sleep(0.1)
			return len(all_errors) == 0
		else:
			MODULE.warn('%r' % result)
			return False

	def find_all_hosts(self, is_master):
		lo = uldap.getMachineConnection(ldap_master=False)
		try:
			hosts = []
			if not is_master:
				hosts.append((get_master(lo), True))
			# use ucr to not find oneself!
			hosts.extend([(host, False) for host in get_all_backups(lo, ucr)])
			return hosts
		finally:
			del lo

	def install_master_packages_on_hosts(self, package_manager, remote_function, username, password, is_master):
		master_packages = self.get('defaultpackagesmaster')
		hosts = self.find_all_hosts(is_master=is_master)
		all_hosts_count = len(hosts)
		package_manager.set_max_steps(all_hosts_count * 200) # up to 50% if all hosts are installed
		# maybe we already installed local packages (on master)
		if is_master:
			# TODO: set_max_steps should reset _start_steps. need function like set_start_steps()
			package_manager.progress_state._start_steps = all_hosts_count * 100
		for host, host_is_master in hosts:
			package_manager.progress_state.info(_('Installing LDAP packages on %s') % host)
			try:
				if not self.install_master_packages_on_host(package_manager, remote_function, host, username, password):
					error_message = 'Unable to install %r on %s. Check /var/log/univention/management-console-module-appcenter.log on the host and this server. All errata updates have been installed on %s?' % (master_packages, host, host)
					raise Exception(error_message)
			except Exception as e:
				MODULE.error('%s: %s' % (host, e))
				if host_is_master:
					role = 'DC Master'
				else:
					role = 'DC Backup'
				# ATTENTION: This message is not localised. It is parsed by the frontend to markup this message! If you change this message, be sure to do the same in AppCenterPage.js
				package_manager.progress_state.error('Installing extension of LDAP schema for %s seems to have failed on %s %s' % (self.component_id, role, host))
				if host_is_master:
					raise # only if host_is_master!
			finally:
				package_manager.add_hundred_percent()

	def install(self, package_manager, component_manager, add_component=True, send_as='install', username=None, password=None, only_master_packages=False, dont_remote_install=False):
		if self.candidate:
			return self.candidate.install(package_manager, component_manager, add_component, send_as, username, password, only_master_packages, dont_remote_install)
		raised_before_installed = True
		try:
			remote_function = send_as
			if remote_function.startswith('install'):
				remote_function = 'install'
			if remote_function.startswith('update'):
				remote_function = 'update'
 			ucr.load()
 			is_master = ucr.get('server/role') == 'domaincontroller_master'
 			is_backup = ucr.get('server/role') == 'domaincontroller_backup'
			to_install = []
			if not only_master_packages:
				to_install.extend(self.get('defaultpackages'))
 			master_packages = self.get('defaultpackagesmaster')
 			if master_packages:
 				MODULE.info('Trying to install master packages on DC master and DC backup')
 				if is_master:
 					to_install.extend(master_packages)
 				else:
					# install remotely when on backup or slave.
					# remote installation on master is done after real installation
					if is_backup:
						# complete installation on backup, too
						to_install.extend(master_packages)
 					if username is None or dont_remote_install:
 						MODULE.warn('Not connecting to DC Master and Backups. Has to be done manually')
 					else:
						self.install_master_packages_on_hosts(package_manager, remote_function, username, password, is_master=False)

			if master_packages:
				# real installation is 50%
				package_manager.set_max_steps(200)
				if not is_master:
					# already have installed 50%
					package_manager.progress_state._start_steps = 100 # TODO: set_max_steps should reset _start_steps. need function like set_start_steps()

			# remove all existing component versions
			for iapp in self.versions:
				# dont remove yourself (if already added)
				if iapp is not self:
					component_manager.remove_app(iapp)

			# add the new repository component for the app
			if add_component:
				component_manager.put_app(self)
				package_manager.update()

			# install + dist_upgrade
			package_manager.log('\n== INSTALLING %s AT %s ==\n' % (self.name, datetime.now()))
			package_manager.commit(install=to_install, dist_upgrade=True)
			self.update_conffiles()

			# from now on better dont remove component
			raised_before_installed = False

			if master_packages and is_master:
				if username is None or dont_remote_install:
					MODULE.warn('Not connecting to DC Backups. Has to be done manually')
				else:
					self.install_master_packages_on_hosts(package_manager, remote_function, username, password, is_master=True)

			# successful installation
			status = 200
		except:
			MODULE.warn(traceback.format_exc())
			if raised_before_installed:
				component_manager.remove_app(self)
			status = 500
		self._send_information(send_as, status)
		return status == 200

	def _send_information(self, action, status):
		ucr.load()
		server = self.get_server(with_scheme=True)
		url = '%s/postinst' % (server, )
		uuid = LICENSE.uuid or '00000000-0000-0000-0000-000000000000'
		try:
			values = {'uuid': uuid,
				  'app': self.id,
				  'version': self.version,
				  'action': action,
				  'status': status,
				  'role': ucr.get('server/role'),
				  }
			request_data = urllib.urlencode(values)
			request = urllib2.Request(url, request_data)
			urlopen(request)
		except:
			MODULE.warn(traceback.format_exc())

	@classmethod
	def update_conffiles(cls):
		handler_commit(['/usr/share/univention-management-console/modules/apps.xml', '/usr/share/univention-management-console/i18n/de/apps.mo'])

