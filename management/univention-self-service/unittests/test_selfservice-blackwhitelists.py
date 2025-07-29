#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import pytest
from univentionunittests.umc import import_umc_module


selfservice = import_umc_module('passwordreset')


@pytest.fixture
def ldap_database_file():
    return 'unittests/selfservice.ldif'


@pytest.fixture
def blacklist_ucr(selfservice_ucr):
    selfservice_ucr['umc/self-service/account-deregistration/blacklist/groups'] = 'Administrators,Domain Admins'
    selfservice_ucr['umc/self-service/account-deregistration/blacklist/users'] = ''
    selfservice_ucr['umc/self-service/account-deregistration/whitelist/groups'] = 'Domain Users'
    selfservice_ucr['umc/self-service/account-deregistration/whitelist/users'] = ''
    selfservice_ucr['umc/self-service/passwordreset/blacklist/groups'] = 'Administrators,Domain Admins'
    selfservice_ucr['umc/self-service/passwordreset/whitelist/groups'] = 'Domain Users'
    selfservice_ucr['umc/self-service/profiledata/blacklist/groups'] = 'Administrators,Domain Admins'
    selfservice_ucr['umc/self-service/profiledata/blacklist/users'] = ''
    selfservice_ucr['umc/self-service/profiledata/whitelist/groups'] = 'Domain Users'
    selfservice_ucr['umc/self-service/profiledata/whitelist/users'] = ''
    return selfservice_ucr


def test_blacklist_user_match(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/users'] = 'hinderkampp'
    assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_user_nomatch(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/users'] = 'hinderkampf'
    assert not selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/groups'] = 'selfservice-group1'
    assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_nomatch(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/groups'] = 'selfservice-group0'
    assert not selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match_nested(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/groups'] = 'selfservice-group2'
    assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_whitelist_precedence(selfservice_instance, blacklist_ucr, mocked_conn):
    feature = 'passwordreset'
    blacklist_ucr[f'umc/self-service/{feature}/whitelist/groups'] = 'selfservice-group1'
    blacklist_ucr[f'umc/self-service/{feature}/blacklist/groups'] = 'Administrators,Domain Admins,selfservice-group2'
    assert selfservice_instance.is_blacklisted('hinderkampp', feature)


@pytest.mark.parametrize("ucrs,command,command_options,feature,expected_traceback", [
    ([('umc/self-service/protect-account/backend/enabled', 'true')], 'get_contact', {}, 'passwordreset', selfservice.ServiceForbidden),
    ([('umc/self-service/protect-account/backend/enabled', 'true')], 'set_contact', {}, 'passwordreset', selfservice.ServiceForbidden),
    ([('umc/self-service/passwordreset/backend/enabled', 'true')], 'send_token', {"method": "email"}, 'passwordreset', selfservice.MissingContactInformation),
    ([('umc/self-service/passwordreset/backend/enabled', 'true')], 'get_reset_methods', {}, 'passwordreset', selfservice.NoMethodsAvailable),
    ([], 'set_password', {"token": "xxx"}, 'passwordreset', selfservice.ServiceForbidden),
    ([], 'get_user_attributes', {}, 'profiledata', selfservice.ServiceForbidden),
    ([], 'set_user_attributes', {"attributes": {}}, 'profiledata', selfservice.ServiceForbidden),
    ([], 'validate_user_attributes', {"attributes": {}}, 'profiledata', selfservice.ServiceForbidden),
    ([('umc/self-service/account-deregistration/enabled', 'true')], 'deregister_account', {}, 'account-deregistration', selfservice.ServiceForbidden),
])
def test_correct_feature_for_umc_command(blacklist_ucr, selfservice_instance, mocked_conn, umc_request, mocker, ucrs, command, command_options, feature, expected_traceback):
    username = 'hinderkampppp'
    mocker.patch.object(selfservice_instance, 'auth', return_value=(None, username))
    mocker.patch.object(selfservice_instance, '_check_token', return_value=True)

    for (key, value) in ucrs:
        blacklist_ucr[key] = value
    is_blacklisted = mocker.patch.object(selfservice_instance, 'is_blacklisted', return_value=True)
    umc_request.options = {"username": username, "password": "univention"}
    umc_request.options.update(command_options)
    with pytest.raises(expected_traceback):
        getattr(selfservice_instance, command)(umc_request)
    is_blacklisted.assert_called_with(username, feature)
