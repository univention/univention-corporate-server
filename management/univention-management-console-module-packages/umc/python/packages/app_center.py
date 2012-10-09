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

# for version comparison
from distutils.version import LooseVersion

from univention.management.console.log import MODULE

from univention.updater import UniventionUpdater
uu = UniventionUpdater(False)

import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

import util
from constants import *

import re
import ConfigParser
import locale
import json
import copy
import traceback

import univention.admin.uexceptions as udm_errors
from ldap import LDAPError

class License(object):
	def __init__(self, udmLicense = None):
		self.license = udmLicense

	def uuid(self, license):
		# TODO: this does not work yet
		# ucr set repository/app_center/debug/licence="fc452bc8-ae06-11e1-abab-00216a6f69f2"
		# ucr unset repository/app_center/debug/licence
		return ucr.get('repository/app_center/debug/licence', None)
		if self.license:
			return None
		return self.license.uuid

	def email_known(self):
		# at least somewhere at univention
		return self.uuid(license) is not None

	def allows_using(self, emailRequired):
		return self.email_known() or not emailRequired

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
	_regComma = re.compile('\s*,\s*')
	_regComponentID = re.compile(r'.*/(?P<id>[^/]+)(\.ini)?')
	_all_applications = None
	_category_translations = {}

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
				self._options[ikey] = self._regComma.split(ival)
			else:
				self._options[ikey] = []

		# localize the category names
		category_translations = self._get_category_translations()
		self._options['categories'] = [ category_translations.get(icat.lower()) or icat for icat in self.get('categories') ]

		# return a proper URL for local files
		for ikey in ('screenshot', 'licensefile'):
			if self.get(ikey):
				self._options[ikey] = urllib2.urlparse.urljoin('%s/' % self.get_repository_url(), self.get(ikey))

		# get the name of the component
		m = self._regComponentID.match(url)
		self.component_id = 'unknown'
		if m:
			self.component_id = m.groupdict()['id']

		# save important meta data
		self.id = self._options['id'] = self._options['id'].lower()
		self.name = self._options['name']
		self.icon = self._options['icon'] = '%s.png' % url[:-4]
		self.version = self._options['version']

	def get(self, key):
		'''Helper function to access configuration elements of the application's .ini
		file. If element is not given, returns (for string elements) an empty string.
		'''
		v = self._options.get(key.lower())
		if v is None:
			return ''
		return v

	@classmethod
	def get_server(cls):
		return ucr.get('repository/app_center/server', 'appcenter.software-univention.de')

	@classmethod
	def get_repository_url(cls):
		return 'http://%s/meta-inf/%s' % (
			cls.get_server(),
			ucr.get('version/version', ''),
		)

	# regular expression to parse the apache HTML directory listing
	_regDirListing = re.compile(""".*<td.*<a href="(?P<name>[^"/]+\.ini)">[^<]+</a>.*</td>.*""")

	@classmethod
	def find(cls, id):
		for application in cls.all():
			if application.id == id:
				return application

	@classmethod
	def _get_category_translations(cls):
		if not cls._category_translations:
			url = '%s/../categories.ini' % cls.get_repository_url()
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
	def all(cls):
		# reload ucr variables
		ucr.load()

		if cls._all_applications is None:
			cls._all_applications = []

			# query all applications from the server
			ucr.load()
			url = cls.get_repository_url()
			try:
				for iline in urllib2.urlopen(url):
					# parse the server's directory listing
					m = cls._regDirListing.match(iline)
					if m:
						# try to load and parse application's .ini file
						ifilename = m.group('name')
						iurl = url + '/' + ifilename
						try:
							cls._all_applications.append(Application(iurl))
						except (ConfigParser.Error, urllib2.HTTPError, ValueError, KeyError) as e:
							MODULE.warn('Could not open application file: %s\n%s' % (iurl, e))
			except urllib2.HTTPError as e:
				MODULE.warn('Could not query App Center host at: %s\n%s' % (url, e))

		# filter function
		def _included(the_list, app):
			if the_list == '*':
				return True
			the_list = map(str.lower, cls._regComma.split(the_list))
			if app.name in the_list:
				return True
			for category in app.get('categories'):
				if category in the_list:
					return True
			return False

		# filter blacklisted apps (by name and by category)
		filtered_applications = cls._all_applications
		blacklist = ucr.get('repository/app_center/blacklist')
		if blacklist:
			filtered_applications = [app for app in filtered_applications if not _included(blacklist, app)]
		else:
			filtered_applications = filtered_applications

		# filter whitelisted apps (by name and by category)
		whitelist = ucr.get('repository/app_center/whitelist')
		if whitelist:
			filtered_applications = [app for app in filtered_applications if _included(whitelist, app) or app in filtered_applications]

		# group app entries by their ID
		appMap = {}
		for iapp in filtered_applications:
			if iapp.id not in appMap:
				appMap[iapp.id] = []
			appMap[iapp.id].append(iapp)

		# version string comparison
		def _versionCmp(iapp, japp):
			iver = LooseVersion(iapp.version)
			jver = LooseVersion(japp.version)
			if iver == jver:
				return 0
			if iver > jver:
				return 1
			return -1

		# pick the latest version of each app
		final_applications = []
		for iid, iapps in appMap.iteritems():
			# sort apps after their version (latest first)
			iapps.sort(cmp=_versionCmp, reverse=True)

			# store all versions
			iapps[0].versions = iapps
			final_applications.append(iapps[0])

		return final_applications

	def to_dict_overwiew(self, package_manager):
		res = copy.copy(self._options)
		res['allows_using'] = LICENSE.allows_using(self.get('emailrequired'))
		cannot_install_reason, cannot_install_reason_detail = self.cannot_install_reason(package_manager)
		res['can_update'] = self.can_be_updated() and cannot_install_reason == 'installed'
		res['can_install'] = cannot_install_reason is None
		res['is_installed'] = cannot_install_reason == 'installed'
		return res

	def can_be_updated(self):
		oldAppRegistered = False
		if len(self.versions) > 1:
			oldAppRegistered = any(['%s/%s' % (COMPONENT_BASE, iapp.component_id) in ucr for iapp in self.versions[1:]])
		return oldAppRegistered

	def cannot_install_reason(self, package_manager):
		is_joined = os.path.exists('/var/univention-join/joined')
		server_role = ucr.get('server/role')
		if all(package_manager.is_installed(package) for package in self.get('defaultpackages')):
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

	def to_dict_detail(self, package_manager):
		ucr.load()
		res = copy.copy(self._options)
		res['cannot_install_reason'], res['cannot_install_reason_detail'] = self.cannot_install_reason(package_manager)
		cannot_install_reason = res['cannot_install_reason']
		res['can_update'] = self.can_be_updated() and cannot_install_reason == 'installed'
		res['can_install'] = cannot_install_reason is None
		res['can_uninstall'] = cannot_install_reason == 'installed'
		res['allows_using'] = LICENSE.allows_using(self.get('emailrequired'))
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['server'] = self.get_server()
		res['server_version'] = ucr.get('version/version')
		return res

	def uninstall(self, package_manager, component_manager):
		# reload ucr variables
		ucr.load()

		try:
			to_uninstall = self.get('defaultpackages')
			max_steps = 100 + len(to_uninstall) * 100
			package_manager.set_max_steps(max_steps)
			for package in to_uninstall:
				package_manager.uninstall(package)
				package_manager.add_hundred_percent()

			# remove all existing component versions
			for iapp in self.versions:
				component_manager.remove(iapp.component_id)

			package_manager.update()
			package_manager.add_hundred_percent()
			status = 200
		except:
			status = 500
		return self._send_information('uninstall', status)

	def install(self, package_manager, component_manager):
		try:
			# remove all existing component versions
			for iapp in self.versions:
				component_manager.remove(iapp.component_id)

			ucr.load()
			is_master = ucr.get('server/role') == 'domaincontroller_master'
			server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
			to_install = self.get('defaultpackages')
			if is_master and self.get('defaultpackagesmaster'):
				to_install.extend(self.get('defaultpackagesmaster'))
			max_steps = 100 + len(to_install) * 100
			package_manager.set_max_steps(max_steps)
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
			package_manager.update()
			package_manager.add_hundred_percent()
			for package in to_install:
				package_manager.install(package)
				package_manager.add_hundred_percent()
			status = 200
		except Exception as e:
			MODULE.warn(traceback.format_exc())
			status = 500
		return self._send_information('install', status)

	def _send_information(self, action, status):
		if not self.get('emailrequired'):
			return
		ucr.load()
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		try:
			url = 'https://%(server)s/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s&version=%(version)s'
			url = url % {
				'server' : server,
				'uuid' : LICENSE.uuid(),
				'app' : self.id,
				'version' : self.version,
				'action' : action,
				'status' : status,
			}
			request = urllib2.Request(url, headers={'User-agent' : 'UMC/AppCenter'})
			#urllib2.urlopen(request)
			return url
		except Exception as e:
			MODULE.warn(traceback.format_exc())
			raise

