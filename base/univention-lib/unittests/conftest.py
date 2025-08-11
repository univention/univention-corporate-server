#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from unittest.mock import MagicMock

import pytest
from univentionunittests import import_module


def pytest_addoption(parser):
    parser.addoption("--installed-lib", action="store_true", help="Test against installed Python lib installation (not src)")


def import_lib_module(request, name):
    use_installed = request.config.getoption('--installed-lib')
    return import_module(name, 'python/', f'univention.lib.{name}', use_installed=use_installed)


@pytest.fixture(scope='session')
def atjobs(request):
    return import_lib_module(request, "atjobs")


@pytest.fixture(scope='session')
def fstab(request):
    return import_lib_module(request, 'fstab')


@pytest.fixture(scope='session')
def i18n(request):
    return import_lib_module(request, 'i18n')


@pytest.fixture(scope='session')
def listenerSharePath(request):
    return import_lib_module(request, 'listenerSharePath')


@pytest.fixture(scope='session')
def locking(request):
    return import_lib_module(request, 'locking')


@pytest.fixture(scope='session')
def misc(request):
    sys.modules['univention.uldap'] = MagicMock()
    import_lib_module(request, 'ucs')
    return import_lib_module(request, 'misc')


@pytest.fixture(scope='session')
def ucrLogrotate(request):
    return import_lib_module(request, 'ucrLogrotate')


@pytest.fixture(scope='session')
def ucs(request):
    return import_lib_module(request, 'ucs')


@pytest.fixture(scope='session')
def umc_module(request):
    return import_lib_module(request, 'umc_module')


@pytest.fixture(scope='session')
def umc(request):
    return import_lib_module(request, 'umc')
