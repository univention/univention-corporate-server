#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for configuring an app
#  (Docker Version)
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

import os.path
from contextlib import contextmanager

from univention.config_registry.backend import _ConfigRegistry

from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.configure import Configure
from univention.appcenter.utils import mkdir, app_is_running
from univention.appcenter.ucr import ucr_save
from univention.appcenter.log import get_logfile_logger


class NoDatabaseFound(Exception):
	pass


class Configure(Configure, DockerActionMixin):
	def setup_parser(self, parser):
		super(Configure, self).setup_parser(parser)
		parser.add_argument('--autostart', help='Sets the autostart mode for the app: yes=App starts when the host starts; manually=App starts when manually started; no=App will never start', choices=['yes', 'manually', 'no'])

	def _set_config(self, app, set_vars, args):
		self._set_autostart(app, args.autostart)
		super(Configure, self)._set_config(app, set_vars, args)

	def _set_autostart(self, app, autostart):
		if not app.docker:
			return
		if autostart is None:
			return
		if autostart not in ['yes', 'manually', 'no']:
			self.warn('Autostart must be one of yes, manually, no. Not setting to %r' % autostart)
			return
		ucr_save({'%s/autostart' % app.id: autostart})

	def _set_config_via_tool(self, app, set_vars):
		if not app.docker:
			return super(Configure, self)._set_config_via_tool(app, set_vars)
		if not app_is_running(app):
			self.warn('Cannot write settings while %s is not running' % app)
			return
		logfile_logger = get_logfile_logger('docker.configure')
		docker = self._get_docker(app)
		if not docker.execute('which', 'ucr', _logger=logfile_logger).returncode == 0:
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
			docker.execute('ucr', 'set', *set_args, _logger=logfile_logger)
		if unset_args:
			docker.execute('ucr', 'unset', *unset_args, _logger=logfile_logger)

	@classmethod
	@contextmanager
	def _locked_app_ucr(cls, app):
		ucr = cls._get_app_ucr(app)
		ucr.lock()
		try:
			ucr.load()
			yield ucr
		finally:
			ucr.unlock()

	@classmethod
	def _get_app_ucr(cls, app):
		ucr_file = cls._get_app_ucr_filename(app)
		ucr = _ConfigRegistry(ucr_file)
		ucr.load()
		return ucr

	@classmethod
	def _get_app_ucr_filename(cls, app):
		docker = cls._get_docker(app)
		ucr_file = docker.path('/etc/univention/base.conf')
		if ucr_file:
			mkdir(os.path.dirname(ucr_file))
			return ucr_file
		raise NoDatabaseFound()

	def _set_config_directly(self, app, set_vars):
		with self._locked_app_ucr(app) as _ucr:
			for key, value in set_vars.iteritems():
				if value is None:
					_ucr.pop(key, None)
				else:
					_ucr[key] = str(value)
			_ucr.save()

	def _run_configure_script(self, app, action):
		success = super(Configure, self)._run_configure_script(app, action)
		if success is not False and app.docker and app_is_running(app):
			success = self._execute_container_script(app, 'configure', credentials=False, cmd_args=[action])
		return success
