#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for configuring an app
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

from tempfile import NamedTemporaryFile

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.exceptions import ConfigureFailed
from univention.appcenter.actions.install_base import StoreConfigAction
from univention.appcenter.utils import get_locale
from univention.appcenter.ucr import ucr_save
from univention.appcenter.settings import SettingValueError, FileSetting


class Configure(UniventionAppAction):

	'''Configures an application.'''
	help = 'Configure an app'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be configured')
		parser.add_argument('--list', action='store_true', help='List all configuration options as well as their current values')
		parser.add_argument('--set', nargs='+', action=StoreConfigAction, metavar='KEY=VALUE', dest='set_vars', help='Sets the configuration variable. Example: --set some/variable=value some/other/variable="value 2"')
		parser.add_argument('--unset', nargs='+', metavar='KEY', help='Unsets the configuration variable. Example: --unset some/variable')
		parser.add_argument('--run-script', choices=['settings', 'install', 'upgrade', 'remove', 'no'], default='settings', help='Run configuration script to support a specific action - or not at all. Default: %(default)s')

	def main(self, args):
		if args.list:
			for setting in args.app.get_settings():
				phase = 'Settings'
				if args.app.is_installed():
					phase = 'Install'
				value = setting.get_value(args.app, phase)
				if isinstance(setting, FileSetting):
					value = 'File %s contains %s bytes' % (setting.filename, len(value or ''))
				else:
					value = repr(value)
				self.log('%s: %s (%s)' % (setting.name, value, setting.description))
		else:
			self.log('Configuring %s' % args.app)
			set_vars = (args.set_vars or {}).copy()
			for key in (args.unset or []):
				set_vars[key] = None
			self._set_config(args.app, set_vars, args)

	@classmethod
	def list_config(cls, app):
		# DEPRECATED. remove after 4.x!
		variables = []
		settings = app.get_settings()
		for setting in settings:
			variable = setting.to_dict()
			variable['id'] = setting.name
			try:
				variable['value'] = setting.get_value(app)
			except SettingValueError:
				variable['value'] = setting.get_initial_value(app)
			variable['advanced'] = False
			variables.append(variable)
		return variables

	def _set_config(self, app, set_vars, args):
		settings = app.get_settings()
		other_settings = {}
		together_config_settings = {}
		for key, value in set_vars.iteritems():
			for setting in settings:
				if setting.name == key:
					try:
						setting.set_value_together(app, value, together_config_settings)
					except SettingValueError as exc:
						raise ConfigureFailed(app.name, exc)
					break
			else:
				other_settings[key] = value
		if together_config_settings.get('outside'):
			ucr_save(together_config_settings['outside'])
		if together_config_settings.get('inside'):
			other_settings.update(together_config_settings['inside'])
		if other_settings:
			self._set_config_via_tool(app, other_settings)
		if args.run_script != 'no':
			self._run_configure_script(app, args.run_script)

	def _set_config_via_tool(self, app, set_vars):
		ucr_save(set_vars)

	def _run_configure_script(self, app, action):
		ext = 'configure_host'
		with NamedTemporaryFile('r+b') as error_file:
			kwargs = {}
			kwargs['version'] = app.version
			kwargs['error_file'] = error_file.name
			locale = get_locale()
			if locale:
				kwargs['locale'] = locale
			success = self._call_cache_script(app, ext, action, **kwargs)
			if success is False:
				for line in error_file:
					self.fatal(line)
			return success
