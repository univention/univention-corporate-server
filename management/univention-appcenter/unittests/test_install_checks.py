#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


import pytest


@pytest.fixture
def ldap_database_file():
    return 'unittests/install_checks.ldif'


def test_install_two_apps(custom_apps, import_appcenter_module, mocked_ucr_appcenter):
    custom_apps.load('unittests/inis/install_checks/')
    current_role = 'domaincontroller_master'
    mocked_ucr_appcenter['server/role'] = current_role
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('samba-memberserver'), custom_apps.find('oxseforucs')]
    requirement = install_checks.get_requirement('must_have_correct_server_role')
    result = requirement(apps, 'install').test()
    assert result == {'samba-memberserver': {'allowed_roles': 'memberserver', 'current_role': current_role}}
    result = requirement(apps, 'upgrade').test()
    assert result == {'samba-memberserver': {'allowed_roles': 'memberserver', 'current_role': current_role}}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_fitting_app_version(custom_apps, import_appcenter_module, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('oxseforucs')]
    old_app = custom_apps.find('oxseforucs', app_version='7.10.2-ucs3')
    mocker.patch.object(old_app, 'is_installed', return_value=True)
    requirement = install_checks.get_requirement('must_have_fitting_app_version')
    result = requirement(apps, 'install').test()
    assert result == {}
    result = requirement(apps, 'upgrade').test()
    assert result == {'oxseforucs': {'required_version': '7.10.3-ucs1'}}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_fitting_kernel_version(custom_apps, import_appcenter_module, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('ucsschool-kelvin-rest-api')]
    mocker.patch.object(install_checks.os, 'uname', return_value=('linux', 'master', '4.8.0-12-amd64', '#1 SMP Debian 4.8.210-1+deb9u1 (2020-06-07)', 'x86_64'))
    requirement = install_checks.get_requirement('must_have_fitting_kernel_version')
    result = requirement(apps, 'install').test()
    assert result == {'__all__': False}
    result = requirement(apps, 'upgrade').test()
    assert result == {'__all__': False}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_fitting_ucs_version(custom_apps, import_appcenter_module, mocked_ucr_appcenter):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('ucsschool-kelvin-rest-api'), custom_apps.find('wekan'), custom_apps.find('collabora')]
    mocked_ucr_appcenter['version/version'] = '4.4'
    mocked_ucr_appcenter['version/patchlevel'] = '1'
    mocked_ucr_appcenter['version/erratalevel'] = '50'
    requirement = install_checks.get_requirement('must_have_fitting_ucs_version')
    result = requirement(apps, 'install').test()
    assert result == {'ucsschool-kelvin-rest-api': {'required_version': '4.4-2'}, 'wekan': {'required_version': '4.4-1 errata251'}}
    result = requirement(apps, 'upgrade').test()
    assert result == {'ucsschool-kelvin-rest-api': {'required_version': '4.4-2'}, 'wekan': {'required_version': '4.4-1 errata251'}}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_conflicts_apps_with_installed(custom_apps, import_appcenter_module, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('kopano-webapp')]
    ox = custom_apps.find('oxseforucs', app_version='7.10.2-ucs3')
    mocker.patch.object(ox, 'is_installed', return_value=True)
    requirement = install_checks.get_requirement('must_have_no_conflicts_apps')
    result = requirement(apps, 'install').test()
    assert result == {'kopano-webapp': [{'id': 'oxseforucs', 'name': 'OX App Suite'}]}
    result = requirement(apps, 'upgrade').test()
    assert result == {'kopano-webapp': [{'id': 'oxseforucs', 'name': 'OX App Suite'}]}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_conflicts_apps_in_list(custom_apps, import_appcenter_module):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('kopano-webapp'), custom_apps.find('oxseforucs')]
    requirement = install_checks.get_requirement('must_have_no_conflicts_apps')
    result = requirement(apps, 'install').test()
    assert result == {'oxseforucs': [{'id': 'kopano-webapp', 'name': 'Kopano WebApp'}], 'kopano-webapp': [{'id': 'oxseforucs', 'name': 'OX App Suite'}]}
    result = requirement(apps, 'upgrade').test()
    assert result == {'oxseforucs': [{'id': 'kopano-webapp', 'name': 'Kopano WebApp'}], 'kopano-webapp': [{'id': 'oxseforucs', 'name': 'OX App Suite'}]}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_conflicts_apps_ports_installed(custom_apps, import_appcenter_module, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('collabora')]
    mocker.patch.object(install_checks, 'app_ports', return_value=[('collabora-online', '9980', '9980')])
    requirement = install_checks.get_requirement('must_have_no_conflicts_apps')
    result = requirement(apps, 'install').test()
    assert result == {'collabora': [{'id': 'collabora-online', 'name': 'Collabora Online'}]}
    result = requirement(apps, 'upgrade').test()
    assert result == {'collabora': [{'id': 'collabora-online', 'name': 'Collabora Online'}]}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_conflicts_apps_ports_in_list(custom_apps, import_appcenter_module):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('collabora'), custom_apps.find('collabora-online')]
    requirement = install_checks.get_requirement('must_have_no_conflicts_apps')
    result = requirement(apps, 'install').test()
    assert result == {'collabora': [{'id': 'collabora-online', 'name': 'Collabora Online'}], 'collabora-online': [{'id': 'collabora', 'name': 'Collabora Online Development Edition'}]}
    result = requirement(apps, 'upgrade').test()
    assert result == {'collabora': [{'id': 'collabora-online', 'name': 'Collabora Online'}], 'collabora-online': [{'id': 'collabora', 'name': 'Collabora Online Development Edition'}]}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_unmet_dependencies(custom_apps, import_appcenter_module):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('ucsschool-kelvin-rest-api'), custom_apps.find('self-service')]
    requirement = install_checks.get_requirement('must_have_no_unmet_dependencies')
    result = requirement(apps, 'install').test()
    assert result == {'self-service': [{'id': 'self-service-backend', 'in_domain': True, 'local_allowed': True, 'name': 'Self Service Backend'}], 'ucsschool-kelvin-rest-api': [{'id': 'ucsschool', 'in_domain': False, 'name': 'UCS@school'}]}
    result = requirement(apps, 'upgrade').test()
    assert result == {'self-service': [{'id': 'self-service-backend', 'in_domain': True, 'local_allowed': True, 'name': 'Self Service Backend'}], 'ucsschool-kelvin-rest-api': [{'id': 'ucsschool', 'in_domain': False, 'name': 'UCS@school'}]}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_no_unmet_dependencies_with_list(custom_apps, import_appcenter_module):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    apps = [custom_apps.find('ucsschool'), custom_apps.find('self-service-backend'), custom_apps.find('ucsschool-kelvin-rest-api'), custom_apps.find('self-service')]
    requirement = install_checks.get_requirement('must_have_no_unmet_dependencies')
    result = requirement(apps, 'install').test()
    assert result == {}
    result = requirement(apps, 'upgrade').test()
    assert result == {}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_not_be_depended_on(custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    kelvin = custom_apps.find('ucsschool-kelvin-rest-api')
    selfservice = custom_apps.find('self-service')
    mocker.patch.object(kelvin, 'is_installed', return_value=True)
    mocker.patch.object(selfservice, 'is_installed', return_value=True)
    apps = [custom_apps.find('ucsschool'), custom_apps.find('self-service-backend')]
    requirement = install_checks.get_requirement('must_not_be_depended_on')
    result = requirement(apps, 'install').test()
    assert result == {}
    result = requirement(apps, 'upgrade').test()
    assert result == {}
    result = requirement(apps, 'remove').test()
    assert result == {'ucsschool': [{'id': 'ucsschool-kelvin-rest-api', 'name': 'UCS@school Kelvin REST API'}], 'self-service-backend': [{'id': 'self-service', 'name': 'Self Service'}]}


def test_must_not_be_depended_on_in_list(custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    kelvin = custom_apps.find('ucsschool-kelvin-rest-api')
    selfservice = custom_apps.find('self-service')
    mocker.patch.object(kelvin, 'is_installed', return_value=True)
    mocker.patch.object(selfservice, 'is_installed', return_value=True)
    apps = [custom_apps.find('ucsschool'), custom_apps.find('self-service-backend'), kelvin, selfservice]
    requirement = install_checks.get_requirement('must_not_be_depended_on')
    result = requirement(apps, 'install').test()
    assert result == {}
    result = requirement(apps, 'upgrade').test()
    assert result == {}
    result = requirement(apps, 'remove').test()
    assert result == {}


def test_must_have_primary_dependency_on_primary(
    custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker,
):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('self-service-backend')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    domain = mocker.Mock()
    domain.to_dict.return_value = []
    mocker.patch.object(install_checks, 'get_action', return_value=domain)
    mocker.patch.object(install_checks, 'app_is_installed_on_server', return_value=False)

    requirement = install_checks.get_requirement('must_have_no_unmet_dependencies')
    result = requirement([connector], 'install').test()

    assert result == {
        connector.id: [{
            'id': provisioning.id,
            'name': provisioning.name,
            'in_domain': True,
            'local_allowed': True,
            'required_host': primary,
        }],
    }


def test_primary_dependency_check_uses_primary_for_transitive_dependencies(
    custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker,
):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    backend = custom_apps.find('kopano-core')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps = [backend.id]
    domain = mocker.Mock()
    domain.to_dict.return_value = []
    mocker.patch.object(install_checks, 'get_action', return_value=domain)
    mocker.patch.object(
        install_checks,
        'app_is_installed_on_server',
        side_effect=lambda app_id, _host: app_id == backend.id,
    )

    requirement = install_checks.get_requirement('must_have_no_unmet_dependencies')

    assert requirement([connector, provisioning], 'install').test() == {}


def test_removing_primary_dependency_is_blocked_only_on_primary(
    custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker,
):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('self-service-backend')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    domain = mocker.Mock()
    domain.to_dict.return_value = [{
        'id': connector.id,
        'name': connector.name,
        'is_installed_anywhere': True,
        'installations': {'master': {'version': connector.version}},
    }]
    mocker.patch.object(install_checks, 'get_action', return_value=domain)
    requirement = install_checks.get_requirement('must_not_be_depended_on')

    assert requirement([provisioning], 'remove').test() == {
        provisioning.id: [{'id': connector.id, 'name': connector.name}],
    }

    mocked_ucr_appcenter['hostname'] = 'member'
    assert requirement([provisioning], 'remove').test() == {}


def test_removing_primary_dependency_and_depending_app_together_is_allowed(
    custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker,
):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    mocked_ucr_appcenter['ldap/master'] = 'master.intranet.example.de'

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('self-service-backend')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    domain = mocker.Mock()
    domain.to_dict.return_value = [{
        'id': connector.id,
        'name': connector.name,
        'is_installed_anywhere': True,
        'installations': {'master': {'version': connector.version}},
    }]
    mocker.patch.object(install_checks, 'get_action', return_value=domain)
    requirement = install_checks.get_requirement('must_not_be_depended_on')

    assert requirement([provisioning, connector], 'remove').test() == {}


def test_removing_primary_dependency_stays_blocked_when_depending_app_remains_elsewhere(
    custom_apps, import_appcenter_module, mocked_ucr_appcenter, mocker,
):
    custom_apps.load('unittests/inis/install_checks/')
    install_checks = import_appcenter_module('install_checks')
    mocked_ucr_appcenter['ldap/master'] = 'master.intranet.example.de'

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('self-service-backend')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    domain = mocker.Mock()
    domain.to_dict.return_value = [{
        'id': connector.id,
        'name': connector.name,
        'is_installed_anywhere': True,
        'installations': {
            'master': {'version': connector.version},
            'member': {'version': connector.version},
        },
    }]
    mocker.patch.object(install_checks, 'get_action', return_value=domain)
    requirement = install_checks.get_requirement('must_not_be_depended_on')

    assert requirement([provisioning, connector], 'remove').test() == {
        provisioning.id: [{'id': connector.id, 'name': connector.name}],
    }
