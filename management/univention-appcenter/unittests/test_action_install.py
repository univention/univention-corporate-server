#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


ANYTHING = object()


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


def test_install_two_apps(get_action, custom_apps, mocked_ucr_appcenter, mocker):
    custom_apps.load('unittests/inis/dependencies')
    app1 = custom_apps.find('self-service')
    app2 = custom_apps.find('kopano-webapp')
    app3 = custom_apps.find('self-service-backend')
    app4 = custom_apps.find('kopano-core')
    for app in [app1, app2, app3, app4]:
        mocker.patch.object(app, 'is_installed', return_value=False)
    install = get_action('install')
    mock_do_it = mocker.patch.object(install, '_do_it')
    mock_send_information = mocker.patch.object(install, '_send_information')
    install.call(app=[app1, app2], noninteractive=True)
    assert_called_with(mock_send_information, ([app3, 200, None], {}), ([app1, 200, None], {}), ([app4, 200, None], {}), ([app2, 200, None], {}))
    assert_called_with(mock_do_it, ([app3, ANYTHING], {}), ([app1, ANYTHING], {}), ([app4, ANYTHING], {}), ([app2, ANYTHING], {}))
