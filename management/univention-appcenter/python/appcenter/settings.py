#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  .settings file for Apps
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

import os
import os.path

from univention.appcenter.utils import app_is_running, container_mode, mkdir, _
from univention.appcenter.log import get_base_logger
from univention.appcenter.ucr import ucr_get, ucr_is_true, ucr_save, ucr_run_filter
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

	def get_initial_value(self):
		if isinstance(self.initial_value, basestring):
			return ucr_run_filter(self.initial_value)
		return self.initial_value

	def get_value(self, app):
		'''Get the current value for this Setting. Easy implementation'''
		if self.is_outside(app):
			value = ucr_get(self.name, self.get_initial_value())
		else:
			if not app_is_running(app):
				settings_logger.error('Cannot read %s while %s is not running' % (self.name, app))
				return
			from univention.appcenter.actions import get_action
			configure = get_action('configure')
			ucr = configure._get_app_ucr(app)
			value = ucr.get(self.name, self.get_initial_value())
		try:
			return self.sanitize_value(app, value)
		except SettingValueError:
			return self.get_initial_value()

	def _log_set_value(self, app, value):
		settings_logger.info('Setting %s to %r' % (self.name, value))

	def set_value(self, app, value):
		value = self.sanitize_value(app, value)
		value = self.value_for_setting(app, value)
		self._log_set_value(app, value)
		if self.is_outside(app):
			ucr_save({self.name: value})
		if self.is_inside(app):
			if not app_is_running(app):
				settings_logger.error('Cannot write %s while %s is not running' % (self.name, app))
				return
			from univention.appcenter.actions import get_action
			configure = get_action('configure')
			configure._set_config_via_tool(app, {self.name: value})

	def sanitize_value(self, app, value):
		if self.required and value in [None, '']:
			raise SettingValueError()
		return value

	def value_for_setting(self, app, value):
		return str(value)


class StringSetting(Setting):
	pass


class IntSetting(Setting):
	def sanitize_value(self, app, value):
		super(IntSetting, self).sanitize_value(app, value)
		if value is not None:
			return int(value)


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
		if not value in self.values:
			raise SettingValueError()
		return value


class UDMListSetting(ListSetting):
	udm_filter = IniSectionAttribute()


class FileSetting(Setting):
	filename = IniSectionAttribute(required=True)

	def _read_file_content(self, filename):
		try:
			with open(filename) as fd:
				return fd.read()
		except EnvironmentError:
			return self.get_initial_value()

	def _write_file_content(self, filename, content):
		try:
			if content:
				settings_logger.debug('Writing to %s' % filename)
				mkdir(os.path.dirname(self.filename))
				with open(self.filename, 'wb') as fd:
					fd.write(content)
			else:
				settings_logger.debug('Deleting %s' % filename)
				os.unlink(self.filename)
		except EnvironmentError as exc:
			settings_logger.error('Could not set content: %s' % exc)

	def get_value(self, app):
		if self.is_outside(app):
			return self._read_file_content(self.filename)
		else:
			if not app_is_running(app):
				settings_logger.error('Cannot read %s while %s is not running' % (self.name, app))
				return
			from univention.appcenter.docker import Docker
			docker = Docker(app)
			return self._read_file_content(docker.path(self.filename))

	def set_value(self, app, value):
		if self.is_outside(app):
			return self._write_file_content(self.filename, value)
		else:
			if not app_is_running(app):
				settings_logger.error('Cannot write %s while %s is not running' % (self.name, app))
				return
			from univention.appcenter.docker import Docker
			docker = Docker(app)
			return self._write_file_content(docker.path(self.filename), value)


class PasswordSetting(Setting):
	description = IniSectionAttribute(default=_('Password'), localisable=True)

	def _log_set_value(self, app, value):
		# do not log password
		pass


class PasswordFileSetting(FileSetting, PasswordSetting):
	pass


class StatusSetting(Setting):
	def set_value(self, app, value):
		# do not set value via this function - has to be done directly
		pass
