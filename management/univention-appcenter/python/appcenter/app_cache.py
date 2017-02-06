#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  module for storing Apps in a cache
#
# Copyright 2017 Univention GmbH
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


import sys
import os
import os.path
from contextlib import contextmanager
from time import sleep
from glob import glob
from json import dump, load
from urlparse import urlsplit
from distutils.version import LooseVersion

from univention.appcenter.app import App, CACHE_DIR, app_logger, _get_rating_items, _get_license_descriptions
#import univention.appcenter.app as appcenter_app
#App = appcenter_app.App
#CACHE_DIR = appcenter_app.CACHE_DIR
#app_logger = appcenter_app.app_logger
#_get_rating_items = appcenter_app._get_rating_items
#_get_license_descriptions = appcenter_app._get_license_descriptions

from univention.appcenter.utils import mkdir, get_locale, get_server_and_version
from univention.appcenter.ucr import ucr_load, ucr_is_true


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
		apps = sorted(self.get_all_apps_with_id(app_id))
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
			latest_app = apps[-1]
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
		for _app in apps:
			if prevent_docker and _app.docker and not (_app.docker_migration_works or _app.docker_migration_link):
				continue
			if _app <= app:
				break
			if _app.required_app_version_upgrade:
				if LooseVersion(_app.required_app_version_upgrade) > app_version:
					continue
			return _app

	def get_all_apps(self):
		ret = []
		ids = set()
		for app in self.get_every_single_app():
			ids.add(app.id)
		for app_id in sorted(ids):
			ret.append(self.find(app_id))
		return ret

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
		self._cache_modified = None
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
			self._server = get_server_and_version()[0][0]
		return self._server

	def get_ucs_version(self):
		if self._ucs_version is None:
			self._ucs_version = get_server_and_version()[0][1]
		return self._ucs_version

	def get_locale(self):
		if self._locale is None:
			self._locale = get_locale() or 'en'
		return self._locale

	def get_cache_dir(self):
		if self._cache_dir is None:
			server = urlsplit(self.get_server()).netloc
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

	def _invalidate_cache_file(self):
		cache_dir = self.get_cache_dir()
		for cache_file in glob(os.path.join(cache_dir, '.*apps*.json')):
			try:
				os.unlink(cache_file)
			except EnvironmentError:
				pass

	def _save_cache(self):
		cache_file = self.get_cache_file()
		if cache_file:
			try:
				with open(cache_file, 'wb') as fd:
					dump([app.attrs_dict() for app in self._cache], fd, indent=2)
			except (IOError, TypeError):
				return False
			else:
				cache_modified = os.stat(cache_file).st_mtime
				self._cache_modified = cache_modified
				return True

	def _load_cache(self):
		cache_file = self.get_cache_file()
		if cache_file:
			try:
				cache_modified = os.stat(cache_file).st_mtime
				for master_file in self._relevant_master_files():
					master_file_modified = os.stat(master_file).st_mtime
					if cache_modified < master_file_modified:
						return None
				with open(cache_file, 'rb') as fd:
					cache = load(fd)
				self._cache_modified = cache_modified
			except (OSError, IOError, ValueError):
				return None
			else:
				try:
					cache_attributes = set(cache[0].keys())
				except (TypeError, AttributeError, IndexError, KeyError):
					return None
				else:
					code_attributes = set(attr.name for attr in self.get_app_class()._attrs)
					if cache_attributes != code_attributes:
						return None
					return [self._build_app_from_attrs(attrs) for attrs in cache]

	def _relevant_master_files(self):
		ret = set()
		ret.add(os.path.join(self.get_cache_dir(), '.index.json.gz'))
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
		attrs = attrs.copy()
		attrs['_cache'] = self
		app = self.get_app_class()(**attrs)
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
		self._cache_modified = None
		self._invalidate_cache_file()
		_get_rating_items._cache = None
		_get_license_descriptions._cache = None

	@contextmanager
	def _locked(self):
		timeout = 60
		wait = 0.1
		while self._lock:
			if not timeout:
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
				try:
					cache_modified = os.stat(cache_file).st_mtime
				except (EnvironmentError, ValueError):
					cache_modified = None
				if cache_modified is None or cache_modified > self._cache_modified:
					app_logger.debug('Cache outdated. Need to rebuild')
					self._cache[:] = []
			if not self._cache:
				cached_apps = self._load_cache()
				if cached_apps is not None:
					self._cache = cached_apps
					app_logger.debug('Loaded %d apps from cache' % len(self._cache))
				else:
					for ini in self._relevant_ini_files():
						app = self._build_app_from_ini(ini)
						if app is not None:
							self._cache.append(app)
					self._cache.sort()
					if self._save_cache():
						app_logger.debug('Saved %d apps into cache' % len(self._cache))
					else:
						app_logger.warn('Unable to cache apps')
		return self._cache

	def get_app_class(self):
		if self._app_class is None:
			self._app_class = App
		return self._app_class

	def call_update(self):
		from univention.appcenter import get_action
		update = get_action('update')
		update.call(ucs_version=self.get_ucs_version(), appcenter_server=self.get_server(), cache_dir=self.get_cache_dir())
		self.clear_cache()

	def __repr__(self):
		return 'AppCache(app_class=%r, ucs_version=%r, server=%r, locale=%r, cache_dir=%r)' % (self.get_app_class(), self.get_ucs_version(), self.get_server(), self.get_locale(), self.get_cache_dir())


class Apps(_AppCache):
	def __init__(self, app_caches=None):
		if app_caches is None:
			app_caches = []
			for server, ucs_version in get_server_and_version():
				app_caches.append(AppCache.build(ucs_version=ucs_version, server=server))
		self.app_caches = app_caches

	def get_every_single_app(self):
		ret = []
		for app_cache in self.app_caches:
			for app in app_cache.get_every_single_app():
				if self.include_app(app):
					ret.append(app)
		return ret

	def include_app(self, app):
		return app.supports_ucs_version()

	def call_update(self):
		for app_cache in self.app_caches:
			app_cache.call_update()


class AllApps(Apps):
	def include_app(self, app):
		return True
