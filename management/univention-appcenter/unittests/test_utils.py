#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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


import pytest


@pytest.fixture
def ldap_database_file():
	return 'unittests/dependencies.ldif'


def test_dependency_selfservice(custom_apps, import_appcenter_module):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service')
	app2 = custom_apps.find('self-service-backend')

	resolved = utils.resolve_dependencies([app], 'install')
	assert resolved == [app2, app]


def test_dependency_selfservices_wrong_order(custom_apps, import_appcenter_module):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service')
	app2 = custom_apps.find('self-service-backend')

	resolved = utils.resolve_dependencies([app2, app], 'install')
	assert resolved == [app2, app]
	resolved = utils.resolve_dependencies([app, app2], 'install')
	assert resolved == [app2, app]


def test_dependency_selfservice_backend(custom_apps, import_appcenter_module):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service-backend')

	resolved = utils.resolve_dependencies([app], 'install')
	assert resolved == [app]


def test_dependency_selfservice_and_webmeetings(custom_apps, import_appcenter_module):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app1 = custom_apps.find('self-service')
	app2 = custom_apps.find('self-service-backend')
	app3 = custom_apps.find('kopano-webmeetings')
	app4 = custom_apps.find('kopano-webapp')
	app5 = custom_apps.find('kopano-core')

	resolved = utils.resolve_dependencies([app1, app3], 'install')
	assert resolved == [app2, app1, app5, app4, app3]


def test_dependency_selfservice_installed_in_domain(custom_apps, import_appcenter_module, mocked_connection):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service')
	app2 = custom_apps.find('kopano-webapp')

	resolved = utils.resolve_dependencies([app, app2], 'install')
	assert resolved == [app, app2]
	resolved = utils.resolve_dependencies([app2, app], 'install')
	assert resolved == [app2, app]


def test_dependency_selfservice_installed_locally(custom_apps, import_appcenter_module, mocker):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('kopano-webmeetings')
	app2 = custom_apps.find('kopano-webapp')
	mocker.patch.object(app2, 'is_installed', return_value=True)

	resolved = utils.resolve_dependencies([app], 'install')
	assert resolved == [app]


def test_dependency_remove_selfservice(custom_apps, import_appcenter_module, mocker):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service')
	app2 = custom_apps.find('self-service-backend')
	mocker.patch.object(app2, 'is_installed', return_value=True)

	resolved = utils.resolve_dependencies([app], 'remove')
	assert resolved == [app]


def test_dependency_remove_selfservice_backend(custom_apps, import_appcenter_module, mocker):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service-backend')
	app2 = custom_apps.find('self-service')
	mocker.patch.object(app2, 'is_installed', return_value=True)

	resolved = utils.resolve_dependencies([app], 'remove')
	assert resolved == [app]


def test_dependency_remove_selfservices_order(custom_apps, import_appcenter_module, mocker):
	utils = import_appcenter_module('utils')
	custom_apps.load('unittests/inis/dependencies')
	app = custom_apps.find('self-service-backend')
	app2 = custom_apps.find('self-service')

	resolved = utils.resolve_dependencies([app, app2], 'remove')
	assert resolved == [app2, app]
	resolved = utils.resolve_dependencies([app2, app], 'remove')
	assert resolved == [app2, app]
