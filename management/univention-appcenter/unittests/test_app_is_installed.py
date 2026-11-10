#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


import pytest


COMPONENT_1_0 = 'repository/online/component/provisioning-service-backend_20250703013511'
COMPONENT_2_1_0 = 'repository/online/component/provisioning-service-backend_20261103162604'


@pytest.fixture
def apps(custom_apps, mocked_ucr_appcenter):
    custom_apps.load('unittests/inis/is_installed')
    return custom_apps


@pytest.fixture
def packages_installed(import_appcenter_module, mocker):
    app_module = import_appcenter_module('app')
    return mocker.patch.object(app_module, 'packages_are_installed', return_value=True)


def _installed_versions(apps, app_id):
    return [app.version for app in apps.get_all_locally_installed_apps() if app.id == app_id]


def test_version_without_repository_installed(apps, packages_installed):
    # e.g. provisioning-service-backend 2.0, whose packages came from the UCS repository
    assert _installed_versions(apps, 'provisioning-service-backend') == ['2.0']
    assert apps.find('provisioning-service-backend').version == '2.0'


def test_registered_component_takes_precedence(apps, packages_installed, mocked_ucr_appcenter):
    # after an upgrade from 2.0 to 2.1.0, the shared packages belong to 2.1.0
    mocked_ucr_appcenter[COMPONENT_2_1_0] = 'enabled'
    assert _installed_versions(apps, 'provisioning-service-backend') == ['2.1.0']
    assert apps.find('provisioning-service-backend').version == '2.1.0'
    assert [app.version for app in apps.get_all_apps() if app.id == 'provisioning-service-backend'] == ['2.1.0']


def test_registered_component_takes_precedence_over_stale_version(apps, packages_installed, mocked_ucr_appcenter):
    # systems that already went through the bug: a register run had set the version back to 2.0
    mocked_ucr_appcenter[COMPONENT_2_1_0] = 'enabled'
    mocked_ucr_appcenter['appcenter/apps/provisioning-service-backend/version'] = '2.0'
    assert _installed_versions(apps, 'provisioning-service-backend') == ['2.1.0']


def test_registered_component_of_older_version(apps, packages_installed, mocked_ucr_appcenter):
    # 1.0 had its own repository before the App moved into the UCS repository with 2.0
    mocked_ucr_appcenter[COMPONENT_1_0] = 'enabled'
    assert _installed_versions(apps, 'provisioning-service-backend') == ['1.0']
    assert apps.find('provisioning-service-backend').version == '1.0'


def test_packages_not_installed(apps, packages_installed, mocked_ucr_appcenter):
    packages_installed.return_value = False
    mocked_ucr_appcenter[COMPONENT_2_1_0] = 'enabled'
    assert _installed_versions(apps, 'provisioning-service-backend') == []
    assert apps.find('provisioning-service-backend').version == '2.1.0'


def test_app_without_any_repository_ignores_version(apps, packages_installed, mocked_ucr_appcenter):
    # UCS component Apps like samba4 have no version with a repository; after a UCS release
    # update, the registered version may still be the old one
    mocked_ucr_appcenter['appcenter/apps/samba4/version'] = '4.18'
    assert _installed_versions(apps, 'samba4') == ['4.21']
