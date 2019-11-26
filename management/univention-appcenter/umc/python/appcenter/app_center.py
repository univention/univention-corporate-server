#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management / app center
#
# Copyright 2012-2019 Univention GmbH
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

# standard library
import shutil
import platform
import time
from distutils.version import LooseVersion
from gzip import GzipFile
import tarfile
from math import ceil
import base64
from StringIO import StringIO
import ConfigParser
import copy
import inspect
import locale
import os.path
import os
import stat
import re
from threading import Thread
import traceback
import urllib2
from glob import glob
from urlparse import urlsplit, urljoin
from ldap import LDAPError
from ldap.filter import escape_filter_chars
from operator import attrgetter
import subprocess
from tempfile import NamedTemporaryFile
from json import loads

# univention
from univention.management.console.log import MODULE
import univention.uldap as uldap
import univention.management.console as umc
from univention.lib.umc import Client, ConnectionError, Forbidden, HTTPError
import univention.admin.handlers.appcenter.app as appcenter_udm_module
import univention.admin.handlers.container.cn as container_udm_module
import univention.admin.uexceptions as udm_errors

# local application
from univention.appcenter.utils import app_ports, gpg_verify, container_mode, send_information
from univention.management.console.modules.decorators import reloading_ucr
from univention.management.console.ldap import machine_connection, get_machine_connection
from univention.management.console.modules.appcenter.util import urlopen, get_free_disk_space, get_current_ram_available, component_registered, component_current, get_master, get_all_backups, get_all_hosts, set_save_commit_load, get_md5, verbose_http_error
from univention.appcenter.app_cache import AppCache, Apps
from univention.appcenter.actions import get_action
from univention.appcenter.ucr import ucr_instance, ucr_save

CACHE_DIR = AppCache().get_cache_dir()
LOCAL_ARCHIVE = '/usr/share/univention-appcenter/local/all.tar.gz'
FRONTEND_ICONS_DIR = '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons'
UCR_VARIABLE_TOKEN = re.compile('@%@')
ucr = ucr_instance()

_ = umc.Translation('univention-management-console-module-appcenter').translate


class License(object):

	def __init__(self):
		self._uuid = None

	@property
	def uuid(self):
		self.reload()
		return self._uuid

	def reload(self, force=False):
		if self._uuid is not None and not force:
			# license with uuid has already been found
			return
		self._uuid = None
		# last time we checked, no uuid was found
		# but maybe the user installed a new license?
		try:
			lo = get_machine_connection(write=False)[0]
			data = lo.search('objectClass=univentionLicense')
			self._uuid = data[0][1]['univentionLicenseKeyID'][0]
		except Exception as e:
			# no licensing available
			MODULE.warn('Failed to load license information: %s' % e)

	def email_known(self):
		# at least somewhere at univention
		return self.uuid is not None

	def allows_using(self, email_required):
		return self.email_known() or not email_required


LICENSE = License()


class AppcenterServerContactFailed(Exception):

	def __init__(self, exc):
		message = _('Error while contacting the App Center server. %s') % (verbose_http_error(exc),)
		super(AppcenterServerContactFailed, self).__init__(message)


class DoesNotExist(Exception):
	pass


class ApplicationLDAPObject(object):

	def __init__(self, ldap_id, lo, co):
		self._localhost = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		self._udm_obj = None
		self._ldap_id = ldap_id
		self._lo = lo
		self._co = co
		self.reload()

	def reload(self):
		result = appcenter_udm_module.lookup(self._co, self._lo, 'id=%s' % escape_filter_chars(self._ldap_id))
		if result:
			self._udm_obj = result[0]
			self._udm_obj.open()
		else:
			raise DoesNotExist()

	@classmethod
	def create(cls, app, lo, co, pos):
		# check for all containers below cn=univention if they exist
		#   if not, create!
		containers = uldap.explodeDn(app.ldap_container, 1)
		containers = containers[0:containers.index('apps')]
		base = 'cn=apps,cn=univention,%s' % ucr.get('ldap/base')
		pos.setDn(base)
		for container in reversed(containers):
			for container_obj in container_udm_module.lookup(co, lo, 'cn=%s' % escape_filter_chars(container), base=base):
				break
			else:
				container_obj = container_udm_module.object(co, lo, pos)
				container_obj.open()
				container_obj.info['name'] = container
				MODULE.process('Container %s for new univentionApp needed. Creating...' % container)
				container_obj.create()
			pos.setDn(container_obj.dn)
		base64icon = ''
		try:
			with open(os.path.join(FRONTEND_ICONS_DIR, '50x50', app.get('icon'))) as f:
				base64icon = base64.b64encode(f.read())
		except IOError:
			pass
		attrs = {
			'id': app.ldap_id,
			'name': app.get_locale_list('name'),
			'version': app.version,
			'shortDescription': app.get_locale_list('description'),
			'longDescription': app.get_locale_list('longdescription'),
			'contact': app.get('contact'),
			'maintainer': app.get('maintainer'),
			'website': app.get_locale_list('website'),
			'websiteVendor': app.get_locale_list('websitevendor'),
			'websiteMaintainer': app.get_locale_list('websitemaintainer'),
			'icon': base64icon,
			'category': app.get('unlocalised_categories'),
			'webInterface': app.get('webinterface'),
			'webInterfaceName': app.get('webinterfacename'),
			'conflictingApps': app.get('conflictedapps'),
			'conflictingSystemPackages': app.get('conflictedsystempackages'),
			'defaultPackages': app.get('defaultpackages'),
			'defaultPackagesMaster': app.get('defaultpackagesmaster'),
			'umcModuleName': app.get('umcmodulename'),
			'umcModuleFlavor': app.get('umcmoduleflavor'),
			'serverRole': app.get('serverrole'),
		}
		obj = appcenter_udm_module.object(co, lo, pos)
		try:
			obj.open()
			for property_name, value in attrs.items():
				property_obj = appcenter_udm_module.property_descriptions[property_name]
				if isinstance(value, (tuple, list)) and property_obj.multivalue:
					if not value and not property_obj.required:
						continue
					obj[property_name] = [property_obj.syntax.parse(ival) for ival in value]
				else:
					# None and empty string represents removing of the attribute (handlers/__init__.py def diff)
					if (value is None or value == '') and not property_obj.required:
						continue
					obj[property_name] = property_obj.syntax.parse(value)
			obj.create()
			MODULE.process('univentionApp %s created' % obj.dn)
		except udm_errors.objectExists:
			MODULE.info('univentionApp %s found' % obj.dn)
		return cls(app.ldap_id, lo, co)

	def add_localhost(self):
		self.reload()
		self._udm_obj.info.setdefault('server', [])
		if self._localhost not in self._udm_obj.info['server']:
			self._udm_obj.info['server'].append(self._localhost)
			MODULE.process('Adding %s to %s' % (self._localhost, self._udm_obj.dn))
			self._udm_obj.modify()

	def remove_localhost(self):
		self.reload()
		try:
			self._udm_obj.info.setdefault('server', [])
			self._udm_obj.info['server'].remove(self._localhost)
		except ValueError:
			pass
		else:
			MODULE.process('Removing %s from %s' % (self._localhost, self._udm_obj.dn))
			self._udm_obj.modify()

	def anywhere_installed(self):
		self.reload()
		return bool(self._udm_obj.info.get('server', []))

	def remove_from_directory(self):
		MODULE.process('%s: Remove because unused.' % self._udm_obj.dn)
		self._udm_obj.remove()


class InvokationRequirement(object):

	def __init__(self, *actions):
		self.name = ''
		self.actions = actions
		self.hard = None
		self.func = None

	def __call__(self, func):
		self.func = func
		self.name = func.__name__
		return self


class HardRequirement(InvokationRequirement):

	def __init__(self, *actions):
		super(HardRequirement, self).__init__(*actions)
		self.hard = True


class SoftRequirement(InvokationRequirement):

	def __init__(self, *actions):
		super(SoftRequirement, self).__init__(*actions)
		self.hard = False


class ApplicationMetaClass(type):

	def __new__(mcs, name, bases, attrs):
		requirements = {}
		for key, value in attrs.items():
			if isinstance(value, InvokationRequirement):
				attrs[key] = value.func
				for action in value.actions:
					requirements.setdefault((action, value.hard), [])
					requirements[(action, value.hard)].append(value.name)
		new_cls = super(ApplicationMetaClass, mcs).__new__(mcs, name, bases, attrs)
		new_cls._requirements = requirements
		return new_cls


class Application(object):
	__metaclass__ = ApplicationMetaClass
	_reg_comma = re.compile('\s*,\s*')
	_reg_component_id = re.compile(r'.*/(?P<id>[^/]+)\.ini')
	_all_applications = None
	_category_translations = None
	_ucs_version = None

	def __init__(self, ini_file, localize=True):
		# load config file
		self._ini_file = ini_file
		self._options = {}
		config = ConfigParser.ConfigParser()
		with open(ini_file, 'rb') as fp:
			config.readfp(fp)
		self.raw_config = config
		url = urljoin('%s/' % self.get_metainf_url(), os.path.basename(ini_file))

		self._options['ucsoverviewcategory'] = 'service'

		def _escape_value(key, value):
			if key == 'ucsoverviewcategory':
				if value == 'False':
					return ''
				elif value == 'admin':
					return 'admin'
				else:
					return 'service'
			return value

		# copy values from config file
		for k, v in config.items('Application'):
			self._options[k] = _escape_value(k, v)
		# copy original name before translating
		self._options['unlocalised_name'] = self.get('name')

		if localize:
			# overwrite english values with localized translations
			loc = locale.getlocale()[0]
			if isinstance(loc, basestring):
				if not config.has_section(loc):
					loc = loc.split('_')[0]
				if config.has_section(loc):
					for k, v in config.items(loc):
						self._options[k] = _escape_value(k, v)

		# parse boolean values
		for ikey in ('notifyvendor', 'useractivationrequired', 'useshop', 'withoutrepository', 'endoflife', 'admemberissuepassword', 'admemberissuehide'):
			if ikey in self._options:
				self._options[ikey] = config.getboolean('Application', ikey)
			else:
				self._options[ikey] = False
		self._options['docker'] = bool(self.get('dockerimage'))

		# parse int values:
		for ikey in ('minphysicalram', 'webinterfaceporthttp', 'webinterfaceporthttps'):
			if ikey in self._options:
				self._options[ikey] = config.getint('Application', ikey)
			else:
				self._options[ikey] = 0

		# parse list values
		for ikey in ('categories', 'defaultpackages', 'additionalpackagesmaster', 'additionalpackagesbackup', 'additionalpackagesslave', 'additionalpackagesmember', 'conflictedsystempackages', 'defaultpackagesmaster', 'conflictedapps', 'requiredapps', 'requiredappsindomain', 'serverrole', 'supportedarchitectures', 'portsexclusive', 'portsredirection', 'supporteducsversions'):
			ival = self.get(ikey)
			if ival:
				self._options[ikey] = self._reg_comma.split(ival)
			else:
				self._options[ikey] = []

		# copy original categories before translating
		self._options['unlocalised_categories'] = self._options['categories'][:]
		if localize:
			# localize the category names
			category_translations = self._get_category_translations()
			self._options['categories'] = [category_translations.get(icat.lower()) or icat for icat in self.get('categories')]

		# return a proper URL for local files
		for ikey in ('screenshot',):
			if self.get(ikey):
				self._options[ikey] = urljoin('%s/' % self.get_metainf_url(), self.get(ikey))

		# versions will be set to something meaningful by Application.all()
		self.versions = [self]

		# save important meta data
		self.id = self.ldap_id = self.ldap_container = None
		self.set_id(self._options['id'])
		self.name = self._options['name']
		self.code = self._options.get('code')
		self.version = self._options['version']

		# get the name of the component
		m = self._reg_component_id.match(url)
		self.component_id = 'unknown'
		if m:
			self.component_id = m.groupdict()['id']
		self.icon = self._options['icon'] = 'apps-%s.png' % self.component_id

		self._fetch_file('readme', 'README', localize)
		self._fetch_file('licenseagreement', 'LICENSE_AGREEMENT', localize)
		self._fetch_file('readmeinstall', 'README_INSTALL', localize)
		self._fetch_file('readmepostinstall', 'README_POST_INSTALL', localize)
		self._fetch_file('readmeupdate', 'README_UPDATE', localize)
		self._fetch_file('readmepostupdate', 'README_POST_UPDATE', localize)
		self._fetch_file('readmeuninstall', 'README_UNINSTALL', localize)
		self._fetch_file('readmepostuninstall', 'README_POST_UNINSTALL', localize)

	@property
	def candidate(self):
		is_installed = self.is_registered(ucr)
		this_version = LooseVersion(self.version)
		for ver in self.versions:
			other_version = LooseVersion(ver.version)
			if other_version <= this_version:
				continue
			if ver.get('dockerimage'):
				continue
			if is_installed and ver.get('requiredappversionupgrade'):
				if LooseVersion(ver.get('requiredappversionupgrade')) > this_version:
					continue
			return ver

	def set_id(self, app_id, recursive=True):
		if recursive:
			for iapp in self.versions:
				# will call also for self!
				iapp.set_id(app_id, recursive=False)
		else:
			app_id = app_id.lower()
			self.id = app_id
			self._options['id'] = app_id
			self.ldap_id = '%s_%s' % (self.id, self.get('version'))
			self.ldap_container = 'cn=%s,cn=apps,cn=univention,%s' % (self.id, ucr.get('ldap/base'))

	def get(self, key):
		'''Helper function to access configuration elements of the application's .ini
		file. If element is not given, returns (for string elements) an empty string.
		'''
		v = self._options.get(key.lower())
		if v is None:
			return ''
		return v

	def get_localised(self, key, locale='en'):
		if locale != 'en':
			try:
				return self.raw_config.get(locale, key)
			except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
				pass
		try:
			return self.raw_config.get('Application', key)
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			return ''

	def get_locale_list(self, key):
		ret = []
		for section in self.raw_config.sections():
			locale = section
			if locale == 'Application':
				locale = 'en'
			try:
				v = self.raw_config.get(section, key)
				if v:
					ret.append('[%s] %s' % (locale, v))
			except ConfigParser.NoOptionError:
				pass
		return ret

	def _fetch_file(self, key, file_ext, localize=True):
		loc = locale.getlocale()[0]
		if localize and isinstance(loc, basestring):
			loc = loc.split('_')[0].upper()
		else:
			loc = 'EN'
		for localised_file_ext in [file_ext + '_%s' % loc, file_ext, file_ext + '_EN']:
			try:
				# open the license file
				filename = os.path.join(CACHE_DIR, '%s.%s' % (self.component_id, localised_file_ext))
				with open(filename, 'rb') as fp:
					template = ''.join(fp.readlines()).strip()
					while True:
						# stolen from config_registry.handler.run_filter()
						i = UCR_VARIABLE_TOKEN.finditer(template)
						try:
							start = i.next()
							end = i.next()
							name = template[start.end():end.start()]
							value = ''
							if name in ucr:
								value = ucr[name]
								if isinstance(value, (list, tuple)):
									value = value[0]
							template = template[:start.start()] + value + template[end.end():]
						except StopIteration:
							break
					self._options[key] = template
					self._options['%s_file' % key] = filename
					return
			except IOError:
				pass

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
	def get_ucs_version(cls):
		'''Returns the current UCS version (ucr get version/version).
		During a release update of UCS, returns the target version instead
		because the new ini files should now be used in any script'''
		if cls._ucs_version is None:
			version = None
			try:
				still_running = False
				next_version = None
				status_file = '/var/lib/univention-updater/univention-updater.status'
				if os.path.exists(status_file):
					with open(status_file, 'r') as status:
						for line in status:
							line = line.strip()
							key, value = line.split('=', 1)
							if key == 'status':
								still_running = value == 'RUNNING'
							elif key == 'next_version':
								next_version = value.split('-')[0]
						if still_running and next_version:
							version = next_version
			except (IOError, ValueError) as exc:
				MODULE.warn('Could not parse univention-updater.status: %s' % exc)
			if version is None:
				version = ucr.get('version/version', '')
			MODULE.info('UCS Version is %r' % version)
			cls._ucs_version = version
		return cls._ucs_version

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
			self.get_ucs_version(),
			self.component_id,
		)

	@classmethod
	def get_metainf_url(cls):
		return '%s/meta-inf/%s' % (
			cls.get_server(with_scheme=True),
			cls.get_ucs_version(),
		)

	@classmethod
	def find(cls, application_id):
		for application in cls.all():
			if application.id == application_id:
				return application

	@classmethod
	def _get_category_translations(cls, fake=False):
		if fake:
			cls._category_translations = {}
		elif cls._category_translations is None:
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
			except (ConfigParser.Error,) as exc:
				MODULE.warn('Could not load category translations from: %s\n%s' % (url, exc))
			except (urllib2.HTTPError, urllib2.URLError) as exc:
				MODULE.warn('Could not load category translations from: %s\n%s' % (url, verbose_http_error(exc)))
			MODULE.info('loaded category translations: %s' % cls._category_translations)
		return cls._category_translations

	@classmethod
	def _extract_local_archive(cls):
		if os.listdir(CACHE_DIR):
			# we already have a cache. our archive is just outdated...
			return False
		if not os.path.exists(LOCAL_ARCHIVE):
			# for some reason the archive is not there. should only happen when deleted intentionally...
			return False
		MODULE.process('Filling the App Center file cache from our local archive!')
		try:
			archive = tarfile.open(LOCAL_ARCHIVE, 'r:*')
		except (tarfile.TarError, IOError) as e:
			MODULE.warn('Error while reading %s: %s' % (LOCAL_ARCHIVE, e))
			return
		try:
			for member in archive.getmembers():
				filename = member.name
				if os.path.sep in filename:
					# just some paranoia
					continue
				MODULE.info('Extracting %s' % filename)
				archive.extract(filename, path=CACHE_DIR)
		finally:
			cls._update_local_files()
			archive.close()
		return True

	@classmethod
	def sync_with_server(cls):
		something_changed = cls._extract_local_archive()

		index_json_gz_filename = 'index.json.gz'
		detached_sig_filename = None

		if not ucr.is_false('appcenter/index/verify'):
			detached_sig_filename = index_json_gz_filename + '.gpg'

			sig_url = urljoin('%s/' % cls.get_metainf_url(), detached_sig_filename)
			MODULE.process('Downloading "%s"...' % sig_url)
			detached_sig = urlopen(sig_url).read()
			detached_sig_path = os.path.join(CACHE_DIR, detached_sig_filename)
			with open(detached_sig_path, 'wb') as f:
				f.write(detached_sig)

		json_url = urljoin('%s/' % cls.get_metainf_url(), index_json_gz_filename)
		MODULE.process('Downloading "%s"...' % json_url)
		index_json_gz = urlopen(json_url).read()

		if detached_sig_filename:
			(rc, gpg_error) = gpg_verify("-", detached_sig_path, content=index_json_gz)
			if rc:
				message = 'Signature verification for %s failed' % (index_json_gz_filename,)
				MODULE.error(message)
				if gpg_error:
					MODULE.error(gpg_error)
				raise Exception(message)

		index_json_gz_path = os.path.join(CACHE_DIR, index_json_gz_filename)
		with open(index_json_gz_path, 'wb') as f:
			f.write(index_json_gz)

		try:
			zipped = StringIO(index_json_gz)
			content = GzipFile(mode='rb', fileobj=zipped).read()
		except (urllib2.HTTPError, urllib2.URLError) as exc:
			raise AppcenterServerContactFailed(exc)
		except:
			MODULE.error('Could not read "%s"' % json_url)
			raise
		try:
			json_apps = loads(content)
		except:
			MODULE.error('JSON malformatted: %r' % content)
			raise
		files_to_download = []
		files_in_json_file = []
		for appname, appinfo in json_apps.iteritems():
			for appfile, appfileinfo in appinfo.iteritems():
				filename = os.path.basename('%s.%s' % (appname, appfile))
				remote_md5sum = appfileinfo['md5']
				remote_url = appfileinfo['url']
				# compare with local cache
				cached_filename = os.path.join(CACHE_DIR, filename)
				files_in_json_file.append(cached_filename)
				local_md5sum = get_md5(cached_filename)
				if remote_md5sum != local_md5sum:
					# ask to re-download this file
					files_to_download.append((remote_url, filename, remote_md5sum))
					something_changed = True
		# remove those files that apparently do not exist on server anymore
		for index_filename in ('index.json.gz', 'index.json.gz.gpg'):
			files_in_json_file.append(os.path.join(CACHE_DIR, index_filename))
		for cached_filename in glob(os.path.join(CACHE_DIR, '*')):
			if os.path.isdir(cached_filename):
				continue
			if cached_filename not in files_in_json_file:
				MODULE.info('Deleting obsolete %s' % cached_filename)
				something_changed = True
				os.unlink(cached_filename)
		num_files_to_be_downloaded = len(files_to_download)
		MODULE.process('%d file(s) are new' % num_files_to_be_downloaded)
		num_files_threshold = 5
		if num_files_to_be_downloaded > num_files_threshold:
			files_to_download = cls._download_archive(files_to_download)
		threads = []
		max_threads = 10
		files_per_thread = max(num_files_threshold, int(ceil(float(len(files_to_download)) / max_threads)))
		while files_to_download:
			# normally, this should be only one thread as
			# _download_archive() is used if many files are to be downloaded
			# but if all.tar.gz fails, everything needs to be downloaded
			# don't do this at once, at this opens 100 connections.
			files_to_download_in_thread, files_to_download = files_to_download[:files_per_thread], files_to_download[files_per_thread:]
			MODULE.process('Starting to download %d file(s) directly' % len(files_to_download_in_thread))
			thread = Thread(target=cls._download_directly, args=(files_to_download_in_thread,))
			thread.start()
			threads.append(thread)
			time.sleep(0.1)  # wait 100 milliseconds so that not all threads start at the same time
		for thread in threads:
			thread.join()
		if something_changed:
			cls._update_local_files()

	@classmethod
	def _download_archive(cls, files_to_download):
		# a lot of files to download? Do not download them
		#   one at a time. Download the full archive!
		files_still_to_download = []
		archive_url = urljoin('%s/' % cls.get_metainf_url(), 'all.tar.gz')
		try:
			MODULE.process('Downloading "%s"...' % archive_url)
			# for some reason saving this in memory is flawed.
			# using StringIO and GZip objects has issues
			# with "empty" files in tar.gz archives, i.e.
			# doublets like .png logos
			with open(os.path.join(CACHE_DIR, 'all.tar.gz'), 'wb') as f:
				f.write(urlopen(archive_url).read())
			archive = tarfile.open(f.name, 'r:*')
			try:
				for filename_url, filename, remote_md5sum in files_to_download:
					MODULE.info('Extracting %s' % filename)
					try:
						archive.extract(filename, path=CACHE_DIR)
						local_md5sum = get_md5(os.path.join(CACHE_DIR, filename))
						if local_md5sum != remote_md5sum:
							MODULE.warn('Checksum for %s should be %r but was %r! Download manually' % (filename, remote_md5sum, local_md5sum))
							raise KeyError(filename)
					except KeyError:
						MODULE.warn('%s not found in archive!' % filename)
						files_still_to_download.append((filename_url, filename, remote_md5sum))
			finally:
				archive.close()
				os.unlink(f.name)
			return files_still_to_download
		except Exception as exc:
			MODULE.error('Could not read "%s": %s' % (archive_url, exc))
			return files_to_download

	@classmethod
	def _download_directly(cls, files_to_download):
		for filename_url, filename, remote_md5sum in files_to_download:
			# don't forget to quote: 'foo & bar.ini' -> 'foo%20%26%20bar.ini'
			# but don't quote https:// -> https%3A//
			path = urllib2.quote(urlsplit(filename_url).path)
			filename_url = '%s%s' % (cls.get_server(with_scheme=True), path)

			cached_filename = os.path.join(CACHE_DIR, filename)

			MODULE.info('Downloading %s to %s' % (filename_url, cached_filename))
			try:
				urlcontent = urlopen(filename_url)
			except Exception as e:
				MODULE.error('Error downloading %s: %s' % (filename_url, e))
			else:
				with open(cached_filename, 'wb') as f:
					f.write(urlcontent.read())
				local_md5sum = get_md5(cached_filename)
				if local_md5sum != remote_md5sum:
					MODULE.error('Checksum for %s should be %r but was %r! Giving up for this time!' % (filename, remote_md5sum, local_md5sum))

	@classmethod
	def _update_local_files(cls):
		# some variables could change apps.xml
		# e.g. Name, Description
		cls.update_conffiles()

		# special handling for icons
		for png in glob(os.path.join(FRONTEND_ICONS_DIR, '**', 'apps-*.png')):
			os.unlink(png)
		for png in glob(os.path.join(CACHE_DIR, '*.png')):
			app_id, ext = os.path.splitext(os.path.basename(png))
			png_50 = os.path.join(FRONTEND_ICONS_DIR, '50x50', 'apps-%s.png' % app_id)
			shutil.copy2(png, png_50)
			# images are created with UMC umask: -rw-------
			# change the mode to UCS umask:      -rw-r--r--
			os.chmod(png_50, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)

	#@classmethod
	# def set_server(cls, host=None, scheme=None):
	#	if host and scheme:
	#		new_server = '%s://%s' % (scheme, host)
	#	elif host:
	#		new_server = host
	#	elif scheme:
	#		current_server = cls.get_server(with_scheme=False)
	#		new_server = '%s://%s' % (scheme, current_server)
	#	else:
	# no-op
	#		return
	#	ucr_update(ucr, {'repository/app_center/server' : new_server})

	@classmethod
	def all_installed(cls, package_manager, force_reread=False, only_local=False, localize=True):
		ret = []
		for app in cls.all(force_reread=force_reread, only_local=only_local, localize=localize):
			if not app.has_active_ad_member_issue('hide') and app.allowed_on_local_server() and app.is_installed(package_manager, strict=False):
				ret.append(app)
		return ret

	@classmethod
	def all(cls, force_reread=False, only_local=False, localize=True):
		# reload ucr variables
		ucr.load()

		# load the first time the category translations
		cls._get_category_translations(fake=not localize)

		if force_reread:
			cls._all_applications = None
			cls._ucs_version = None

		if cls._all_applications is None:
			cls._all_applications = []
			# first of all, look for local archive
			cls._extract_local_archive()
			# query all applications from the server
			if not only_local:
				cls.sync_with_server()
			for ini_file in glob(os.path.join(CACHE_DIR, '*.ini')):
				cls._all_applications.append(Application(ini_file, localize))

		# filter function
		def _included(the_list, app):
			if the_list == '*':
				return True
			the_list = map(str.lower, cls._reg_comma.split(the_list))
			if app.id.lower() in the_list:
				return True
			if app.get('unlocalised_name').lower() in the_list:
				return True
			for category in app.get('unlocalised_categories'):
				if category.lower() in the_list:
					return True
			return False

		# filter blacklisted apps (by id, name, and category)
		filtered_applications = cls._all_applications
		blacklist = ucr.get('repository/app_center/blacklist')
		if blacklist:
			filtered_applications = [app for app in filtered_applications if not _included(blacklist, app)]

		# filter whitelisted apps (by id, name, and category)
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

			used_app = iapps[0]  # take newest one
			for iiapp in iapps:
				if iiapp.is_registered(ucr):
					if iiapp is not used_app:
						used_app = iiapp
						if used_app.candidate:
							used_app.candidate.versions = iapps
					break
			# store all versions
			used_app.versions = iapps
			final_applications.append(used_app)

		final_applications.sort(key=attrgetter('id'))
		return final_applications

	def is_registered(self, ucr):
		if self.get('withoutrepository'):
			return True
		return component_registered(self.component_id, ucr)

	def is_current(self, ucr):
		if self.get('withoutrepository'):
			return True
		return component_current(self.component_id, ucr)

	def disable_component(self, component_manager):
		if self.get('withoutrepository'):
			return
		with set_save_commit_load(component_manager.ucr) as super_ucr:
			return component_manager.uncurrentify(self.component_id, super_ucr)

	def enable_component(self, component_manager):
		if self.get('withoutrepository'):
			return
		with set_save_commit_load(component_manager.ucr) as super_ucr:
			return component_manager.currentify(self.component_id, super_ucr)

	def allowed_on_local_server(self):
		server_role = ucr.get('server/role')
		allowed_roles = self.get('serverrole')
		return not allowed_roles or server_role in allowed_roles

	def has_active_ad_member_issue(self, issue):
		return ucr.is_true('ad/member') and self.get('admemberissue%s' % issue)

	def should_show_up_in_app_center(self, package_manager, domainwide_managed=None):
		# NOT iff:
		#  * has wrong server role while not domainwide_managed OR
		#  * is not installed and has EndOfLife=True OR
		#  * has ADMemberIssueHide and UCS is part of a Windows Active Directory
		if domainwide_managed is None:
			domainwide_managed = self.domainwide_managed()
		return (domainwide_managed or self.allowed_on_local_server()) and (not self.get('endoflife') or self.is_installed(package_manager)) and not self.has_active_ad_member_issue('hide')

	@machine_connection(write=False, loarg='lo', poarg='pos')
	def get_installations(self, hosts=None, lo=None, pos=None):
		try:
			ret = {}
			try:
				app_objs = appcenter_udm_module.lookup(None, lo, None, base=self.ldap_container)
			except udm_errors.noObject:
				app_objs = []
			for app_obj in app_objs:
				# do not do it multiple times in the next loop
				app_obj.open()
			if hosts is None:
				hosts = get_all_hosts(lo)
			for computer_obj in hosts:
				role = computer_obj.info.get('serverRole')[0]
				description = computer_obj.info.get('description')
				ip = computer_obj.info.get('ip')  # list
				version = None
				candidate_version = self.version
				if self.candidate:
					candidate_version = self.candidate.version
				for app_obj in app_objs:
					if computer_obj.info.get('fqdn') in app_obj.info.get('server', []):
						version = app_obj.info.get('version')
						break
				ret[computer_obj['name']] = {
					'version': version,
					'candidate_version': candidate_version,
					'description': description,
					'ip': ip,
					'role': role,
				}
			return ret
		finally:
			del lo

	@classmethod
	def domainwide_managed(self, hosts=None):
		ret = ucr.is_true('appcenter/domainwide')
		if ret:
			if hosts is None:
				hosts = get_all_hosts()
			ret = len(hosts) > 1
		return ret

	@reloading_ucr(ucr)
	def to_dict(self, package_manager, domainwide_managed=None, hosts=None):
		res = copy.copy(self._options)
		res['component_id'] = self.component_id

		if domainwide_managed is None:
			domainwide_managed = self.domainwide_managed(hosts)
		if domainwide_managed:
			res['installations'] = self.get_installations(hosts)
		else:
			res['installations'] = None
		res['is_installed'] = self.is_installed(package_manager)
		res['is_current'] = self.is_current(ucr)
		res['is_joined'] = os.path.exists('/var/univention-join/joined')
		res['is_master'] = ucr.get('server/role') == 'domaincontroller_master'
		res['local_role'] = ucr.get('server/role')
		res['host_master'] = ucr.get('ldap/master')
		res['umc_module'] = 'apps'
		res['umc_flavor'] = self.id
		ldap_object = self.get_ldap_object()
		if ldap_object is None:
			res['is_installed_anywhere'] = False
		else:
			res['is_installed_anywhere'] = ldap_object.anywhere_installed()
		if self.candidate:
			# too expensive
			# res['candidate'] = self.candidate.to_dict(package_manager)
			res['candidate_version'] = self.candidate.version
			res['candidate_component_id'] = self.candidate.component_id
			res['candidate_readmeupdate'] = self.candidate.get('readmeupdate')
			res['candidate_readmepostupdate'] = self.candidate.get('readmepostupdate')
		res['fully_loaded'] = True
		return res

	def __repr__(self):
		return '<Application id="%s" name="%s (%s)" code="%s" component="%s">' % (self.id, self.name, self.version, self.code, self.component_id)

	@HardRequirement('install', 'update')
	def must_have_fitting_ucs_version(self):
		required_ucs_version = None
		for supported_version in self.get('supporteducsversions'):
			if supported_version.startswith('%s-' % ucr.get('version/version')):
				required_ucs_version = supported_version
				break
		else:
			required_ucs_version = self.get('requireducsversion')
			if not required_ucs_version:
				return True
		major, minor = ucr.get('version/version').split('.', 1)
		patchlevel = ucr.get('version/patchlevel')
		errata = ucr.get('version/erratalevel')
		version_bits = re.match(r'^(\d+)\.(\d+)-(\d+)(?: errata(\d+))?$', required_ucs_version).groups()
		comparisons = zip(version_bits, [major, minor, patchlevel, errata])
		for required, present in comparisons:
			if int(required or 0) > int(present):
				return {'required_version': required_ucs_version}
			if int(required or 0) < int(present):
				return True
		return True

	@HardRequirement('install', 'update')
	def must_not_be_docker_in_docker(self):
		return not self.get('docker') or not container_mode()

	@HardRequirement('install', 'update')
	def must_have_valid_license(self):
		return LICENSE.allows_using(self.get('notifyvendor'))

	@HardRequirement('install')
	def must_not_be_installed(self, package_manager):
		return not self.is_installed(package_manager)

	@HardRequirement('install')
	def must_not_be_end_of_life(self):
		return not self.get('endoflife')

	@HardRequirement('install', 'update')
	def must_have_supported_architecture(self):
		supported_architectures = self.get('supportedarchitectures')
		platform_bits = platform.architecture()[0]
		aliases = {'i386': '32bit', 'amd64': '64bit'}
		if supported_architectures:
			for architecture in supported_architectures:
				if aliases[architecture] == platform_bits:
					break
			else:
				# For now only two architectures are supported:
				#   32bit and 64bit - and this will probably not change
				#   too soon.
				# So instead of returning lists and whatnot
				#   just return a nice message
				# Needs to be adapted when supporting different archs
				supported = supported_architectures[0]
				if supported == 'i386':
					needs = 32
					has = 64
				else:
					needs = 64
					has = 32
				msg = _('The application needs a %(needs)s-bit operating system. This server is running a %(has)s-bit operating system.') % {'needs': needs, 'has': has}
				return {'supported': supported, 'msg': msg}
		return True

	@HardRequirement('install', 'update')
	def must_be_joined_if_master_packages(self):
		is_joined = os.path.exists('/var/univention-join/joined')
		return bool(is_joined or not self.get('defaultpackagesmaster'))

	@HardRequirement('install', 'update', 'uninstall')
	def must_not_have_concurrent_operation(self, package_manager):
		return package_manager.progress_state._finished  # TODO: package_manager.is_finished()

	@HardRequirement('install', 'update')
	def must_have_correct_server_role(self):
		server_role = ucr.get('server/role')
		if not self.allowed_on_local_server():
			return {
				'current_role': server_role,
				'allowed_roles': ', '.join(self.get('serverrole')),
			}
		return True

	@HardRequirement('install', 'update')
	def must_have_no_conflicts_packages(self, package_manager):
		conflict_packages = []
		for pkgname in self.get('conflictedsystempackages'):
			if package_manager.is_installed(pkgname):
				conflict_packages.append(pkgname)
		if conflict_packages:
			return conflict_packages
		return True

	@HardRequirement('install', 'update')
	def must_have_no_conflicts_apps(self, package_manager):
		conflictedapps = set()
		# check ConflictedApps
		for app in self.all():
			if not app.allowed_on_local_server():
				# cannot be installed, continue
				continue
			if app.id in self.get('conflictedapps') or self.id in app.get('conflictedapps'):
				if app.is_installed(package_manager):
					conflictedapps.add(app.id)
		# check port conflicts
		ports = []
		for i in self.get('portsexclusive'):
			ports.append(i)
		for i in self.get('portsredirection'):
			ports.append(i.split(':', 1)[0])
		for app_id, container_port, host_port in app_ports():
			if app_id != self.id and str(host_port) in ports:
				conflictedapps.add(app_id)
		if conflictedapps:
			conflictedapps = [self.find(app_id) for app_id in conflictedapps]
			return [{'id': app.id, 'name': app.name} for app in conflictedapps if app]
		return True

	@HardRequirement('install', 'update')
	def must_have_no_unmet_dependencies(self, package_manager):
		unmet_packages = []

		# RequiredApps
		for app in self.all():
			if app.id in self.get('requiredapps'):
				if not app.is_installed(package_manager):
					unmet_packages.append({'id': app.id, 'name': app.name, 'in_domain': False})

		# Plugin
		if self.get('plugin_of'):
			app = Application.find(self.get('plugin_of'))
			if not app.is_installed(package_manager):
				unmet_packages.append({'id': app.id, 'name': app.name, 'in_domain': False})

		# RequiredAppsInDomain
		apps = [Application.find(app_id) for app_id in self.get('requiredappsindomain')]
		for app in apps:
			if not app:
				continue
			app = app.to_dict(package_manager, domainwide_managed=True)
			if not app['is_installed_anywhere']:
				local_allowed = app['id'] not in self.get('conflictedapps')
				unmet_packages.append({'id': app['id'], 'name': app['name'], 'in_domain': True, 'local_allowed': local_allowed})

		if unmet_packages:
			return unmet_packages
		return True

	@HardRequirement('uninstall')
	def must_not_be_depended_on(self, package_manager):
		depending_apps = []

		# RequiredApps
		for app in self.all():
			if self.id in app.get('requiredapps') and app.is_installed(package_manager):
				depending_apps.append({'id': app.id, 'name': app.name})

		# Plugin
		if not self.get('docker'):
			for app in Application.all():
				if self.id == app.get('plugin_of'):
					depending_apps.append({'id': app.id, 'name': app.name})

		# RequiredAppsInDomain
		apps = [app for app in Application.all() if self.id in app.get('requiredappsindomain')]
		if apps:
			ldap_object = self.get_ldap_object()
			if ldap_object and ldap_object._udm_obj and len(ldap_object._udm_obj.info.get('server', [])) <= 1:
				for app in apps:
					app = app.to_dict(package_manager, domainwide_managed=True)
					if app['is_installed_anywhere']:
						depending_apps.append({'id': app['id'], 'name': app['name']})

		if depending_apps:
			return depending_apps
		return True

	@SoftRequirement('install')
	def shall_have_enough_free_disk_space(self, function):
		'''The application requires %(minimum)d MB of free disk space but only
		%(current)d MB are available.'''
		if not self.docker:
			return True
		current_free_disk_space = get_free_disk_space()
		required_free_disk_space = self.min_free_disk_space
		if current_free_disk_space and current_free_disk_space < required_free_disk_space:
			return {'minimum': required_free_disk_space, 'current': current_free_disk_space}
		return True

	@SoftRequirement('install', 'update')
	def shall_have_enough_ram(self, function):
		current_ram = get_current_ram_available()
		required_ram = self.get('minphysicalram')
		if function == 'update':
			# is already installed, just a minor version update
			#   RAM "used" by this installed app should count
			#   as free. best approach: subtract it
			installed_app = self.find(self.id)
			old_required_ram = installed_app.get('minphysicalram')
			required_ram = required_ram - old_required_ram
		if current_ram < required_ram:
			return {'minimum': required_ram, 'current': current_ram}
		return True

	@SoftRequirement('install', 'update')
	def shall_only_be_installed_in_ad_env_with_password_service(self):
		return not self.has_active_ad_member_issue('password')

	def check_invokation(self, function, package_manager):
		def _check(hard_requirements):
			ret = {}
			for func_name in self._requirements.get((function, hard_requirements), []):
				possible_variables = {
					'package_manager': package_manager,
					'function': function,
				}
				if function == 'update' and hard_requirements:
					app = self.candidate
					if app is None:
						# update is not possible,
						#   special handling
						ret['must_have_candidate'] = False
						continue
				else:
					app = self
				method = getattr(app, func_name)
				arguments = inspect.getargspec(method).args[1:]  # remove self
				kwargs = dict((key, value) for key, value in possible_variables.iteritems() if key in arguments)
				reason = method(**kwargs)
				if reason is not True:
					ret[func_name] = reason
			return ret
		return _check(True), _check(False)

	def get_packages(self, additional=True):
		packages = []
		packages.extend(self.get('defaultpackages'))
		if additional:
			role = ucr.get('server/role')
			if role == 'domaincontroller_master':
				packages.extend(self.get('additionalpackagesmaster'))
			elif role == 'domaincontroller_backup':
				packages.extend(self.get('additionalpackagesbackup'))
			elif role == 'domaincontroller_slave':
				packages.extend(self.get('additionalpackagesslave'))
			elif role == 'memberserver':
				packages.extend(self.get('additionalpackagesmember'))
		return packages

	def is_installed(self, package_manager, strict=True):
		if self.get('dockerimage') and not container_mode():
			return ucr.get('appcenter/apps/%s/status' % self.id) in ['installed', 'stalled'] and ucr.get('appcenter/apps/%s/version' % self.id) == self.version
		default_packages = self.get_packages()
		if strict:
			return all(package_manager.is_installed(package) for package in default_packages)
		else:
			# app.is_installed(package_manager, strict=True) uses
			# apt_pkg.CURSTATE. Not desired when called during
			# installation of umc-module-appcenter together with
			# several other (app relevant) packages; for example
			# in postinst or joinscript (on master).
			# see Bug #33535 and Bug #31261
			for package_name in default_packages:
				try:
					package = package_manager.get_package(package_name, raise_key_error=True)
				except KeyError:
					return False
				else:
					if not package.is_installed:
						return False
			return True

	def uninstall(self, package_manager, component_manager, username=None, password=None):
		# reload ucr variables
		ucr.load()

		try:
			# remove all packages of the component
			package_manager.set_max_steps(200)
			package_manager.commit(remove=self.get_packages(additional=False))
			package_manager.add_hundred_percent()

			# remove all dependencies
			package_manager.autoremove()
			package_manager.add_hundred_percent()

			# remove all existing component versions
			self.unregister_all_and_register(None, component_manager, package_manager)

			# unregister app in LDAP
			self.tell_ldap(component_manager.ucr, package_manager)

			register = get_action('register')
			app = Apps().find(self.id, self.version)
			if app:
				register.call_safe(apps=[app], do_it=False)
				ucr_save({'appcenter/prudence/docker/%s' % app.id: 'yes'})
			status = 200
		except:
			status = 500
		self._finished('uninstall', status, component_manager.ucr, package_manager, username, password)
		return status == 200

	def install_dry_run(self, package_manager, component_manager, remove_component=True, username=None, password=None, only_master_packages=False, dont_remote_install=False, function='install', force=False, this_version=False):
		if not this_version and self.candidate:
			return self.candidate.install_dry_run(package_manager, component_manager, remove_component, username, password, only_master_packages, dont_remote_install, function, force, True)
		MODULE.info('Invoke install_dry_run')
		ucr.load()
		server_role = ucr.get('server/role')
		is_install = True
		if function.startswith('update'):
			is_install = False
			remote_function = 'update-schema'
		else:
			remote_function = 'install-schema'

		master_packages = self.get('defaultpackagesmaster')

		# connect to master/backups
		unreachable = []
		hosts_info = {}
		remote_info = {
			'master_unreachable': False,
			'problems_with_hosts': False,
			'serious_problems_with_hosts': False,
		}
		dry_run_threads = []
		if master_packages and not dont_remote_install:
			is_master = server_role == 'domaincontroller_master'
			hosts = self.find_all_hosts(is_master=is_master)
			# checking remote host is I/O heavy, so use threads
			#   "global" variables: unreachable, hosts_info, remote_info

			def _check_remote_host(application_id, host, host_is_master, username, password, force, remote_function):
				MODULE.process('Starting dry_run for %s on %s' % (application_id, host))
				try:
					client = Client(host, username, password)
				except (ConnectionError, HTTPError) as exc:
					MODULE.warn('_check_remote_host: %s: %s' % (host, exc))
					unreachable.append(host)
					if host_is_master:
						remote_info['master_unreachable'] = True
				else:
					host_info = {}
					try:
						host_version = client.umc_command('appcenter/version').result
					except Forbidden:
						# command is not yet known (older app center)
						host_version = None
					except (ConnectionError, HTTPError) as exc:
						MODULE.warn('Could not get appcenter/version: %s' % (exc,))
						raise
					host_info['compatible_version'] = Application.compatible_version(host_version)
					try:
						host_info['result'] = client.umc_command('appcenter/invoke_dry_run', {
							'function': remote_function,
							'application': application_id,
							'force': force,
							'dont_remote_install': True,
						}).result
					except Forbidden:
						# command is not yet known (older app center)
						host_info['result'] = {'can_continue': False, 'serious_problems': False}
					except (ConnectionError, HTTPError) as exc:
						MODULE.warn('Could not get appcenter/version: %s' % (exc,))
						raise
					if not host_info['compatible_version'] or not host_info['result']['can_continue']:
						remote_info['problems_with_hosts'] = True
						if host_info['result']['serious_problems'] or not host_info['compatible_version']:
							remote_info['serious_problems_with_hosts'] = True
					hosts_info[host] = host_info
				MODULE.process('Finished dry_run for %s on %s' % (application_id, host))

			for host, host_is_master in hosts:
				thread = Thread(target=_check_remote_host, args=(self.id, host, host_is_master, username, password, force, remote_function))
				thread.start()
				dry_run_threads.append(thread)

		result = {}
		# checking localhost is I/O heavy, so use threads
		#   "global" variables: result

		def _check_local_host(app, only_master_packages, server_role, master_packages, component_manager, package_manager, remove_component, previously_registered_list):
			MODULE.process('Starting dry_run for %s on %s' % (app.id, 'localhost'))
			# packages to install
			to_install = []
			if not only_master_packages:
				to_install.extend(app.get_packages())
			MODULE.info('defaultpackages: %s' % (to_install, ))
			if server_role in ('domaincontroller_master', 'domaincontroller_backup', ):
				MODULE.info('Running on DC master or DC backup')
				if master_packages:
					to_install.extend(master_packages)

			# add the new component
			previously_registered = app.register(component_manager, package_manager)
			previously_registered_list.append(previously_registered)  # HACK it into a list so that it is accessible after the thread ends

			# get package objects
			to_install_pkgs = package_manager.get_packages(to_install)

			# determine the changes
			# also check for changes from dist-upgrade (as it will
			#   be performed when upgrading - NOT when installing!).
			#   dry_run will throw away changes marked by upgrade
			if not is_install:
				package_manager.cache.upgrade(dist_upgrade=True)
			package_changes = package_manager.mark(to_install_pkgs, [], dry_run=True)
			result.update(dict(zip(['install', 'remove', 'broken'], package_changes)))
			for to_inst in to_install:
				for to_install_pkg in to_install_pkgs:
					if to_inst == to_install_pkg.name:
						break
				else:
					result['broken'].append(to_inst)

			if remove_component:
				# remove the newly added component
				MODULE.info('Remove component: %s' % (app.component_id, ))
				app.unregister_all_and_register(previously_registered, component_manager, package_manager)
			MODULE.process('Finished dry_run for %s on %s' % (app.id, 'localhost'))

		previously_registered = False
		previously_registered_list = []  # HACKY: thread shall "return" previously_registered
		thread = Thread(target=_check_local_host, args=(self, only_master_packages, server_role, master_packages, component_manager, package_manager, remove_component, previously_registered_list))
		thread.start()
		dry_run_threads.append(thread)
		for thread in dry_run_threads:
			thread.join()
		if previously_registered_list:
			previously_registered = previously_registered_list[0]

		result['unreachable'] = unreachable
		result['hosts_info'] = hosts_info
		result.update(remote_info)
		return result, previously_registered

	@machine_connection(write=True)
	def get_ldap_object(self, ldap_id=None, or_create=False, ldap_connection=None, ldap_position=None):
		if ldap_id is None:
			ldap_id = self.ldap_id
		if ldap_connection is None:
			return
		co = None
		try:
			return ApplicationLDAPObject(ldap_id, ldap_connection, co)
		except DoesNotExist:
			if or_create:
				return ApplicationLDAPObject.create(self, ldap_connection, co, ldap_position)
			return None

	def set_ucs_overview_ucr_variables(self, super_ucr, unset=False):
		ucsoverviewcategory = self.get('ucsoverviewcategory')
		webinterface = self.get('webinterface')
		port_http = self.get('webinterfaceporthttp') or ''  # '' deletes
		port_https = self.get('webinterfaceporthttps') or ''
		if ucsoverviewcategory and webinterface:
			registry_key = 'ucs/web/overview/entries/%s/%s/%%s' % (ucsoverviewcategory, self.id)
			variables = {
				'icon': '/univention-management-console/js/dijit/themes/umc/icons/50x50/%s' % self.get('icon'),
				'port_http': str(port_http),
				'port_https': str(port_https),
				'label': self.get_localised('name'),
				'label/de': self.get_localised('name', 'de'),
				'description': self.get_localised('description'),
				'description/de': self.get_localised('description', 'de'),
				'link': webinterface,
			}
			for key, value in variables.iteritems():
				if unset:
					value = ''
				super_ucr.set_registry_var(registry_key % key, value)

	def register(self, component_manager, package_manager, tell_ldap=False):
		'''Registers the component of the app in UCR and unregisters
		all other versions in one operation ("atomic"). Does an apt-get
		update if necessary.
		Returns the latest previously registered version of this app if
		there was one.
		tell_ldap does nothing!
		'''
		return self.unregister_all_and_register(self, component_manager, package_manager, tell_ldap=tell_ldap)

	def unregister(self, component_manager, super_ucr=None, tell_ldap=False):
		'''Removes its component from UCR.
		Returns whether this has been necessary (i.e. False if it was
		not registered)
		tell_ldap does nothing!
		'''
		got_unregistered = False
		if not self.get('withoutrepository') and self.is_registered(component_manager.ucr):
			component_manager.remove_app(self, super_ucr)
			got_unregistered = True
		return got_unregistered

	def unregister_all_and_register(self, to_be_registered, component_manager, package_manager, tell_ldap=False):
		'''Removes all versions of this app and registers
		`to_be_registered` if given (may be None). Does an apt-get
		update if necessary.
		Returns the latest previously registered version of this app if
		there was one.
		tell_ldap does nothing!
		'''
		should_update = False
		previously_registered = None
		with set_save_commit_load(component_manager.ucr) as super_ucr:
			other_versions = self.find(self.id).versions
			for app in reversed(other_versions):
				# remove all existing component versions,
				#   walk in reversed order so that
				#   previously_registered will be the latest if
				#   there are multiple already registered
				if app is not to_be_registered:  # don't remove the one we want to register (may be already added)
					app.set_ucs_overview_ucr_variables(super_ucr, unset=True)
					if app.unregister(component_manager, super_ucr):
						# this app actually was registered!
						previously_registered = app
						should_update = True
				elif app.is_registered(component_manager.ucr):
					# this app is to_be_registered!
					# no need to unregister, but should be returned if registered!
					previously_registered = app
			if to_be_registered:
				to_be_registered.set_ucs_overview_ucr_variables(super_ucr)
				if not to_be_registered.is_current(component_manager.ucr):  # does not hold for withoutrepository
					# add the new repository component for the app
					component_manager.put_app(to_be_registered, super_ucr)
					should_update = True
		if should_update:
			# component was added or removed. apt-get update
			package_manager.update()
		else:
			package_manager.reopen_cache()
		return previously_registered

	def tell_ldap(self, ucr, package_manager, inform_about_error=True):
		''' Registers localhost at the appcenter/app UDM object with
		the correct version. Creates that object if necessary. Also
		unregisters localhost on all other UDM objects related to this
		app. Removes them if they are useless afterwards.
		'''
		try:
			lo, pos = get_machine_connection(write=True)
			if lo is None:
				raise LDAPError()
			installed_version = None
			versions = self.find(self.id).versions
			co = None
			localhost = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
			for iapp in versions:
				if iapp.is_registered(ucr) and iapp.is_installed(package_manager, strict=False) and iapp.allowed_on_local_server():
					installed_version = iapp.version
					ldap_object = iapp.get_ldap_object(or_create=True)
					ldap_object.add_localhost()
					break
			same_app_filter = '(&(id=%s_*)(server=%s))' % (escape_filter_chars(self.id), escape_filter_chars(localhost))
			udm_objects = appcenter_udm_module.lookup(co, lo, same_app_filter)
			for udm_object in udm_objects:
				udm_object.open()
				if installed_version != udm_object.info['version']:
					ldap_object = self.get_ldap_object(udm_object.info['id'])
					if ldap_object:
						ldap_object.remove_localhost()
						if not ldap_object.anywhere_installed():
							ldap_object.remove_from_directory()

		except (LDAPError, udm_errors.base) as e:
			MODULE.error('Registering LDAP object failed. %s' % e)
			if inform_about_error:
				package_manager.progress_state.error(_('Registration of the application in LDAP failed. It will be retried every time the App Center module is opened.'))
			raise

	def uninstall_dry_run(self, package_manager):
		MODULE.info('Invoke uninstall_dry_run')
		package_manager.reopen_cache()
		to_uninstall = package_manager.get_packages(self.get_packages(additional=False))
		for package in to_uninstall:
			package.mark_delete()
		packages = [pkg.name for pkg in package_manager.packages() if pkg.is_auto_removable or pkg.marked_delete]
		package_manager.reopen_cache()
		return packages

	@classmethod
	def _query_remote_progress(cls, client, package_manager):
		all_errors = set()
		number_failures = 0
		number_failures_max = 20
		host = client.hostname
		while True:
			try:
				result = client.umc_command('appcenter/progress').result
			except (ConnectionError, HTTPError) as exc:
				MODULE.warn('%s: appcenter/progress returned an error: %s' % (host, exc))
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
				package_manager.progress_state.info(info)
			if steps:
				steps = float(steps)  # bug in package_manager in 3.1-0: int will result in 0 because of division and steps < max_steps
				package_manager.progress_state.percentage(steps)
			for error in errors:
				if error not in all_errors:
					package_manager.progress_state.error(error)
					all_errors.add(error)
			if result['finished'] is True:
				break
			time.sleep(0.1)
		return all_errors

	def install_master_packages_on_host(self, package_manager, function, host, username, password):
		if function == 'update':
			function = 'update-schema'
		else:
			function = 'install-schema'
		client = Client(host, username, password)
		result = client.umc_command('appcenter/invoke', {'function': function, 'application': self.id, 'force': True, 'dont_remote_install': True}).result
		if result['can_continue']:
			all_errors = self._query_remote_progress(client, package_manager)
			return len(all_errors) == 0
		else:
			MODULE.warn('%r' % result)
			return False

	@machine_connection(write=False, loarg='lo', poarg='pos')
	def find_all_hosts(self, is_master, lo=None, pos=None):
		hosts = []
		if not is_master:
			hosts.append((get_master(lo), True))
		# use ucr to not find oneself!
		hosts.extend([(host, False) for host in get_all_backups(lo, ucr)])
		return hosts

	def install_master_packages_on_hosts(self, package_manager, remote_function, username, password, is_master, hosts=None):
		master_packages = self.get('defaultpackagesmaster')
		if hosts is None:
			hosts = self.find_all_hosts(is_master=is_master)
		all_hosts_count = len(hosts)
		package_manager.set_max_steps(all_hosts_count * 200)  # up to 50% if all hosts are installed
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
					raise  # only if host_is_master!
			finally:
				package_manager.add_hundred_percent()

	def install(self, package_manager, component_manager, add_component=True, send_as='install', username=None, password=None, only_master_packages=False, dont_remote_install=False, previously_registered_by_dry_run=False, this_version=False):
		if not this_version and self.candidate:
			return self.candidate.install(package_manager, component_manager, add_component, send_as, username, password, only_master_packages, dont_remote_install, previously_registered_by_dry_run, True)
		if self.get('dockerimage'):
			MODULE.error('Cannot install a Docker app. Use "univention-app install" or a newer version of the UMC module App Center')
			return False
		raised_before_installed = True
		something_went_wrong_with_ldap = False
		previously_registered = None
		try:
			remote_function = send_as
			is_install = True
			if remote_function.startswith('update'):
				is_install = False
				remote_function = 'update'
			if remote_function.startswith('install'):
				remote_function = 'install'
			ucr.load()
			is_master = ucr.get('server/role') == 'domaincontroller_master'
			is_backup = ucr.get('server/role') == 'domaincontroller_backup'
			to_install = []
			if not only_master_packages:
				to_install.extend(self.get_packages())
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

			hosts = None
			if master_packages:
				if is_master:
					hosts = self.find_all_hosts(is_master=True)
					if len(hosts):
						# real installation is 50%
						#   if there are any backups. otherwise use 100%
						package_manager.set_max_steps(200)
				else:
					# real installation is 50%
					package_manager.set_max_steps(200)
					# already have installed 50%
					package_manager.progress_state._start_steps = 100  # TODO: set_max_steps should reset _start_steps. need function like set_start_steps()

			previously_registered = self.register(component_manager, package_manager)
			if previously_registered_by_dry_run is not False:
				# dry_run may have registered self and it was left there for performance reasons.
				# so that self.register() returned self, although at the beginning of
				#   self.install_dry_run(remove_component=False); self.install()
				# there was something else registered, maybe even None
				previously_registered = previously_registered_by_dry_run

			# install (+ dist_upgrade if update)
			package_manager.commit(install=to_install, dist_upgrade=not is_install)

			# from now on better don't remove component
			raised_before_installed = False

			if only_master_packages:
				# do not leave the component registered. might cause troubles
				# when updating to a new UCS version. See Bug #33947
				self.unregister_all_and_register(previously_registered, component_manager, package_manager)

			if master_packages and is_master:
				if username is None or dont_remote_install:
					MODULE.warn('Not connecting to DC Backups. Has to be done manually')
				else:
					self.install_master_packages_on_hosts(package_manager, remote_function, username, password, is_master=True, hosts=hosts)

			try:
				self.tell_ldap(component_manager.ucr, package_manager)
			except (LDAPError, udm_errors.base):
				something_went_wrong_with_ldap = True
				raise

			# successful installation
			if not only_master_packages:
				register = get_action('register')
				app = Apps().find(self.id, self.version)
				if app:
					register.call_safe(apps=[app], do_it=True)
				ucr_save({'appcenter/prudence/docker/%s' % app.id: 'yes'})
			status = 200
		except:
			MODULE.warn(traceback.format_exc())
			if raised_before_installed:
				self.unregister_all_and_register(previously_registered, component_manager, package_manager)
			try:
				self.tell_ldap(component_manager.ucr, package_manager, inform_about_error=not something_went_wrong_with_ldap)
			except (LDAPError, udm_errors.base):
				pass
			status = 500
		self._finished(send_as, status, component_manager.ucr, package_manager, username, password)
		return status == 200

	def _finished(self, action, status, ucr, package_manager, username, password):
		self._set_ucr_codes_variable(ucr, package_manager)
		self._run_joinscripts(package_manager, username, password, ucr)
		self._send_information(action, status)

	def _run_joinscripts(self, package_manager, username, password, ucr):
		with NamedTemporaryFile() as pwd_file:
			args = ['/usr/sbin/univention-run-join-scripts']
			MODULE.process('Running join scripts')
			if ucr.get('server/role') != 'domaincontroller_master':
				if username is not None and password is not None:
					args.extend(['-dcaccount', username])
					pwd_file.write(password)
					pwd_file.flush()
					args.extend(['-dcpwd', pwd_file.name])
				else:
					MODULE.process('Cannot run them without credentials')
					return
			run_join_scripts = Thread(target=subprocess.call, args=[args])
			run_join_scripts.start()
			while run_join_scripts.is_alive():
				# i did not find anything nearly as efficient as this one
				# open().readlines() works, but not very good for big log files
				# working with f.seek() is a hassle
				try:
					line = subprocess.check_output(['tail', '-n', '1', '/var/log/univention/join.log']).strip()
				except subprocess.CalledProcessError as exc:
					MODULE.warn('Watching join.log failed: %s' % exc)
				else:
					if line:
						package_manager.progress_state.info(line)
				time.sleep(1)
			run_join_scripts.join()

	def _get_new_lib_app(self):
		return AppCache().find_by_component_id(self.component_id)

	def _send_information(self, action, status):
		app = self._get_new_lib_app()
		send_information(action, app=app, status=status)

	@classmethod
	def _set_ucr_codes_variable(cls, ucr, package_manager):
		register = get_action('register')()
		register._register_installed_apps_in_ucr()

	@classmethod
	def update_conffiles(cls):
		update = get_action('update')()
		update._update_conffiles()
