#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  module for storing Apps in a cache
#
# Copyright 2017-2019 Univention GmbH
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


import sys
import os
import os.path
from contextlib import contextmanager
from time import sleep
from glob import glob
from json import dump, load
from urlparse import urlsplit
from distutils.version import LooseVersion
from ConfigParser import NoSectionError

from univention.appcenter.app import App
from univention.appcenter.log import get_base_logger
from univention.appcenter.utils import mkdir, get_locale
from univention.appcenter.ini_parser import read_ini_file, IniSectionListAttribute, IniSectionAttribute, IniSectionObject
from univention.appcenter.ucr import ucr_load, ucr_get, ucr_is_true


CACHE_DIR = '/var/cache/univention-appcenter'

cache_logger = get_base_logger().getChild('cache')


def _cmp_mtimes(mtime1, mtime2):
	if mtime1 is None or mtime2 is None:
		return cmp(mtime1, mtime2)
	return cmp(float('{:.3f}'.format(mtime1)), float('{:.3f}'.format(mtime2)))


class _AppCache(object):
	def get_every_single_app(self):
		raise NotImplementedError()

	def get_all_apps_with_id(self, app_id):
		ret = []
		for app in self.get_every_single_app():
			if app.id == app_id:
				ret.append(app)
		return ret

	def get_all_locally_installed_apps(self):
		ret = []
		for app in self.get_every_single_app():
			if app.is_installed():
				ret.append(app)
		return ret

	def find(self, app_id, app_version=None, latest=False):
		apps = self.get_all_apps_with_id(app_id)
		if app_version:
			for app in apps:
				if app.version == app_version:
					return app
			return None
		elif not latest:
			for app in apps:
				if app.is_installed():
					return app
		if apps:
			latest_app = sorted(apps)[-1]
			for app in apps:
				if app == latest_app:
					return app

	def find_candidate(self, app, prevent_docker=None):
		if prevent_docker is None:
			prevent_docker = ucr_is_true('appcenter/prudence/docker/%s' % app.id)
		if app.docker:
			prevent_docker = False
		app_version = LooseVersion(app.version)
		apps = list(reversed(self.get_all_apps_with_id(app.id)))
		not_permitted_app = None
		for _app in apps:
			if prevent_docker and _app.docker and not (_app.docker_migration_works or _app.docker_migration_link):
				continue
			if _app <= app:
				continue
			if _app.required_app_version_upgrade:
				if LooseVersion(_app.required_app_version_upgrade) > app_version:
					continue
			if not _app.install_permissions_exist():
				# do not consider app without permission...
				# ... until it is the only one (and then fail eventually...)
				if not_permitted_app is None:
					not_permitted_app = _app
				continue
			return _app
		if not_permitted_app:
			return not_permitted_app

	def get_all_apps(self):
		apps = {}
		for app in self.get_every_single_app():
			if app.id in apps:
				old_app, old_is_installed = apps[app.id]
				if not old_is_installed:
					if old_app < app:
						apps[app.id] = (app, app.is_installed())
					elif app.is_installed():
						apps[app.id] = (app, True)
			else:
				apps[app.id] = (app, app.is_installed())
		return sorted(app for (app, is_installed) in apps.itervalues())

	def find_by_component_id(self, component_id):
		for app in self.get_every_single_app():
			if app.component_id == component_id:
				return app


class AppCache(_AppCache):
	_app_cache_cache = {}

	def __init__(self, app_class=None, ucs_version=None, server=None, locale=None, cache_dir=None):
		self._app_class = app_class
		self._ucs_version = ucs_version
		if server and not server.startswith('http'):
			server = 'https://%s' % server
		self._server = server
		self._locale = locale
		self._cache_dir = cache_dir
		self._cache_file = None
		self._cache = []
		self._cache_modified_mtime = None
		self._lock = False

	def copy(self, app_class=None, ucs_version=None, server=None, locale=None, cache_dir=None):
		if app_class is None:
			app_class = self._app_class
		if ucs_version is None:
			ucs_version = self._ucs_version
		if server is None:
			server = self._server
		if locale is None:
			locale = self._locale
		if cache_dir is None:
			cache_dir = self._cache_dir
		return self.build(app_class=app_class, ucs_version=ucs_version, server=server, locale=locale, cache_dir=cache_dir)

	def get_server(self):
		if self._server is None:
			self._server = default_server()
		return self._server

	def get_server_netloc(self):
		return urlsplit(self.get_server()).netloc

	def get_ucs_version(self):
		if self._ucs_version is None:
			self._ucs_version = default_ucs_version()
		return self._ucs_version

	def get_locale(self):
		if self._locale is None:
			self._locale = default_locale()
		return self._locale

	def get_cache_dir(self):
		if self._cache_dir is None:
			server = self.get_server_netloc()
			self._cache_dir = os.path.join(CACHE_DIR, server, self.get_ucs_version())
			mkdir(self._cache_dir)
		return self._cache_dir

	def get_cache_file(self):
		if self._cache_file is None:
			cache_dir = self.get_cache_dir()
			locale = self.get_locale()
			self._cache_file = os.path.join(cache_dir, '.apps.%s.json' % locale)
		return self._cache_file

	@classmethod
	def build(cls, app_class=None, ucs_version=None, server=None, locale=None, cache_dir=None):
		obj = cls(app_class, ucs_version, server, locale, cache_dir)
		key = cls, obj.get_app_class(), obj.get_ucs_version(), obj.get_server(), obj.get_locale(), obj.get_cache_file()
		if key not in cls._app_cache_cache:
			cls._app_cache_cache[key] = obj
		return cls._app_cache_cache[key]

	def get_appcenter_cache_obj(self):
		return AppCenterCache.build(server=self.get_server(), ucs_versions=[self.get_ucs_version()], locale=self.get_locale())

	def _save_cache(self):
		cache_file = self.get_cache_file()
		if cache_file:
			try:
				with open(cache_file, 'wb') as fd:
					dump([app.attrs_dict() for app in self._cache], fd, indent=2)
				cache_modified = self._cache_modified()
			except (EnvironmentError, TypeError):
				return False
			else:
				self._cache_modified_mtime = cache_modified
				return True

	def _load_cache(self):
		cache_file = self.get_cache_file()
		try:
			cache_modified = self._cache_modified()
			archive_modified = self._archive_modified()
			if _cmp_mtimes(cache_modified, archive_modified) == -1:
				cache_logger.debug('Cannot load cache: mtimes of cache files do not match: %r < %r' % (cache_modified, archive_modified))
				return None
			for master_file in self._relevant_master_files():
				master_file_modified = os.stat(master_file).st_mtime
				if _cmp_mtimes(cache_modified, master_file_modified) == -1:
					cache_logger.debug('Cannot load cache: %s is newer than cache' % master_file)
					return None
			with open(cache_file, 'rb') as fd:
				cache = load(fd)
			self._cache_modified_mtime = cache_modified
		except (EnvironmentError, ValueError, TypeError):
			cache_logger.debug('Cannot load cache: getting mtimes failed')
			return None
		else:
			try:
				cache_attributes = set(cache[0].keys())
			except (TypeError, AttributeError, IndexError, KeyError):
				cache_logger.debug('Cannot load cache: Getting cached attributes failed')
				return None
			else:
				code_attributes = set(attr.name for attr in self.get_app_class()._attrs)
				if cache_attributes != code_attributes:
					cache_logger.debug('Cannot load cache: Attributes in cache file differ from attribute in code')
					return None
				return [self._build_app_from_attrs(attrs) for attrs in cache]

	def _archive_modified(self):
		try:
			return os.stat(os.path.join(self.get_cache_dir(), '.all.tar')).st_mtime
		except (EnvironmentError, AttributeError) as exc:
			cache_logger.debug('Unable to get mtime for archive: %s' % exc)
			return None

	def _cache_modified(self):
		try:
			return os.stat(self.get_cache_file()).st_mtime
		except (EnvironmentError, AttributeError) as exc:
			cache_logger.debug('Unable to get mtime for cache: %s' % exc)
			return None

	def _relevant_master_files(self):
		ret = set()
		classes_visited = set()

		def add_class(klass):
			if klass in classes_visited:
				return
			classes_visited.add(klass)
			try:
				module = sys.modules[klass.__module__]
				ret.add(module.__file__)
			except (AttributeError, KeyError):
				pass
			if hasattr(klass, '__bases__'):
				for base in klass.__bases__:
					add_class(base)
			if hasattr(klass, '__metaclass__'):
				add_class(klass.__metaclass__)

		add_class(self.get_app_class())
		return ret

	def _relevant_ini_files(self):
		return glob(os.path.join(self.get_cache_dir(), '*.ini'))

	def _build_app_from_attrs(self, attrs):
		app = self.get_app_class()(attrs, self)
		return app

	def _build_app_from_ini(self, ini):
		app = self.get_app_class().from_ini(ini, locale=self.get_locale(), cache=self)
		if app:
			for attr in app._attrs:
				attr.post_creation(app)
		return app

	def clear_cache(self):
		ucr_load()
		self._cache[:] = []
		self._cache_modified_mtime = None
		self._invalidate_cache_files()

	def _invalidate_cache_files(self):
		cache_dir = self.get_cache_dir()
		for cache_file in glob(os.path.join(cache_dir, '.*apps*.json')):
			try:
				os.unlink(cache_file)
			except EnvironmentError:
				pass

	@contextmanager
	def _locked(self):
		timeout = 60
		wait = 0.1
		while self._lock:
			if timeout < 0:
				raise RuntimeError('Could not get lock in %s seconds' % timeout)
			sleep(wait)
			timeout -= wait
		self._lock = True
		try:
			yield
		finally:
			self._lock = False

	def get_every_single_app(self):
		with self._locked():
			cache_file = self.get_cache_file()
			if cache_file:
				archive_modified = self._archive_modified()

				if _cmp_mtimes(archive_modified, self._cache_modified_mtime) == 1:
					cache_logger.debug('Cache outdated. Need to rebuild')
					self._cache[:] = []
			if not self._cache:
				cached_apps = self._load_cache()
				if cached_apps is not None:
					self._cache = cached_apps
					cache_logger.debug('Loaded %d apps from cache' % len(self._cache))
				else:
					for ini in self._relevant_ini_files():
						app = self._build_app_from_ini(ini)
						if app is not None:
							self._cache.append(app)
					self._cache.sort()
					if self._save_cache():
						cache_logger.debug('Saved %d apps into cache' % len(self._cache))
					else:
						cache_logger.warn('Unable to cache apps')
		return self._cache

	def get_app_class(self):
		if self._app_class is None:
			self._app_class = App
		return self._app_class

	def __repr__(self):
		return 'AppCache(app_class=%r, ucs_version=%r, server=%r, locale=%r, cache_dir=%r)' % (self.get_app_class(), self.get_ucs_version(), self.get_server(), self.get_locale(), self.get_cache_dir())


class AppCenterCache(_AppCache):
	_appcenter_cache_cache = {}

	def __init__(self, cache_class=None, server=None, ucs_versions=None, locale=None, cache_dir=None):
		self._cache_class = cache_class
		self._server = server
		self._ucs_versions = ucs_versions
		self._locale = locale
		self._cache_dir = cache_dir
		self._license_type_cache = None
		self._ratings_cache = None
		self._app_categories_cache = None

	@classmethod
	def build(cls, cache_class=None, server=None, ucs_versions=None, locale=None, cache_dir=None):
		obj = cls(cache_class, server, ucs_versions, locale, cache_dir)
		key = cls, obj.get_app_cache_class(), obj.get_server(), tuple(obj.get_ucs_versions()), obj.get_locale(), obj.get_cache_dir()
		if key not in cls._appcenter_cache_cache:
			cls._appcenter_cache_cache[key] = obj
		return cls._appcenter_cache_cache[key]

	def _get_current_ucs_version(self):
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
						cache_logger.debug('Using UCS %s. Apparently an updater is running' % next_version)
						return next_version
		except (EnvironmentError, ValueError) as exc:
			cache_logger.warn('Could not parse univention-updater.status: %s' % exc)
		return ucr_get('version/version')

	def get_app_cache_class(self):
		if self._cache_class is None:
			self._cache_class = AppCache
		return self._cache_class

	def get_server(self):
		if self._server is None:
			self._server = default_server()
		return self._server

	def get_server_netloc(self):
		return urlsplit(self.get_server()).netloc

	def get_ucs_versions(self):
		if self._ucs_versions is None:
			cache_file = self.get_cache_file('.ucs.ini')
			ucs_version = self._get_current_ucs_version()
			versions = AppCenterVersion.all_from_file(cache_file)
			for version in versions:
				if version.name == ucs_version:
					self._ucs_versions = version.supported_ucs_versions
					break
			else:
				self._ucs_versions = [ucs_version]
		return self._ucs_versions

	def get_locale(self):
		if self._locale is None:
			self._locale = default_locale()
		return self._locale

	def get_cache_dir(self):
		if self._cache_dir is None:
			server = self.get_server_netloc()
			self._cache_dir = os.path.join(CACHE_DIR, server)
			mkdir(self._cache_dir)
		return self._cache_dir

	def get_cache_file(self, fname):
		return os.path.join(self.get_cache_dir(), fname)

	def get_app_caches(self):
		ret = []
		for ucs_version in self.get_ucs_versions():
			ret.append(self._build_app_cache(ucs_version))
		return ret

	def _build_app_cache(self, ucs_version):
		cache_dir = self.get_cache_file(ucs_version)
		return self.get_app_cache_class().build(ucs_version=ucs_version, server=self.get_server(), locale=self.get_locale(), cache_dir=cache_dir)

	def get_license_description(self, license_name):
		if self._license_type_cache is None:
			cache_file = self.get_cache_file('.license_types.ini')
			self._license_type_cache = LicenseType.all_from_file(cache_file)
		for license in self._license_type_cache:
			if license.name == license_name:
				return license.description

	def get_ratings(self):
		if self._ratings_cache is None:
			cache_file = self.get_cache_file('.rating.ini')
			self._ratings_cache = Rating.all_from_file(cache_file)
		return self._ratings_cache

	def get_app_categories(self):
		if self._app_categories_cache is None:
			cache_file = self.get_cache_file('.app-categories.ini')
			parser = read_ini_file(cache_file)
			locale = self.get_locale()
			if not parser.has_section(locale):
				locale = 'en'
			try:
				categories = dict(parser.items(locale))
			except NoSectionError:
				categories = {}
			self._app_categories_cache = categories
		return self._app_categories_cache

	def get_every_single_app(self):
		ret = []
		for app_cache in self.get_app_caches():
			ret.extend(app_cache.get_every_single_app())
		return ret

	def clear_cache(self):
		ucr_load()
		self._license_type_cache = None
		self._ratings_cache = None
		self._app_categories_cache = None
		for app_cache in self.get_app_caches():
			app_cache.clear_cache()

	def __repr__(self):
		return 'AppCenterCache(app_cache_class=%r, server=%r, ucs_versions=%r, locale=%r, cache_dir=%r)' % (self.get_app_cache_class(), self.get_server(), self.get_ucs_versions(), self.get_locale(), self.get_cache_dir())


class Apps(_AppCache):
	def __init__(self, cache_class=None, locale=None):
		self._cache_class = cache_class
		self._locale = locale

	def get_appcenter_cache_class(self):
		if self._cache_class is None:
			self._cache_class = AppCenterCache
		return self._cache_class

	def get_locale(self):
		if self._locale is None:
			self._locale = default_locale()
		return self._locale

	def get_appcenter_caches(self):
		server = default_server()
		cache = self._build_appcenter_cache(server, None)
		return [cache]

	def _build_appcenter_cache(self, server, ucs_versions):
		return self.get_appcenter_cache_class().build(server=server, ucs_versions=ucs_versions, locale=self.get_locale())

	def get_every_single_app(self):
		ret = []
		for app_cache in self.get_appcenter_caches():
			for app in app_cache.get_every_single_app():
				if self.include_app(app):
					ret.append(app)
		return ret

	def include_app(self, app):
		return app.supports_ucs_version()

	def clear_cache(self):
		for app_cache in self.get_appcenter_caches():
			app_cache.clear_cache()


class AllApps(Apps):
	def include_app(self, app):
		return True


class AppCenterVersion(IniSectionObject):
	supported_ucs_versions = IniSectionListAttribute(required=True)


class LicenseType(IniSectionObject):
	description = IniSectionAttribute(localisable=True)


class Rating(IniSectionObject):
	label = IniSectionAttribute(localisable=True)
	description = IniSectionAttribute(localisable=True)


def default_locale():
	return get_locale() or 'en'


def default_server():
	server = ucr_get('repository/app_center/server', 'https://appcenter.software-univention.de')
	if not server.startswith('http'):
		server = 'https://%s' % server
	return server


def default_ucs_version():
	cache = AppCenterCache.build(server=default_server())
	return cache.get_ucs_versions()[0]
