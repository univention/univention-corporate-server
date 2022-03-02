#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from univentionunittests import import_module
from univentionunittests.udm_database import Database
from univentionunittests.udm_connection import MockedAccess, MockedPosition, get_domain  # noqa: F401


def pytest_addoption(parser):
	parser.addoption("--installed-udm", action="store_true", help="Test against installed UDM installation (not src)")


def import_udm_module(udm_path):
	python_module_name = 'univention.admin.{}'.format(udm_path)
	umc_src_path = 'modules/univention/admin'
	use_installed = pytest.config.getoption('--installed-udm')
	return import_module(udm_path, umc_src_path, python_module_name, use_installed)


@pytest.fixture
def ldap_database_file():
	return None


@pytest.fixture
def ldap_database(ldap_database_file, empty_ldap_database):
	if ldap_database_file:
		empty_ldap_database.fill(ldap_database_file)
	return empty_ldap_database


@pytest.fixture
def empty_ldap_database():
	database = Database()
	return database


@pytest.fixture
def lo(ldap_database):
	from univention.admin.uldap import access
	lo = MockedAccess()
	lo.database = ldap_database
	lo.base = get_domain()
	lo.mock_add_spec(access)
	return lo


@pytest.fixture
def pos():
	return MockedPosition()
