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

from univention.management.console.log import MODULE

import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

import re
import ConfigParser
import locale
import json
import copy

class License(object):
	def uuid(self, license):
		# ucr set repository/app_center/debug/licence="fc452bc8-ae06-11e1-abab-00216a6f69f2"
		# ucr unset repository/app_center/debug/licence
		return ucr.get('repository/app_center/debug/licence', None)
		if self.license is None:
			return None
		return self.license._license.uuid

	def email_known(self, license):
		# at least somewhere at univention
		return self.uuid(license) is not None

	def allows_using(self, app, license):
		return self.email_known(license) or not app.get('emailrequired')

LICENSE = License()

class Application(object):
	_regComma = re.compile('\s*,\s*')
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

		# return a proper URL for a given screenshot (if it exists)
		if self.get('screenshot'):
			self._options['screenshot'] = urllib2.urlparse.urljoin('%s/' % self.get_repository_url(), self.get('screenshot'))

		# save the url
		self.id = self._options['id'] = self._options['id'].lower()
		self.name = self._options['name']
		self.icon = self._options['icon'] = '%s.png' % url[:-4]

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
						except (ConfigParser.Error, urllib2.HTTPError) as e:
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

		return filtered_applications

	def to_dict_overwiew(self, module_instance, license):
		res = copy.copy(self._options)
		res['allows_using'] = LICENSE.allows_using(self, license)
		res['can_be_installed'] = self.can_be_installed(module_instance)
		return res

	def cannot_install_reason(self, module_instance):
		is_joined = os.path.exists('/var/univention-join/joined')
		server_role = ucr.get('server/role')
		if all(module_instance.package_manager.is_installed(package) for package in self.get('defaultpackages')):
			return 'installed', None
		elif self.get('defaultpackagesmaster') and not is_joined:
			return 'not_joined', None
		elif self.get('serverrole') and server_role not in self.get('serverrole'):
			return 'wrong_serverrole', server_role
		else:
			conflict_packages = []
			for package in self.get('conflictedsystempackages'):
				if module_instance.package_manager.is_installed(package):
					conflict_packages.append(package)
			for app in self.all():
				if app.id in self.get('conflictedapps') or self.id in app.get('conflictedapps'):
					if any(module_instance.package_manager.is_installed(package) for package in app.get('defaultpackages')):
						if app.name not in conflict_packages:
							# can conflict multiple times: conflicts with 
							# APP-1.1 and APP-1.2, both named APP
							conflict_packages.append(app.name)
			if conflict_packages:
				return 'conflict', conflict_packages
		return None, None

	def can_be_installed(self, module_instance):
		return not bool(self.cannot_install_reason(module_instance)[0])

	def to_dict_detail(self, module_instance, license):
		ucr.load()
		res = copy.copy(self._options)
		res['cannot_install_reason'], res['cannot_install_reason_detail'] = self.cannot_install_reason(module_instance)
		cannot_install_reason = res['cannot_install_reason']
		res['can_install'] = cannot_install_reason is None
		res['can_uninstall'] = cannot_install_reason == 'installed'
		res['allows_using'] = LICENSE.allows_using(self, license)
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['server'] = self.get_server()
		return res

	def uninstall(self, module_instance, license):
		try:
			to_uninstall = self.get('defaultpackages')
			max_steps = 100 + len(to_uninstall) * 100
			module_instance.package_manager.set_max_steps(max_steps)
			for package in to_uninstall:
				module_instance.package_manager.uninstall(package)
				module_instance.package_manager.add_hundred_percent()
			module_instance._del_component(self.id)
			module_instance.package_manager.update()
			module_instance.package_manager.add_hundred_percent()
			status = 200
		except:
			status = 500
		return self._send_information('uninstall', status, license)

	def install(self, module_instance, license):
		try:
			ucr.load()
			is_master = ucr.get('server/role') == 'domaincontroller_master'
			server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
			to_install = self.get('defaultpackages')
			if is_master and self.get('defaultpackagesmaster'):
				to_install.extend(self.get('defaultpackagesmaster'))
			max_steps = 100 + len(to_install) * 100
			module_instance.package_manager.set_max_steps(max_steps)
			data = {
				'server' : server,
				'prefix' : '',
				'maintained' : True,
				'unmaintained' : False,
				'enabled' : True,
				'name' : self.id,
				'description' : self.get('description'),
				'username' : '',
				'password' : '',
				'version' : 'current',
				}
			with module_instance.set_save_commit_load() as super_ucr:
				module_instance._put_component(data, super_ucr)
			module_instance.package_manager.update()
			module_instance.package_manager.add_hundred_percent()
			for package in to_install:
				module_instance.package_manager.install(package)
				module_instance.package_manager.add_hundred_percent()
			status = 200
		except Exception as e:
			MODULE.warn(str(e))
			status = 500
		return self._send_information('install', status, license)

	def _send_information(self, action, status, license):
		if not self.get('emailrequired'):
			return
		ucr.load()
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		try:
			url = 'https://%(server)s/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s'
			url = url % {'server' : server, 'uuid' : LICENSE.uuid(license), 'app' : self.id, 'action' : action, 'status' : status}
			request = urllib2.Request(url, headers={'User-agent' : 'UMC/AppCenter'})
			#urllib2.urlopen(request)
			return url
		except Exception as e:
			MODULE.warn(str(e))
			raise

