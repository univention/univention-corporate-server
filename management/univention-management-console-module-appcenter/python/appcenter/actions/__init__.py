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
import re
from glob import glob
import os.path
from argparse import ArgumentParser, Action, Namespace
import logging

#from univention.appcenter import App
from univention.management.console.modules.appcenter.app_center import Application as _Application

from univention.appcenter.log import get_base_logger
from univention.appcenter.utils import call_process

_ACTIONS = {}
JOINSCRIPT_DIR = '/usr/lib/univention-install'

class StoreAppAction(Action):
	def __call__(self, parser, namespace, value, option_string=None):
		if self.nargs is None:
			app = _Application.find(value)
			setattr(namespace, self.dest, app)
		else:
			apps = []
			for val in value:
				app = _Application.find(val)
				if app is None:
					parser.error('Unable to find app %s. Maybe "%s update" to get the latest list of applications?' % (val, sys.argv[0]))
				apps.append(app)
			setattr(namespace, self.dest, apps)

class UniventionAppActionMeta(type):
    def __new__(mcs, name, bases, attrs):
        new_cls = super(UniventionAppActionMeta, mcs).__new__(mcs, name, bases, attrs)
	if hasattr(new_cls, 'main') and getattr(new_cls, 'main') is not None:
		_ACTIONS[new_cls.get_action_name()] = new_cls
		new_cls.logger = new_cls.parent_logger.getChild(new_cls.get_action_name())
        return new_cls

class UniventionAppAction(object):
	__metaclass__ = UniventionAppActionMeta

	parent_logger = get_base_logger().getChild('actions')

	@classmethod
	def get_action_name(cls):
		return re.sub('([a-z])([A-Z])', r'\1-\2', cls.__name__).lower()

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

	@classmethod
	def call(cls, **kwargs):
		obj = cls()
		parser = ArgumentParser()
		obj.setup_parser(parser)
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
		obj.debug('Calling with %r' % namespace)
		return obj.main(namespace)

	def _subprocess(self, args, logger=None, env=None):
		if logger is None:
			logger = self.logger
		elif isinstance(logger, basestring):
			logger = self.logger.getChild(logger)
		return call_process(args, logger, env)

path = os.path.dirname(__file__)
for pymodule in glob(os.path.join(path, '*.py')):
	pymodule_name = os.path.basename(pymodule)[:-3] # without .py
	__import__('univention.appcenter.actions.%s' % pymodule_name)

def get_action(action_name):
	return _ACTIONS.get(action_name)

def all_actions():
	for action_name in sorted(_ACTIONS):
		yield action_name, _ACTIONS[action_name]

