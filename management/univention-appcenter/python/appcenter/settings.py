#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  .settings file for Apps
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

import os
import os.path

from univention.appcenter.utils import app_is_running, container_mode, mkdir, _
from univention.appcenter.log import get_base_logger
from univention.appcenter.ucr import ucr_get, ucr_is_true, ucr_run_filter
from univention.appcenter.ini_parser import TypedIniSectionObject, IniSectionBooleanAttribute, IniSectionListAttribute, IniSectionAttribute

settings_logger = get_base_logger().getChild('settings')


class SettingValueError(Exception):
	pass


class Setting(TypedIniSectionObject):
	'''Based on the .settings file, models additional settings for Apps
	that can be configured before installation, during run-time, etc.'''

	type = IniSectionAttribute(default='String', choices=['String', 'Int', 'Bool', 'List', 'Password', 'File', 'PasswordFile', 'Status'])
	description = IniSectionAttribute(localisable=True, required=True)
	group = IniSectionAttribute(localisable=True)
	show = IniSectionListAttribute(default=['Settings'], choices=['Install', 'Upgrade', 'Remove', 'Settings'])
	show_read_only = IniSectionListAttribute(choices=['Install', 'Upgrade', 'Remove', 'Settings'])

	initial_value = IniSectionAttribute()
	required = IniSectionBooleanAttribute()
	scope = IniSectionListAttribute(choices=['inside', 'outside'])

	@classmethod
	def get_class(cls, name):
		if name and not name.endswith('Setting'):
			name = '%sSetting' % name
		return super(Setting, cls).get_class(name)

	def is_outside(self, app):
		# for Non-Docker Apps, Docker Apps when called from inside, Settings specified for 'outside'
		return not app.docker or container_mode() or 'outside' in self.scope

	def is_inside(self, app):
		# only for Docker Apps (and called from the Docker Host). And not only 'outside' is specified
		return app.docker and not container_mode() and ('inside' in self.scope or self.scope == [])

	def get_initial_value(self, app):
		if self.is_outside(app):
			value = ucr_get(self.name)
			if value is not None:
				return self.sanitize_value(app, value)
		if isinstance(self.initial_value, basestring):
			return ucr_run_filter(self.initial_value)
		return self.initial_value

	def get_value(self, app, phase='Settings'):
		'''Get the current value for this Setting. Easy implementation'''
		if self.is_outside(app):
			value = ucr_get(self.name)
		else:
			if app_is_running(app):
				from univention.appcenter.actions import get_action
				configure = get_action('configure')
				ucr = configure._get_app_ucr(app)
				value = ucr.get(self.name)
			else:
				settings_logger.info('Cannot read %s while %s is not running' % (self.name, app))
				value = None
		try:
			value = self.sanitize_value(app, value)
		except SettingValueError:
			settings_logger.info('Cannot use %r for %s' % (value, self.name))
			value = None
		if value is None and phase == 'Install':
			settings_logger.info('Falling back to initial value for %s' % self.name)
			value = self.get_initial_value(app)
		return value

	def _log_set_value(self, app, value):
		if value is None:
			settings_logger.info('Unsetting %s' % self.name)
		else:
			settings_logger.info('Setting %s to %r' % (self.name, value))

	def set_value(self, app, value, together_config_settings, part):
		together_config_settings[part][self.name] = value

	def set_value_together(self, app, value, together_config_settings):
		value = self.sanitize_value(app, value)
		value = self.value_for_setting(app, value)
		self._log_set_value(app, value)
		if self.is_outside(app):
			together_config_settings.setdefault('outside', {})
			self.set_value(app, value, together_config_settings, 'outside')
		if self.is_inside(app):
			together_config_settings.setdefault('inside', {})
			self.set_value(app, value, together_config_settings, 'inside')

	def sanitize_value(self, app, value):
		if self.required and value in [None, '']:
			raise SettingValueError('%s is required' % self.name)
		return value

	def value_for_setting(self, app, value):
		if value is None:
			return None
		value = str(value)
		if value == '':
			return None
		return value

	def should_go_into_image_configuration(self, app):
		return self.is_inside(app) and ('Install' in self.show or 'Upgrade' in self.show)


class StringSetting(Setting):
	pass


class IntSetting(Setting):
	def sanitize_value(self, app, value):
		super(IntSetting, self).sanitize_value(app, value)
		if value is not None:
			try:
				return int(value)
			except (ValueError, TypeError):
				raise SettingValueError('%s: %r is not a number' % (self.name, value))


class BoolSetting(Setting):
	def sanitize_value(self, app, value):
		super(BoolSetting, self).sanitize_value(app, value)
		if isinstance(value, bool):
			return value
		return ucr_is_true(self.name, value=value)

	def value_for_setting(self, app, value):
		return str(value).lower()


class ListSetting(Setting):
	labels = IniSectionListAttribute()
	values = IniSectionListAttribute()

	def sanitize_value(self, app, value):
		super(ListSetting, self).sanitize_value(app, value)
		if value not in self.values:
			raise SettingValueError('%s: %r is not a valid option' % (self.name, value))
		return value


class UDMListSetting(ListSetting):
	udm_filter = IniSectionAttribute()


class FileSetting(Setting):
	filename = IniSectionAttribute(required=True)

	def _log_set_value(self, app, value):
		# do not log complete file content
		pass

	def _read_file_content(self, filename):
		try:
			with open(filename) as fd:
				return fd.read()
		except EnvironmentError:
			return None

	def _touch_file(self, filename):
		if not os.path.exists(filename):
			mkdir(os.path.dirname(filename))
			open(filename, 'wb')

	def _write_file_content(self, filename, content):
		try:
			if content:
				settings_logger.debug('Writing to %s' % filename)
				self._touch_file(filename)
				with open(filename, 'wb') as fd:
					fd.write(content)
			else:
				settings_logger.debug('Deleting %s' % filename)
				if os.path.exists(filename):
					os.unlink(filename)
		except EnvironmentError as exc:
			settings_logger.error('Could not set content: %s' % exc)

	def get_value(self, app, phase='Settings'):
		if self.is_outside(app):
			value = self._read_file_content(self.filename)
		else:
			if app_is_running(app):
				from univention.appcenter.docker import Docker
				docker = Docker(app)
				value = self._read_file_content(docker.path(self.filename))
			else:
				settings_logger.info('Cannot read %s while %s is not running' % (self.name, app))
				value = None
		if value is None and phase == 'Install':
			settings_logger.info('Falling back to initial value for %s' % self.name)
			value = self.get_initial_value(app)
		return value

	def set_value(self, app, value, together_config_settings, part):
		if part == 'outside':
			return self._write_file_content(self.filename, value)
		else:
			if not app_is_running(app):
				settings_logger.error('Cannot write %s while %s is not running' % (self.name, app))
				return
			from univention.appcenter.docker import Docker
			docker = Docker(app)
			return self._write_file_content(docker.path(self.filename), value)

	def should_go_into_image_configuration(self, app):
		return False


class PasswordSetting(Setting):
	description = IniSectionAttribute(default=_('Password'), localisable=True)

	def _log_set_value(self, app, value):
		# do not log password
		pass


class PasswordFileSetting(FileSetting, PasswordSetting):
	def _touch_file(self, filename):
		super(PasswordFileSetting, self)._touch_file(filename)
		os.chmod(filename, 0o600)


class StatusSetting(Setting):
	def set_value(self, app, value, together_config_settings, part):
		# do not set value via this function - has to be done directly
		pass
