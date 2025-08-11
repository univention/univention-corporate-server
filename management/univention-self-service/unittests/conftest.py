#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys

import pytest


@pytest.fixture
def mocked_conn(mocker, lo, pos):
    from univentionunittests.umc import import_umc_module
    selfservice = import_umc_module('passwordreset')
    mocker.patch.object(selfservice, 'get_admin_connection', return_value=[lo, pos])
    mocker.patch.object(selfservice, 'get_machine_connection', return_value=[lo, pos])
    import univention.management.console.ldap as umc_ldap
    mocker.patch.object(umc_ldap, '_getMachineConnection', return_value=[lo, pos])
    mocker.patch.object(umc_ldap, '_getAdminConnection', return_value=[lo, pos])
    yield
    umc_ldap.machine_connection.__self__.__dict__['_LDAP__ldap_connections'].clear()


@pytest.fixture
def selfservice_ucr(mocker, mock_ucr):
    from univentionunittests.umc import import_umc_module

    from univention.config_registry import ConfigRegistry
    selfservice = import_umc_module('passwordreset')
    mocker.patch.object(selfservice, 'ucr', mock_ucr)

    def inject_fake_ucr(self):
        self.clear()
        self.update(mock_ucr.items)
    mocker.patch.object(ConfigRegistry, 'load', inject_fake_ucr)
    mocker.patch.object(ConfigRegistry, '__enter__', side_effect=ValueError("You may not save a faked UCR"))
    mock_ucr['umc/self-service/enabled'] = 'yes'
    mock_ucr['umc/self-service/passwordreset/email/enabled'] = 'yes'
    mock_ucr['umc/self-service/account-deregistration/blacklist/groups'] = 'Administrators,Domain Admins'
    mock_ucr['umc/self-service/account-deregistration/blacklist/users'] = ''
    mock_ucr['umc/self-service/account-deregistration/whitelist/groups'] = 'Domain Users'
    mock_ucr['umc/self-service/account-deregistration/whitelist/users'] = ''
    mock_ucr['umc/self-service/passwordreset/blacklist/groups'] = 'Administrators,Domain Admins'
    mock_ucr['umc/self-service/passwordreset/whitelist/groups'] = 'Domain Users'
    mock_ucr['umc/self-service/profiledata/blacklist/groups'] = 'Administrators,Domain Admins'
    mock_ucr['umc/self-service/profiledata/blacklist/users'] = ''
    mock_ucr['umc/self-service/profiledata/whitelist/groups'] = 'Domain Users'
    mock_ucr['umc/self-service/profiledata/whitelist/users'] = ''
    return mock_ucr


@pytest.fixture
def selfservice_instance(umc_module_class, mocker):
    from univentionunittests.umc import import_umc_module, save_result_on_request
    selfservice = import_umc_module('passwordreset')
    send_plugin = import_umc_module('passwordreset.send_plugin', set_umc_module_fixture=False)
    mocker.patch.object(umc_module_class, 'finished', side_effect=save_result_on_request)
    mocker.patch.object(sys.modules[selfservice.get_sending_plugins.__module__], 'UniventionSelfServiceTokenEmitter', send_plugin.UniventionSelfServiceTokenEmitter)
    mod = umc_module_class()
    mod.init()
    return mod
