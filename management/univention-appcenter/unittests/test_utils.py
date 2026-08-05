#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
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


def test_dependency_on_primary_omits_satisfied_transitive_dependency(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    backend = custom_apps.find('kopano-core')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps = [backend.id]
    mocker.patch.object(
        utils,
        'app_is_installed_on_server',
        side_effect=lambda app_id, _server, _lo=None: app_id == backend.id,
    )

    for selected_apps in ([connector, provisioning], [provisioning, connector]):
        resolved, required_hosts = utils.resolve_domain_dependencies(selected_apps, 'install')

        assert resolved == [provisioning, connector]
        assert required_hosts == {provisioning.id: [primary]}


def test_dependency_on_primary_propagates_target_to_transitive_dependency(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    backend = custom_apps.find('kopano-core')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps = [backend.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=False)

    for selected_apps in ([connector, provisioning], [provisioning, connector]):
        resolved, required_hosts = utils.resolve_domain_dependencies(selected_apps, 'install')

        assert resolved == [backend, provisioning, connector]
        assert required_hosts == {
            provisioning.id: [primary],
            backend.id: [primary],
        }


def test_dependency_on_primary_is_omitted_when_already_installed(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=True)

    resolved, required_hosts = utils.resolve_domain_dependencies([connector], 'install')

    assert resolved == [connector]
    assert required_hosts == {}


def test_cli_does_not_install_missing_primary_dependency_on_member(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    mocked_ucr_appcenter['ldap/master'] = 'master.intranet.example.de'
    mocked_ucr_appcenter['hostname'] = 'member'

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=False)

    assert utils.resolve_dependencies([connector], 'install') == [connector]


def test_cli_installs_missing_primary_dependency_locally_on_primary(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    mocked_ucr_appcenter['ldap/master'] = 'master.intranet.example.de'

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    backend = custom_apps.find('kopano-core')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps = [backend.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=False)
    mocker.patch.object(backend, 'is_installed', return_value=False)

    assert utils.resolve_dependencies([connector], 'install') == [backend, provisioning, connector]


def test_nested_primary_dependencies_are_seeded_before_explicit_apps(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    primary = 'master.intranet.example.de'
    mocked_ucr_appcenter['ldap/master'] = primary

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    provisioning_backend = custom_apps.find('kopano-core')
    local_backend = custom_apps.find('self-service-backend')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps = []
    provisioning.required_apps_in_domain_on_primary = [provisioning_backend.id]
    provisioning_backend.required_apps = [local_backend.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=False)

    for selected_apps in ([connector, provisioning_backend], [provisioning_backend, connector]):
        resolved, required_hosts = utils.resolve_domain_dependencies(selected_apps, 'install')

        assert resolved == [local_backend, provisioning_backend, provisioning, connector]
        assert required_hosts == {
            provisioning.id: [primary],
            provisioning_backend.id: [primary],
            local_backend.id: [primary],
        }


def test_primary_dependency_cycle_is_detected(
    custom_apps, import_appcenter_module, mocked_connection, mocked_ucr_appcenter, mocker,
):
    utils = import_appcenter_module('utils')
    custom_apps.load('unittests/inis/dependencies')
    mocked_ucr_appcenter['ldap/master'] = 'master.intranet.example.de'

    connector = custom_apps.find('self-service')
    provisioning = custom_apps.find('kopano-webapp')
    connector.required_apps_in_domain = []
    connector.required_apps_in_domain_on_primary = [provisioning.id]
    provisioning.required_apps_in_domain = []
    provisioning.required_apps_in_domain_on_primary = [connector.id]
    mocker.patch.object(utils, 'app_is_installed_on_server', return_value=False)

    with pytest.raises(RuntimeError, match='dependency cycle'):
        utils.resolve_domain_dependencies([connector], 'install')
