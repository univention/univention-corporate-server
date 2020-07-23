#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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

from univentionunittests import import_module

import pytest


@pytest.fixture
def mocked_connection(mocker, lo, pos):
	udm_module = _import('udm')
	mocker.patch.object(udm_module, 'get_machine_connection', return_value=[lo, pos])
	mocker.patch.object(udm_module, 'get_admin_connection', return_value=[lo, pos])


@pytest.fixture
def get_action(mocker, lo, pos):
	actions_module = _import('actions')
	return actions_module.get_action


@pytest.fixture
def custom_apps(mocker):
	cache_module = _import('app_cache')
	app_module = _import('app')
	Apps = cache_module.Apps

	def get_every_single_app(self):
		return self._test_apps

	def load(self, path):
		for ini in glob(path + '/*/*.ini'):
			app = app_module.App.from_ini(ini)
			self._test_apps.append(app)
	mocker.patch.object(Apps, 'get_every_single_app', get_every_single_app)
	Apps.load = load
	Apps._test_apps = []
	yield Apps()
	del Apps._test_apps
	del Apps.load


def pytest_addoption(parser):
	parser.addoption("--installed-appcenter", action="store_true", help="Test against installed appcenter installation (not src)")


def import_appcenter_modules():
	use_installed = pytest.config.getoption('--installed-appcenter')
	local_python_path = 'python/appcenter/'
	# for pymod in glob(local_python_path + '*.py'):
	# 	name = os.path.basename(pymod)[:-3]
	import_module('listener', None, 'listener', use_installed=True)
	for name in ['log', 'ucr', 'utils', 'packages', 'meta', 'ini_parser', 'settings', 'app', 'app_cache', 'udm', 'install_checks', 'actions']:
		import_module(name, local_python_path, 'univention.appcenter.{}'.format(name), use_installed=use_installed)


def _import(name):
	import_appcenter_modules()
	return sys.modules['univention.appcenter.{}'.format(name)]


@pytest.fixture
def import_appcenter_module():
	return _import
