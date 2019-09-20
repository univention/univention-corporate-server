#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app modules
#
# Copyright 2015-2019 Univention GmbH
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
from glob import glob
import os.path
from argparse import ArgumentParser, Action, Namespace
import logging
import urllib2
import httplib
import ssl
from functools import wraps

from univention.appcenter.app_cache import Apps
from univention.appcenter.log import get_base_logger
from univention.appcenter.utils import underscore, call_process, verbose_http_error, send_information
from univention.appcenter.exceptions import Abort, NetworkError

_ACTIONS = {}
JOINSCRIPT_DIR = '/usr/lib/univention-install'


def possible_network_error(func):
	@wraps(func)
	def _func(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except (urllib2.HTTPError, urllib2.URLError, ssl.CertificateError, httplib.BadStatusLine) as exc:
			raise NetworkError(verbose_http_error(exc))
	return _func


class StoreAppAction(Action):
	cache_class = Apps

	@classmethod
	def parse_app_id_string(cls, app_id):
		try:
			app_id, app_version = app_id.split('=', 1)
		except ValueError:
			app_id, app_version = app_id, None
		try:
			ucs_version, app_id = app_id.split('/', 1)
		except ValueError:
			ucs_version, app_id = None, app_id
		if ucs_version:
			try:
				ucs_version, server = ucs_version.split('@', 1)
			except ValueError:
				ucs_version, server = ucs_version, None
		else:
			server = None
		ucs_version = ucs_version or None
		return app_id, app_version, ucs_version, server

	@classmethod
	def get_app_from_app_id_string(cls, app_id, app_version, ucs_version, server):
		apps_cache = cls.cache_class()
		if ucs_version or server:
			apps = []
			for appcenter_cache in apps_cache.get_appcenter_caches():
				for cache in appcenter_cache.get_app_caches():
					if ucs_version and ucs_version != cache.get_ucs_version():
						continue
					if server and server != cache.get_server_netloc():
						continue
					app = cache.find(app_id, app_version=app_version)
					if app:
						if app.is_installed():
							return app
						apps.append(app)
			if apps:
				return sorted(apps)[-1]
		else:
			return apps_cache.find(app_id, app_version=app_version)

	def __call__(self, parser, namespace, value, option_string=None):
		apps = []
		if self.nargs is None:
			value = [value]
		for val in value:
			app_id, app_version, ucs_version, server = self.parse_app_id_string(val)
			if self.cache_class:
				app = self.get_app_from_app_id_string(app_id, app_version, ucs_version, server)
			else:
				app = app_id, app_version, ucs_version, server
			if app is None:
				if app_version is not None:
					parser.error('Unable to find version %s of app %s. Maybe "%s update" to get the latest list of applications?' % (app_version, app_id, sys.argv[0]))
				else:
					parser.error('Unable to find app %s. Maybe "%s update" to get the latest list of applications?' % (app_id, sys.argv[0]))
			apps.append(app)
		if self.nargs is None:
			apps = apps[0]
		setattr(namespace, self.dest, apps)


class UniventionAppActionMeta(type):

	def __new__(mcs, name, bases, attrs):
		new_cls = super(UniventionAppActionMeta, mcs).__new__(mcs, name, bases, attrs)
		if hasattr(new_cls, 'main') and getattr(new_cls, 'main') is not None:
			_ACTIONS[new_cls.get_action_name()] = new_cls
			new_cls.logger = new_cls.parent_logger.getChild(new_cls.get_action_name())
			new_cls.progress = new_cls.logger.getChild('progress')
		return new_cls


class UniventionAppAction(object):
	__metaclass__ = UniventionAppActionMeta

	parent_logger = get_base_logger().getChild('actions')

	def __init__(self):
		self._progress_percentage = 0

	@classmethod
	def get_action_name(cls):
		return underscore(cls.__name__).replace('_', '-')

	@classmethod
	def _log(cls, logger, level, msg, *args, **kwargs):
		if logger is not None:
			logger = cls.logger.getChild(logger)
		else:
			logger = cls.logger
		logger.log(level, msg, *args, **kwargs)

	@classmethod
	def debug(cls, msg, logger=None):
		cls._log(logger, logging.DEBUG, str(msg))

	@classmethod
	def log(cls, msg, logger=None):
		cls._log(logger, logging.INFO, str(msg))

	@classmethod
	def warn(cls, msg, logger=None):
		cls._log(logger, logging.WARN, str(msg))

	@classmethod
	def fatal(cls, msg, logger=None):
		cls._log(logger, logging.FATAL, str(msg))

	@classmethod
	def log_exception(cls, exc, logger=None):
		cls._log(logger, logging.ERROR, exc, exc_info=1)

	def setup_parser(self, parser):
		pass

	@property
	def percentage(self):
		return self._progress_percentage

	@percentage.setter
	def percentage(self, percentage):
		self._progress_percentage = percentage
		self.progress.debug(str(percentage))

	def _build_namespace(self, _namespace=None, **kwargs):
		parser = ArgumentParser()
		self.setup_parser(parser)
		namespace = Namespace()
		args = {}
		for action in parser._actions:
			default = parser._defaults.get(action.dest)
			if action.default is not None:
				default = action.default
			if hasattr(_namespace, action.dest):
				default = getattr(_namespace, action.dest)
			args[action.dest] = default
		args.update(kwargs)
		for key, value in args.iteritems():
			setattr(namespace, key, value)
		return namespace

	@classmethod
	def call_safe(cls, **kwargs):
		try:
			return cls.call(**kwargs)
		except Abort:
			return None

	@classmethod
	def call(cls, **kwargs):
		obj = cls()
		namespace = obj._build_namespace(**kwargs)
		return obj.call_with_namespace(namespace)

	def call_with_namespace(self, namespace):
		self.debug('Calling %s' % self.get_action_name())
		self.percentage = 0
		try:
			result = self.main(namespace)
		except Abort as exc:
			msg = str(exc)
			if msg:
				self.fatal(msg)
			self.percentage = 100
			raise
		except Exception as exc:
			self.log_exception(exc)
			raise
		else:
			self.percentage = 100
			return result

	def _get_joinscript_path(self, app, unjoin=False):
		number = 50
		suffix = ''
		ext = 'inst'
		if unjoin:
			number = 51
			ext = 'uinst'
			suffix = '-uninstall'
		return os.path.join(JOINSCRIPT_DIR, '%d%s%s.%s' % (number, app.id, suffix, ext))

	def _call_cache_script(self, _app, _ext, *args, **kwargs):
		fname = _app.get_cache_file(_ext)
		# change to UCS umask + u+x:      -rwxr--r--
		if os.path.exists(fname):
			os.chmod(fname, 0o744)
		return self._call_script(fname, *args, **kwargs)

	def _call_script(self, _script, *args, **kwargs):
		if not os.path.exists(_script):
			self.debug('%s does not exist' % _script)
			return None
		subprocess_args = [_script] + list(args)
		for key, value in kwargs.iteritems():
			if value is None or value is False:
				continue
			key = '--%s' % key.replace('_', '-')
			subprocess_args.append(key)
			if value is not True:
				subprocess_args.append(value)

		process = self._subprocess(subprocess_args)
		self.debug('%s returned with %s' % (_script, process.returncode))

		return process.returncode == 0

	def _subprocess(self, args, logger=None, env=None):
		if logger is None:
			logger = self.logger
		elif isinstance(logger, basestring):
			logger = self.logger.getChild(logger)
		return call_process(args, logger, env)

	@possible_network_error
	def _send_information(self, app, status, value=None):
		action = self.get_action_name()
		send_information(action, app, status, value)


def get_action(action_name):
	_import()
	return _ACTIONS.get(action_name)


def all_actions():
	_import()
	for action_name in sorted(_ACTIONS):
		yield action_name, _ACTIONS[action_name]

def _import():
	if _ACTIONS:
		return
	path = os.path.dirname(__file__)
	for pymodule in glob(os.path.join(path, '*.py')):
		pymodule_name = os.path.basename(pymodule)[:-3]  # without .py
		__import__('univention.appcenter.actions.%s' % pymodule_name)
