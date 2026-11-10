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
def register(get_action):
    return get_action('register')()


def _enable_component(ucr, key):
    ucr[key] = 'enabled'
    ucr[key + '/server'] = 'appcenter.software-univention.de'
    ucr[key + '/version'] = 'current'


def test_register_component_unregisters_other_versions(apps, register, mocked_ucr_appcenter):
    _enable_component(mocked_ucr_appcenter, COMPONENT_1_0)
    updates = register._register_component(apps.find('provisioning-service-backend', app_version='2.1.0'), delay=True)
    assert updates[COMPONENT_2_1_0] == 'enabled'
    assert updates[COMPONENT_1_0] is None
    assert updates[COMPONENT_1_0 + '/server'] is None


@pytest.mark.parametrize('component', [
    # upgrade from 1.0 to 2.0
    COMPONENT_1_0,
    # reverting a dry run of the upgrade from 2.0 to 2.1.0
    COMPONENT_2_1_0,
], ids=['1.0', '2.1.0'])
def test_register_without_repository_unregisters_other_versions(apps, register, mocked_ucr_appcenter, component):
    _enable_component(mocked_ucr_appcenter, component)
    updates = register._register_component(apps.find('provisioning-service-backend', app_version='2.0'), delay=True)
    assert updates == {
        component: None,
        component + '/server': None,
        component + '/version': None,
    }


def test_register_without_repository_nothing_to_unregister(apps, register):
    assert register._register_component(apps.find('provisioning-service-backend', app_version='2.0'), delay=True) == {}
    assert register._register_component(apps.find('samba4'), delay=True) == {}
