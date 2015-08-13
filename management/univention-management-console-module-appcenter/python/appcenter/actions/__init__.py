#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app modules
#
# Copyright 2015 Univention GmbH
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
from glob import glob
import os.path
from argparse import ArgumentParser, Action, Namespace
import stat
import logging
import urllib2
import urllib

from univention.config_registry import ConfigRegistry

from univention.appcenter import AppManager
from univention.appcenter.log import get_base_logger
from univention.appcenter.utils import underscore, call_process, urlopen

_ACTIONS = {}
JOINSCRIPT_DIR = '/usr/lib/univention-install'

class Abort(Exception):
	pass

class StoreAppAction(Action):
	def __call__(self, parser, namespace, value, option_string=None):
		apps = []
		if self.nargs is None:
			value = [value]
		for val in value:
			try:
				app_id, app_version = val.split('=', 1)
			except ValueError:
				app_id, app_version = val, None
			app = AppManager.find(app_id, app_version)
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

	def _build_namespace(self, **kwargs):
		parser = ArgumentParser()
		self.setup_parser(parser)
		namespace = Namespace()
		args = {}
		for action in parser._actions:
			default = parser._defaults.get(action.dest)
			if action.default is not None:
				default = action.default
			args[action.dest] = default
		args.update(kwargs)
		for key, value in args.iteritems():
			setattr(namespace, key, value)
		return namespace

	@classmethod
	def call(cls, **kwargs):
		obj = cls()
		namespace = obj._build_namespace(**kwargs)
		return obj.call_with_namespace(namespace)

	def call_with_namespace(self, namespace):
		self.debug('Calling with %r' % namespace)
		self.percentage = 0
		try:
			result = self.main(namespace)
		except Exception as exc:
			self.log_exception(exc)
			raise
		else:
			self.percentage = 100
			return result

	def _get_cache_file(self, app, ext):
		return app.get_cache_file(ext)

	def _call_cache_script(self, _app, _ext, *args, **kwargs):
		fname = self._get_cache_file(_app, _ext)
		# change to UCS umask + u+x:      -rwxr--r--
		if os.path.exists(fname):
			os.chmod(0744)
		return self._call_script(fname, *args, **kwargs)

	def _get_share_file(self, app, ext):
		return app.get_share_file(ext)

	def _call_share_script(self, _app, _ext, *args, **kwargs):
		fname = self._get_share_file(_app, _ext)
		if os.path.exists(fname):
			os.chmod(fname, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC | stat.S_IRGRP | stat.S_IROTH)
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
		self.log('%s returned with %s' % (_script, process.returncode))

		return process.returncode == 0

	def _subprocess(self, args, logger=None, env=None):
		if logger is None:
			logger = self.logger
		elif isinstance(logger, basestring):
			logger = self.logger.getChild(logger)
		return call_process(args, logger, env)

	def _send_information(self, app, status):
		action = self.get_action_name()
		self.debug('%s %s: %s' % (action, app.id, status))
		if not app.notify_vendor:
			return
		ucr = ConfigRegistry()
		ucr.load()
		server = AppManager.get_server()
		url = '%s/postinst' % server
		uuid = ucr.get('uuid/license', '00000000-0000-0000-0000-000000000000')
		try:
			values = {
				'uuid': uuid,
				'app': app.id,
				'version': app.version,
				'action': action,
				'status': status,
				'role': ucr.get('server/role'),
			}
			request_data = urllib.urlencode(values)
			request = urllib2.Request(url, request_data)
			urlopen(request)
		except Exception as exc:
			self.log_exception(exc)

def get_action(action_name):
	return _ACTIONS.get(action_name)

def all_actions():
	for action_name in sorted(_ACTIONS):
		yield action_name, _ACTIONS[action_name]

path = os.path.dirname(__file__)
for pymodule in glob(os.path.join(path, '*.py')):
	pymodule_name = os.path.basename(pymodule)[:-3] # without .py
	__import__('univention.appcenter.actions.%s' % pymodule_name)

