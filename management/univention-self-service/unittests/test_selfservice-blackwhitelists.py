#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.


from univentionunittests.umc import import_umc_module

import pytest

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
	blacklist_ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampp'
	assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_user_nomatch(selfservice_instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampf'
	assert not selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match(selfservice_instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group1'
	assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_nomatch(selfservice_instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group0'
	assert not selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match_nested(selfservice_instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group2'
	assert selfservice_instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_whitelist_precedence(selfservice_instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/whitelist/groups'.format(feature)] = 'selfservice-group1'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'Administrators,Domain Admins,selfservice-group2'
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
