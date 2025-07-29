#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest
from univentionunittests import import_module
from univentionunittests.udm_connection import MockedAccess, MockedPosition, get_domain
from univentionunittests.udm_database import Database


def pytest_addoption(parser):
    parser.addoption("--installed-udm", action="store_true", help="Test against installed UDM installation (not src)")


def import_udm_module(udm_path):
    python_module_name = f'univention.admin.{udm_path}'
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
