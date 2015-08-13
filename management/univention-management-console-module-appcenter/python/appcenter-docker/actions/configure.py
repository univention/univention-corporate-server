#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for configuring an app
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

import os.path
import locale
import ConfigParser
from argparse import Action

from univention.config_registry import ConfigRegistry
from univention.config_registry.backend import _ConfigRegistry
from univention.config_registry.frontend import ucr_update

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.docker import Docker
from univention.appcenter.utils import app_is_running, mkdir

class NoDatabaseFound(Exception):
	pass

class StoreConfigAction(Action):
	def __call__(self, parser, namespace, value, option_string=None):
		set_vars = {}
		for val in value:
			try:
				key, value = val.split('=', 1)
			except ValueError:
				parser.error('Could not parse %s. Use var=val. Skipping...' % val)
			else:
				set_vars[key] = value
		setattr(namespace, self.dest, set_vars)

class Configure(UniventionAppAction):
	'''Configures an application.'''
	help='Configure an app'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the app that shall be configured')
		parser.add_argument('--list', action='store_true', help='List all configuration options as well as their current values')
		parser.add_argument('--autostart', help='Sets the autostart mode for the app: yes=App starts when the host starts; manually=App starts when manually started; no=App will never start', choices=['yes', 'manually', 'no'])
		parser.add_argument('--set', nargs='+', action=StoreConfigAction, metavar='KEY=VALUE', dest='set_vars', help='Sets the configuration variable. Example: --set some/variable=value some/other/variable="value 2"')
		parser.add_argument('--unset', nargs='+', metavar='KEY', help='Unsets the configuration variable. Example: --unset some/variable')

	def main(self, args):
		if args.list:
			variables = self.list_config(args.app)
			for variable in variables:
				self.log('%s: %s (%s)' % (variable['id'], variable['value'], variable['description']))
			return variables
		else:
			self._set_autostart(args.app, args.autostart)
			set_vars = (args.set_vars or {}).copy()
			for key in (args.unset or []):
				set_vars[key] = None
			self._set_config(args.app, set_vars)

	@classmethod
	def _get_app_ucr(cls, app):
		docker = Docker(app, cls.logger)
		ucr_file = docker.path('/etc/univention/base.conf')
		if ucr_file:
			mkdir(os.path.dirname(ucr_file))
			ucr = _ConfigRegistry(ucr_file)
			ucr.load()
			return ucr
		raise NoDatabaseFound()

	@classmethod
	def list_config(cls, app):
		cls.debug('Finding all configuration options for %s' % app.id)
		filename = app.get_cache_file('univention-config-registry-variables')
		if not os.path.exists(filename):
			return []
		parser = ConfigParser.ConfigParser()
		with open(filename, 'rb') as fp:
			parser.readfp(fp)
		loc = locale.getlocale()[0]
		if isinstance(loc, basestring):
			loc = loc.split('_')[0]
		try:
			_ucr = cls._get_app_ucr(app)
		except NoDatabaseFound:
			_ucr = {}

		def _get_cfg(config, sec, name):
			try:
				return config.get(sec, name)
			except ConfigParser.NoOptionError:
				return None

		variables = []
		ucr = ConfigRegistry()
		for section in parser.sections():
			variable = {'id': section}
			variable['description'] = _get_cfg(parser, section, 'Description[%s]' % loc) or _get_cfg(parser, section, 'Description[en]')
			variable['type'] = _get_cfg(parser, section, 'type')
			if variable['type'] == 'boolean':
				variable['type'] = 'bool'
			default = _get_cfg(parser, section, 'default')
			value = _ucr.get(section, default)
			if variable['type'] == 'bool':
				if isinstance(value, basestring):
					value = value.lower()
				value = ucr.is_true(value=value)
			variable['value'] = value
			variable['advanced'] = _get_cfg(parser, section, 'advanced')
			variables.append(variable)
		return variables

	@classmethod
	def get_variable(cls, app, key):
		ucr = cls._get_app_ucr(app)
		return ucr.get(key)

	def _set_autostart(self, app, autostart):
		if autostart is None:
			return
		if autostart not in ['yes', 'manually', 'no']:
			self.warn('Autostart must be one of yes, manually, no. Not setting to %r' % autostart)
			return
		ucr = ConfigRegistry()
		ucr_update(ucr, {'%s/autostart' % app.id: autostart})

	def _set_config(self, app, set_vars):
		if not app_is_running(app):
			self.fatal('%s is not running. Cannot configure the app' % app.id)
			return
		if not set_vars:
			return
		self._set_config_via_tool(app, set_vars)

	def _set_config_directly(self, app, set_vars):
		ucr = ConfigRegistry()
		_ucr = self._get_app_ucr(app)
		variables = self.list_config(app)
		for key, value in set_vars.iteritems():
			# if this was one of the defined variables
			# and it is boolean, format it to "true"/"false"
			for variable in variables:
				if variable['id'] == key:
					if variable['type'] == 'bool':
						value = str(ucr.is_true(value=str(value).lower())).lower()

			_ucr[key] = value
		_ucr.lock()
		try:
			_ucr.save()
		finally:
			_ucr.unlock()

	def _set_config_via_tool(self, app, set_vars):
		docker = Docker(app, self.logger)
		if not docker.execute('which', 'ucr').returncode == 0:
			self.warn('ucr cannot be found, falling back to changing the database file directly')
			self._set_config_directly(app, set_vars)
			return
		self.log('Setting registry variables for %s' % app.id)
		set_args = []
		unset_args = []
		for key, value in set_vars.iteritems():
			if value is None:
				unset_args.append(key)
			else:
				set_args.append('%s=%s' % (key, value))
		if set_args:
			docker.execute('ucr', 'set', *set_args)
		if unset_args:
			docker.execute('ucr', 'unset', *unset_args)

