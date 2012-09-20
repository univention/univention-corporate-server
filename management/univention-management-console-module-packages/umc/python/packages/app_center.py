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

try:
	import univention.admin.license as udm_license
except ImportError:
	# uh uh, no udm with all its licensing stuff...
	udm_license = None

class License(object):
	def __init__(self, udm_license):
		self.license = udm_license # may be None

	@property
	def uuid(self):
		return None
		return 'fc452bc8-ae06-11e1-abab-00216a6f69f2'
		raise NotImplentedError
		if self.license is None:
			return None
		return self.license._license.uuid

	def email_known(self):
		# at least somewhere at univention
		return self.uuid is not None

	def allows_using(self, app):
		return self.email_known() or not app.get('emailRequired')

LICENSE = License(udm_license)

class Application(object):
	_regComma = re.compile('\s*,\s*')
	def __init__(self, url):
		self._options = dict()
		try:
			# load config file
			fp = urllib2.urlopen(url)
			config = ConfigParser.ConfigParser()
			config.readfp(fp)

			# copy values from config file
			for k, v in config.items('Application'):
				self._options[k] = v

			# overwrite english values with localized translations
			loc = locale.getdefaultlocale()[0]
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
			for ikey in ('categories', 'defaultpackages', 'conflictedsystempackages', 'defaultpackagesmaster', 'conflictedapps'):
				ival = self.get(ikey)
				if ival:
					self._options[ikey] = self._regComma.split(ival)
				else:
					self._options[ikey] = []

		except ConfigParser.Error as err:
			# reraise as ValueError
			raise ValueError(err.message)

		# save the url
		self.id = self._options['id'] = self._options['id'].lower()
		self.name = self._options['name']
		self.icon = self._options['icon'] = '%s.png' % url[:-4]

	def get(self, key):
		'''Helper function to access configuration elements of the application's .ini
		file. If element is not given, returns (for string elements) an empty string.
		'''
		v = self._options.get(key.lower())
		if v == None:
			return ''
		return v

	@classmethod
	def get_server(cls):
		return 'http://%s/meta-inf/%s' % (
			ucr.get('repository/app_center/server', 'appcenter.software-univention.de'),
			ucr.get('version/version', ''),
		)

	_regDirListing = re.compile(""".*<td.*<a href="(?P<name>[^"/]+\.ini)">[^<]+</a>.*</td>.*""")

	@classmethod
	def all(cls):
		ucr.load()

		# query all applications from the server
		all_applications = []
		url = cls.get_server() % ucr
		try:
			print 'open %s' % url
			for iline in urllib2.urlopen(url):
				# parse the server's directory listing
				m = cls._regDirListing.match(iline)
				if m:
					# try to load and parse application's .ini file
					ifilename = m.group('name')
					iurl = url + '/' + ifilename
					try:
						all_applications.append(Application(iurl))
					except ValueError as e:
						MODULE.warn('Could not open application file: %s\n%s' % (iurl, e))
		except urllib2.HTTPError as e:
			MODULE.warn('Could not query App Center host at:%s\n%s' % (url, e))

		# filter function
		def _included(the_list, app):
			if the_list == '*':
				return True
			the_list = map(str.lower, the_list.split(':'))
			if app.name in the_list:
				return True
			for category in app.categories:
				if category in the_list:
					return True
			return False

		# filter blacklisted apps (by name and by category)
		blacklist = ucr.get('repository/app_center/blacklist')
		if blacklist:
			filtered_applications = [app for app in all_applications if not _included(blacklist, app)]
		else:
			filtered_applications = all_applications

		# filter whitelisted apps (by name and by category)
		whitelist = ucr.get('repository/app_center/whitelist')
		if whitelist:
			filtered_applications = [app for app in all_applications if _included(whitelist, app) or app in filtered_applications]

		return filtered_applications

	def to_dict_overwiew(self):
		res = copy.copy(self._options)
		res['allows_using'] = LICENSE.allows_using(self)
		return res

	def to_dict_detail(self, module_instance):
		res = copy.copy(self._options)

		#TODO: adapt conditions
		can_uninstall = res['can_uninstall'] = False #module_instance.package_manager.is_installed(self.package_name)
		res['can_install'] = True #not can_uninstall and (is_joined or not self.master_packages)
		res['allows_using'] = LICENSE.allows_using(self)
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['server'] = self.get_server()
		return res

	@classmethod
	def find(cls, id):
		for application in cls.all():
			if application.id == id:
				return application

	def uninstall(self, module_instance):
		try:
			module_instance.package_manager.set_max_steps(200)
			module_instance.package_manager.uninstall(self.package_name)
			module_instance.package_manager.add_hundred_percent()
			module_instance._del_component(self.id)
			module_instance.package_manager.update()
			module_instance.package_manager.add_hundred_percent()
			status = 200
		except:
			status = 500
		return self._send_information('uninstall', status)

	def install(self, module_instance):
		try:
			ucr.load()
			is_master = ucr.get('server/role') == 'domaincontroller_master'
			server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
			to_install = [self.package_name]
			if is_master and self.master_packages:
				to_install.extend(self.master_packages)
			max_steps = 100 + len(to_install) * 100
			MODULE.warn(str(max_steps))
			module_instance.package_manager.set_max_steps(max_steps)
			data = {
				'server' : server,
				'prefix' : '',
				'maintained' : True,
				'unmaintained' : False,
				'enabled' : True,
				'name' : self.id,
				'description' : self.description,
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
		return self._send_information('install', status)

	def _send_information(self, action, status):
		ucr.load()
		server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
		try:
			url = 'https://%(server)s/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s'
			url = 'http://www.univention.de/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s'
			url = url % {'server' : server, 'uuid' : LICENSE.uuid, 'app' : self.id, 'action' : action, 'status' : status}
			request = urllib2.Request(url, headers={'User-agent' : 'UMC/AppCenter'})
			#urllib2.urlopen(request)
			return url
		except Exception as e:
			MODULE.warn(str(e))
			raise

