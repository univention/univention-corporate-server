#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import sys

import pytest


ANYTHING = object()


@pytest.fixture
def custom_apps_umc(custom_apps, mocked_ucr_appcenter):
    custom_apps.load('unittests/inis/umc/')
    return custom_apps


def assert_called_with(mock, *argss):
    assert mock.call_count == len(argss)
    for call, (args, kwargs) in zip(mock.call_args_list, argss):
        call = call.call_list()
        assert len(call[0][0]) == len(args)
        assert len(call[0][1]) == len(kwargs)
        for call_arg, assert_arg in zip(call[0][0], args):
            if assert_arg is ANYTHING:
                continue
            assert call_arg == assert_arg
        for key, assert_arg in kwargs.items():
            call_arg = call[0][1][key]
            if assert_arg is ANYTHING:
                continue
            assert call_arg == assert_arg


class TestRiot:
    def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
        umc_request.options = {'apps': ['riot'], 'action': 'install'}
        appcenter_umc_instance.resolve(umc_request)
        assert 'apps' in umc_request.result
        assert len(umc_request.result['apps']) == 1
        assert umc_request.result['apps'][0]['id'] == 'riot'
        assert 'autoinstalled' in umc_request.result
        assert [] == umc_request.result['autoinstalled']
        assert 'errors' in umc_request.result
        assert isinstance(umc_request.result['errors'], dict)
        assert 'warnings' in umc_request.result
        assert isinstance(umc_request.result['warnings'], dict)

    def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        settings = {'riot/default/base_url': '/riot', 'riot/default/server_name': host}
        umc_request.options = {'apps': ['riot'], 'action': 'install', 'auto_installed': [], 'hosts': {'riot': host}, 'settings': {'riot': settings}, 'dry_run': True}
        mock = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_local')
        mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(mock, [(custom_apps_umc.find('riot'), 'install', settings, ANYTHING), {}])

    def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        settings = {'riot/default/base_url': '/riot', 'riot/default/server_name': host}
        umc_request.options = {'apps': ['riot'], 'action': 'install', 'auto_installed': [], 'hosts': {'riot': host}, 'settings': {'riot': settings}, 'dry_run': False}
        mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mock = mocker.patch.object(appcenter_umc_instance, '_run_local')
        mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(mock, [(custom_apps_umc.find('riot'), 'install', settings, ANYTHING), {}])


class TestKopano:
    def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
        umc_request.options = {'apps': ['kopano-webapp'], 'action': 'install'}
        appcenter_umc_instance.resolve(umc_request)
        assert 'apps' in umc_request.result
        assert len(umc_request.result['apps']) == 2
        assert umc_request.result['apps'][0]['id'] == 'kopano-core'
        assert 'autoinstalled' in umc_request.result
        assert ['kopano-core'] == umc_request.result['autoinstalled']
        assert 'errors' in umc_request.result
        assert isinstance(umc_request.result['errors'], dict)
        assert 'warnings' in umc_request.result
        assert isinstance(umc_request.result['warnings'], dict)

    def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}-fake.{domainname}'.format(**mocked_ucr_appcenter)
        localhost = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        umc_request.options = {'apps': ['kopano-webapp', 'kopano-core'], 'action': 'install', 'auto_installed': ['kopano-core'], 'hosts': {'kopano-webapp': localhost, 'kopano-core': host}, 'settings': {'kopano-core': {}, 'kopano-webapp': {}}, 'dry_run': True}
        mock1 = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_local')
        mock2 = mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(mock1, [(custom_apps_umc.find('kopano-webapp'), 'install', {}, ANYTHING), {}])
        assert_called_with(mock2, [(host, custom_apps_umc.find('kopano-core'), 'install', True, {}, ANYTHING), {}])

    def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}-fake.{domainname}'.format(**mocked_ucr_appcenter)
        localhost = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        umc_request.options = {'apps': ['kopano-webapp', 'kopano-core'], 'action': 'install', 'auto_installed': ['kopano-core'], 'hosts': {'kopano-webapp': localhost, 'kopano-core': host}, 'settings': {'kopano-core': {}, 'kopano-webapp': {}}, 'dry_run': False}
        mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mock1 = mocker.patch.object(appcenter_umc_instance, '_run_local')
        mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mock2 = mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(mock1, [(custom_apps_umc.find('kopano-webapp'), 'install', {}, ANYTHING), {}])
        assert_called_with(mock2, [(host, custom_apps_umc.find('kopano-core'), 'install', True, {}, ANYTHING), {}])


class TestUCSSchool:
    def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
        umc_request.options = {'apps': ['ucsschool-kelvin-rest-api', 'ucsschool'], 'action': 'install'}
        appcenter_umc_instance.resolve(umc_request)
        assert 'apps' in umc_request.result
        assert len(umc_request.result['apps']) == 2
        assert umc_request.result['apps'][0]['id'] == 'ucsschool'
        assert 'autoinstalled' in umc_request.result
        assert [] == umc_request.result['autoinstalled']
        assert 'errors' in umc_request.result
        assert isinstance(umc_request.result['errors'], dict)
        assert 'warnings' in umc_request.result
        assert isinstance(umc_request.result['warnings'], dict)

    def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        settings_ucsschool = {'ucsschool/join/create_demo': False}
        settings_kelvin = {'ucsschool/kelvin/access_tokel_ttl': 60, 'ucsschool/kelvin/log_level': 'DEBUG'}
        umc_request.options = {'apps': ['ucsschool', 'ucsschool-kelvin-rest-api'], 'action': 'install', 'auto_installed': [], 'hosts': {'ucsschool': host, 'ucsschool-kelvin-rest-api': host}, 'settings': {'ucsschool': settings_ucsschool, 'ucsschool-kelvin-rest-api': settings_kelvin}, 'dry_run': True}
        mock = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_local')
        mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(
            mock,
            [(custom_apps_umc.find('ucsschool'), 'install', settings_ucsschool, ANYTHING), {}],
            [(custom_apps_umc.find('ucsschool-kelvin-rest-api'), 'install', settings_kelvin, ANYTHING), {}],
        )

    def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
        host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
        settings_ucsschool = {'ucsschool/join/create_demo': False}
        settings_kelvin = {'ucsschool/kelvin/access_tokel_ttl': 60, 'ucsschool/kelvin/log_level': 'DEBUG'}
        umc_request.options = {'apps': ['ucsschool', 'ucsschool-kelvin-rest-api'], 'action': 'install', 'auto_installed': [], 'hosts': {'ucsschool': host, 'ucsschool-kelvin-rest-api': host}, 'settings': {'ucsschool': settings_ucsschool, 'ucsschool-kelvin-rest-api': settings_kelvin}, 'dry_run': False}
        mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
        mock = mocker.patch.object(appcenter_umc_instance, '_run_local')
        mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
        mocker.patch.object(appcenter_umc_instance, '_run_remote')
        appcenter_umc_instance.run(umc_request)
        umc_request.progress(appcenter_umc_instance.progress)
        assert_called_with(
            mock,
            [(custom_apps_umc.find('ucsschool'), 'install', settings_ucsschool, ANYTHING), {}],
            [(custom_apps_umc.find('ucsschool-kelvin-rest-api'), 'install', settings_kelvin, ANYTHING), {}],
        )


def test_run_validates_required_hosts_server_side(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    provisioning = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([provisioning, connector], {provisioning.id: [primary]}),
    )

    appcenter_umc_instance._validate_required_hosts(
        [provisioning, connector],
        [provisioning.id],
        'install',
        {primary: [provisioning.id], member: [connector.id]},
    )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='must be installed on'):
        appcenter_umc_instance._validate_required_hosts(
            [provisioning, connector],
            [provisioning.id],
            'install',
            {primary: [connector.id], member: [provisioning.id]},
        )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='exactly one target host'):
        appcenter_umc_instance._validate_required_hosts(
            [provisioning, connector],
            [provisioning.id],
            'install',
            {primary: [provisioning.id], member: [provisioning.id, connector.id]},
        )


def test_run_rejects_incomplete_or_inconsistent_plan(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    provisioning = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([provisioning, connector], {provisioning.id: [primary]}),
    )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='now also requires'):
        appcenter_umc_instance._validate_required_hosts(
            [connector], [], 'install', {member: [connector.id]},
        )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='now also requires'):
        appcenter_umc_instance._validate_required_hosts(
            [connector], [provisioning.id], 'install', {member: [connector.id]},
        )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='duplicate Apps'):
        appcenter_umc_instance._validate_required_hosts(
            [connector, connector], [], 'install', {member: [connector.id]},
        )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='unknown Apps'):
        appcenter_umc_instance._validate_required_hosts(
            [provisioning, connector],
            [provisioning.id],
            'install',
            {primary: [provisioning.id, 'unknown'], member: [connector.id]},
        )


def test_run_rejects_newly_satisfied_automatic_dependency(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    provisioning = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([connector], {}),
    )
    with pytest.raises(appcenter_module.umcm.UMC_Error, match='inconsistent'):
        appcenter_umc_instance._validate_required_hosts(
            [provisioning, connector],
            [provisioning.id],
            'install',
            {primary: [provisioning.id], member: [connector.id]},
        )


def test_run_rejects_unrelated_app_marked_as_automatic(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    unrelated = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([connector], {}),
    )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='inconsistent'):
        appcenter_umc_instance._validate_required_hosts(
            [connector, unrelated],
            [unrelated.id],
            'install',
            {member: [connector.id], primary: [unrelated.id]},
        )


def test_run_rejects_full_plan_with_only_automatic_apps(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    provisioning = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([], {}),
    )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='inconsistent'):
        appcenter_umc_instance._validate_required_hosts(
            [provisioning],
            [provisioning.id],
            'install',
            {primary: [provisioning.id]},
        )


def test_remote_auto_dependency_subsets_keep_auto_installed_semantics(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    provisioning = custom_apps_umc.find('kopano-webapp')
    backend = custom_apps_umc.find('kopano-core')
    primary = 'master.intranet.example.de'
    resolver = mocker.patch.object(appcenter_module, 'resolve_domain_dependencies')
    auto_installed = [backend.id, provisioning.id]

    resolver.return_value = ([provisioning], {})
    apps, hosts = appcenter_umc_instance._validate_required_hosts(
        [provisioning], auto_installed, 'install', {primary: [provisioning.id]},
        plan_is_subset=True,
    )
    assert apps == [provisioning]
    assert hosts == {primary: [provisioning.id]}
    assert auto_installed == [backend.id, provisioning.id]
    assert resolver.call_args.args[0] == [provisioning]

    resolver.return_value = ([backend, provisioning], {})
    apps, hosts = appcenter_umc_instance._validate_required_hosts(
        [backend, provisioning],
        auto_installed,
        'install',
        {primary: [backend.id, provisioning.id]},
        plan_is_subset=True,
    )
    assert apps == [backend, provisioning]
    assert hosts == {primary: [backend.id, provisioning.id]}
    assert auto_installed == [backend.id, provisioning.id]
    assert resolver.call_args.args[0] == [backend, provisioning]


def test_remote_root_subset_accepts_dependency_assigned_to_another_host(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    provisioning = custom_apps_umc.find('kopano-webapp')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([provisioning, connector], {provisioning.id: [primary]}),
    )
    auto_installed = [provisioning.id]

    apps, hosts = appcenter_umc_instance._validate_required_hosts(
        [connector], auto_installed, 'install', {member: [connector.id]},
        plan_is_subset=True,
        dry_run=True,
    )

    assert apps == [connector]
    assert hosts == {member: [connector.id]}
    assert auto_installed == [provisioning.id]


@pytest.mark.parametrize('action', ['remove', 'upgrade'])
def test_run_allows_same_app_on_multiple_hosts(
    action, custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([connector], {}),
    )

    apps, hosts = appcenter_umc_instance._validate_required_hosts(
        [connector], [], action, {primary: [connector.id], member: [connector.id]},
    )

    assert apps == [connector]
    assert hosts == {primary: [connector.id], member: [connector.id]}


def test_run_rejects_installing_same_app_on_multiple_hosts(
    custom_apps_umc, appcenter_umc_instance, mocked_ucr_appcenter, mocker,
):
    appcenter_module = sys.modules[appcenter_umc_instance.__class__.__module__]
    connector = custom_apps_umc.find('riot')
    primary = 'master.intranet.example.de'
    member = 'member.intranet.example.de'
    mocker.patch.object(
        appcenter_module,
        'resolve_domain_dependencies',
        return_value=([connector], {}),
    )

    with pytest.raises(appcenter_module.umcm.UMC_Error, match='exactly one target host'):
        appcenter_umc_instance._validate_required_hosts(
            [connector], [], 'install', {primary: [connector.id], member: [connector.id]},
        )
