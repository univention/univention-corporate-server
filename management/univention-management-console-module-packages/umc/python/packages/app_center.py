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
import urllib2
import os.path
import threading

# for version comparison
from distutils.version import LooseVersion

from univention.management.console.log import MODULE

from univention.updater import UniventionUpdater
uu = UniventionUpdater(False)

import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

import util
from constants import COMPONENT_BASE

import re
import ConfigParser
import locale
import copy
import traceback

import univention.admin.uexceptions as udm_errors
from ldap import LDAPError

class License(object):
	def __init__(self, license=None):
		self.license = license

	def dump_data(self):
		# we could return infos we have in this object itself.
		# but dont be too clever here. just dump
		# everything we have in LDAP.
		try:
			ret = {}
			import univention.uldap as uldap
			_lo = uldap.getMachineConnection()
			data = _lo.search('objectClass=univentionLicense')
			del _lo
			# just one license (should be always the case)
			# return the dictionary without the dn
			data = data[0][1]
			# make sure data is dictionary
			ret.update(data)
			return ret
		except Exception as e:
			# no udm, no ldap, malformed return value, whatever
			MODULE.error('getting License from LDAP failed: %s' % e)
			return None

	@property
	def uuid(self):
		try:
			if self.license.licenseKeyID:
				return self.license.licenseKeyID
		except AttributeError:
			return None

		return None

	def email_known(self):
		# at least somewhere at univention
		return self.uuid is not None

	def allows_using(self, email_required):
		return self.email_known() or not email_required

try:
	import univention.admin.filter as udm_filter  # needed for udm_license
	import univention.admin.license as udm_license
	import univention.uldap as uldap

	_lo = uldap.getMachineConnection()
	udm_license.init_select(_lo, 'admin')
	del _lo
	LICENSE = License(udm_license._license)

except (ImportError, LDAPError, udm_errors.base) as err:
	# no licensing available
	MODULE.warn('Failed to load license information: %s' % err)
	LICENSE = License()


class Application(object):
	_reg_comma = re.compile('\s*,\s*')
	_reg_component_id = re.compile(r'.*/(?P<id>[^/]+)\.ini')
	_all_applications = None
	_category_translations = None

	def __init__(self, url):
		# load config file
		self._options = {}
		fp = urllib2.urlopen(url)
		config = ConfigParser.ConfigParser()
		config.readfp(fp)

		# copy values from config file
		for k, v in config.items('Application'):
			self._options[k] = v

		# overwrite english values with localized translations
		loc = locale.getlocale()[0]
		if isinstance(loc, basestring):
			if not config.has_section(loc):
				loc = loc.split('_')[0]
			if config.has_section(loc):
				for k, v in config.items(loc):
					self._options[k] = v

		# parse boolean values
		for ikey in ('emailrequired',):
			if ikey in self._options:
				self._options[ikey] = config.getboolean('Application', ikey)
			else:
				self._options[ikey] = False

		# parse list values
		for ikey in ('categories', 'defaultpackages', 'conflictedsystempackages', 'defaultpackagesmaster', 'conflictedapps', 'serverrole'):
			ival = self.get(ikey)
			if ival:
				self._options[ikey] = self._reg_comma.split(ival)
			else:
				self._options[ikey] = []

		# localize the category names
		category_translations = self._get_category_translations()
		self._options['categories'] = [ category_translations.get(icat.lower()) or icat for icat in self.get('categories') ]

		# return a proper URL for local files
		for ikey in ('screenshot',):
			if self.get(ikey):
				self._options[ikey] = urllib2.urlparse.urljoin('%s/' % self.get_metainf_url(), self.get(ikey))

		# save important meta data
		self.id = self._options['id'] = self._options['id'].lower()
		self.name = self._options['name']
		self.icon = self._options['icon'] = '%s.png' % url[:-4]
		self.version = self._options['version']

		# get the name of the component
		m = self._reg_component_id.match(url)
		self.component_id = 'unknown'
		if m:
			self.component_id = m.groupdict()['id']

		# fetch files via threads
		threads = [
			threading.Thread(target=self._fetch_file, args=('licenseagreement', self.get_repository_url() + '/LICENSE_AGREEMENT')),
			threading.Thread(target=self._fetch_file, args=('readmeupdate', self.get_repository_url() + '/README_UPDATE')),
		]
		for ithread in threads:
			ithread.start()
		for ithread in threads:
			ithread.join()

	def get(self, key):
		'''Helper function to access configuration elements of the application's .ini
		file. If element is not given, returns (for string elements) an empty string.
		'''
		v = self._options.get(key.lower())
		if v is None:
			return ''
		return v

	def _fetch_file(self, key, url):
		try:
			# open the license file 
			fp = urllib2.urlopen(url)
			self._options[key] = ''.join(fp.readlines()).strip()
		except (urllib2.HTTPError, urllib2.URLError) as e:
			MODULE.warn('No information for %s available (%s): %s' % (key, e, url))

	@classmethod
	def get_server(cls):
		return ucr.get('repository/app_center/server', 'appcenter.software-univention.de')

	def get_repository_url(self):
		# univention-repository/3.1/maintained/component/owncloud/all/
		return 'http://%s/univention-repository/%s/maintained/component/%s' % (
			self.get_server(),
			ucr.get('version/version', ''),
			self.component_id,
		)

	@classmethod
	def get_metainf_url(cls):
		return 'http://%s/meta-inf/%s' % (
			cls.get_server(),
			ucr.get('version/version', ''),
		)

	# regular expression to parse the apache HTML directory listing
	_reg_dir_listing = re.compile(""".*<td.*<a href="(?P<name>[^"/]+\.ini)">[^<]+</a>.*</td>.*""")

	@classmethod
	def find(cls, id):
		for application in cls.all():
			if application.id == id:
				return application

	@classmethod
	def _get_category_translations(cls):
		if cls._category_translations == None:
			cls._category_translations = {}
			url = '%s/../categories.ini' % cls.get_metainf_url()
			try:
				# open .ini file
				MODULE.info('opening category translation file: %s' % url)
				fp = urllib2.urlopen(url)
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
	def all(cls, force_reread=False):
		# reload ucr variables
		ucr.load()

		# load the first time the category translations
		cls._get_category_translations()

		if force_reread:
			cls._all_applications = None

		if cls._all_applications is None:
			# query all applications from the server
			ucr.load()
			url = cls.get_metainf_url()
			try:
				cls._all_applications = []

				threads = []
				for iline in urllib2.urlopen(url):
					# parse the server's directory listing
					m = cls._reg_dir_listing.match(iline)
					if m:
						# try to load and parse application's .ini file
						ifilename = m.group('name')
						iurl = url + '/' + ifilename

						# thread function
						def _append_app(myurl):
							try:
								cls._all_applications.append(Application(myurl))
							except (ConfigParser.Error, urllib2.HTTPError, urllib2.URLError, ValueError, KeyError) as e:
								MODULE.warn('Could not open application file: %s\n%s' % (myurl, e))

						# start a new thread for fetching the application information
						thread = threading.Thread(target=_append_app, args=(iurl,))
						thread.start()
						threads.append(thread)

				# wait until all threads are finished
				for ithread in threads:
					ithread.join()

			except (urllib2.HTTPError, urllib2.URLError) as e:
				MODULE.warn('Could not query App Center host at: %s\n%s' % (url, e))
				raise

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
		for iid, iapps in app_map.iteritems():
			# sort apps after their version (latest first)
			iapps.sort(cmp=_version_cmp, reverse=True)

			# store all versions
			iapps[0].versions = iapps
			final_applications.append(iapps[0])

		return final_applications

	def to_dict(self, package_manager):
		ucr.load()
		res = copy.copy(self._options)
		res['cannot_install_reason'], res['cannot_install_reason_detail'] = self.cannot_install_reason(package_manager)
		cannot_install_reason = res['cannot_install_reason']

		res['allows_using'] = LICENSE.allows_using(self.get('emailrequired'))

		res['can_update'] = self.can_be_updated() and cannot_install_reason == 'installed'
		res['can_install'] = cannot_install_reason is None
		res['is_installed'] = res['can_uninstall'] = cannot_install_reason == 'installed'
		res['allows_using'] = LICENSE.allows_using(self.get('emailrequired'))
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['server'] = self.get_server()
		res['server_version'] = ucr.get('version/version')
		return res

	def can_be_updated(self):
		old_app_registered = False
		if len(self.versions) > 1:
			old_app_registered = any(['%s/%s' % (COMPONENT_BASE, iapp.component_id) in ucr for iapp in self.versions[1:]])
		return old_app_registered

	def cannot_install_reason(self, package_manager):
		is_joined = os.path.exists('/var/univention-join/joined')
		server_role = ucr.get('server/role')
		if all(package_manager.is_installed(package, reopen=False) for package in self.get('defaultpackages')):
			return 'installed', None
		elif self.get('defaultpackagesmaster') and not is_joined:
			return 'not_joined', None
		elif self.get('serverrole') and server_role not in self.get('serverrole'):
			return 'wrong_serverrole', server_role
		else:
			conflict_packages = []
			for package in self.get('conflictedsystempackages'):
				if package_manager.is_installed(package):
					conflict_packages.append(package)
			for app in self.all():
				if app.id in self.get('conflictedapps') or self.id in app.get('conflictedapps'):
					if any(package_manager.is_installed(package) for package in app.get('defaultpackages')):
						if app.name not in conflict_packages:
							# can conflict multiple times: conflicts with 
							# APP-1.1 and APP-1.2, both named APP
							conflict_packages.append(app.name)
			if conflict_packages:
				return 'conflict', conflict_packages
		return None, None

	def can_be_installed(self, package_manager):
		return not bool(self.cannot_install_reason(package_manager)[0])

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
			package_manager.commit(remove=self.get('defaultpackages'), install=to_keep)
			package_manager.add_hundred_percent()

			# remove all dependencies
			package_manager.autoremove()
			package_manager.add_hundred_percent()

			# remove all existing component versions
			for iapp in self.versions:
				component_manager.remove(iapp.component_id)

			# update package information
			package_manager.update()

			status = 200
		except:
			status = 500
		self._send_information('uninstall', status)
		return status == 200

	def install(self, package_manager, component_manager):
		try:
			# remove all existing component versions
			for iapp in self.versions:
				component_manager.remove(iapp.component_id)

			# add the new repository component for the app
			ucr.load()
			is_master = ucr.get('server/role') in ('domaincontroller_master', 'domaincontroller_backup')  # packages need to be installed on backup AND master systems
			server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
			to_install = self.get('defaultpackages')
			if is_master and self.get('defaultpackagesmaster'):
				to_install.extend(self.get('defaultpackagesmaster'))
			data = {
				'server' : server,
				'prefix' : '',
				'maintained' : True,
				'unmaintained' : False,
				'enabled' : True,
				'name' : self.component_id,
				'description' : self.get('description'),
				'username' : '',
				'password' : '',
				'version' : 'current',
				'localmirror' : 'false',
			}
			with util.set_save_commit_load(ucr) as super_ucr:
				component_manager.put(data, super_ucr)

			# update and install + dist_upgrade
			package_manager.update()
			package_manager.commit(install=to_install, dist_upgrade=True)

			# successful installation
			status = 200
		except:
			MODULE.warn(traceback.format_exc())
			status = 500
		self._send_information('install', status)
		return status == 200

	def _send_information(self, action, status):
		if not self.get('emailrequired'):
			return
		ucr.load()
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		try:
			url = 'https://%(server)s/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s&version=%(version)s&role=%(role)s'
			url = url % {
				'server' : server,
				'uuid' : LICENSE.uuid,
				'app' : self.id,
				'version' : self.version,
				'action' : action,
				'status' : status,
				'role': ucr.get('server/role'),
			}
			#request = urllib2.Request(url, headers={'User-agent' : 'UMC/AppCenter'})
			#urllib2.urlopen(request)
			return url
		except:
			MODULE.warn(traceback.format_exc())
			raise

