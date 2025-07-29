#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


import logging
import sys
from glob import glob

import pytest
from univentionunittests import import_module
from univentionunittests.umc import import_umc_module, save_result_on_request


@pytest.fixture
def mocked_connection(mocker, lo, pos):
    udm_module = _import('udm')
    mocker.patch.object(udm_module, 'getMachineConnection', return_value=[lo, pos])
    mocker.patch.object(udm_module, 'getAdminConnection', return_value=[lo, pos])
    return lo


@pytest.fixture
def get_action():
    actions_module = _import('actions')
    return actions_module.get_action


@pytest.fixture
def mocked_ucr_appcenter(mock_ucr, mocker):
    ucr_module = _import('ucr')
    mocker.patch.object(ucr_module, '_UCR', mock_ucr)

    def ucr_save(values):
        changed_values = {}
        for k, v in values.items():
            if mock_ucr.get(k) != v:
                changed_values[k] = v  # noqa: PERF403
        if changed_values:
            mock_ucr.items.update(changed_values)
        return changed_values
    mocker.patch.object(ucr_module, 'ucr_save', ucr_save)

    mock_ucr['uuid/license'] = '00000000-0000-0000-0000-000000000000'
    mock_ucr['server/role'] = 'domaincontroller_master'
    mock_ucr['hostname'] = 'master'
    mock_ucr['domainname'] = 'intranet.example.de'
    mock_ucr['version/version'] = '5.2'
    mock_ucr['version/patchlevel'] = '0'
    mock_ucr['version/erratalevel'] = '0'
    mock_ucr['repository/app_center/server'] = 'https://appcenter.software-univention.de'
    return mock_ucr


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
    #     name = os.path.basename(pymod)[:-3]
    import_module('listener', None, 'listener', use_installed=True)
    for name in ['log', 'ucr', 'utils', 'packages', 'meta', 'ini_parser', 'settings', 'app', 'app_cache', 'udm', 'actions', 'install_checks']:
        module = import_module(name, local_python_path, f'univention.appcenter.{name}', use_installed=use_installed)
        if name == 'log':
            module.log_to_stream()
            logger = module.get_base_logger()
            for handler in logger.handlers:
                for filter in handler.filters:
                    if hasattr(filter, 'min_level'):
                        filter.min_level = logging.DEBUG
        if name == 'actions' and not use_installed:
            import os.path
            for pymodule in glob('python/appcenter/actions/*.py'):
                name = os.path.basename(pymodule)[:-3]  # without .py
                local_python_path = os.path.dirname(pymodule)
                import_module(name, local_python_path, f'univention.appcenter.actions.{name}', use_installed=use_installed)
            for pymodule in glob('python/appcenter-docker/actions/service.py'):
                name = os.path.basename(pymodule)[:-3]  # without .py
                local_python_path = os.path.dirname(pymodule)
                import_module(name, local_python_path, f'univention.appcenter.actions.{name}', use_installed=use_installed)
            for pymodule in glob('python/appcenter-docker/actions/docker_base.py'):
                name = os.path.basename(pymodule)[:-3]  # without .py
                local_python_path = os.path.dirname(pymodule)
                import_module(name, local_python_path, f'univention.appcenter.actions.{name}', use_installed=use_installed)
            for pymodule in glob('python/appcenter-docker/actions/docker_*.py'):
                name = os.path.basename(pymodule)[:-3]  # without .py
                local_python_path = os.path.dirname(pymodule)
                import_module(name, local_python_path, f'univention.appcenter.actions.{name}', use_installed=use_installed)
            for pymodule in glob('python/appcenter-docker/actions/*.py'):
                name = os.path.basename(pymodule)[:-3]  # without .py
                local_python_path = os.path.dirname(pymodule)
                import_module(name, local_python_path, f'univention.appcenter.actions.{name}', use_installed=use_installed)


def _import(name):
    import_appcenter_modules()
    return sys.modules[f'univention.appcenter.{name}']


@pytest.fixture
def imported_appcenter_modules():
    import_appcenter_modules()


@pytest.fixture
def import_appcenter_module():
    return _import


@pytest.fixture
def appcenter_umc_instance(imported_appcenter_modules, mocker):
    appcenter = import_umc_module('appcenter')
    mocker.patch.object(appcenter.Instance, 'finished', side_effect=save_result_on_request)
    instance = appcenter.Instance()
    instance.init()
    return instance
