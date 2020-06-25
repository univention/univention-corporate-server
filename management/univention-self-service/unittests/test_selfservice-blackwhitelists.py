#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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


from univention.unittests.umc import import_umc_module

import pytest

selfservice = import_umc_module('passwordreset')


@pytest.fixture
def ldap_database_file():
	return 'unittests/selfservice.ldif'


@pytest.fixture
def blacklist_ucr(mocker, ucr):
	ucr['umc/self-service/account-deregistration/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/account-deregistration/blacklist/users'] = ''
	ucr['umc/self-service/account-deregistration/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/account-deregistration/whitelist/users'] = ''
	ucr['umc/self-service/passwordreset/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/passwordreset/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/profiledata/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/profiledata/blacklist/users'] = ''
	ucr['umc/self-service/profiledata/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/profiledata/whitelist/users'] = ''
	mocker.patch.object(selfservice, 'ucr', ucr)
	return ucr


@pytest.fixture
def mocked_conn(mocker, lo, pos):
	mocker.patch.object(selfservice, 'get_admin_connection', return_value=[lo, pos])
	mocker.patch.object(selfservice, 'get_machine_connection', return_value=[lo, pos])
	import univention.management.console.ldap as umc_ldap
	mocker.patch.object(umc_ldap, '_getMachineConnection', return_value=[lo, pos])
	mocker.patch.object(umc_ldap, '_getAdminConnection', return_value=[lo, pos])


def test_blacklist_user_match(instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampp'
	assert instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_user_nomatch(instance, blacklist_ucr):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampf'
	assert not instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match(instance, blacklist_ucr):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group1'
	assert instance.is_blacklisted('hinderkampp', feature)


@pytest.fixture
def test_blacklist_group_nomatch(instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group0'
	assert not instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match_nested(instance, blacklist_ucr):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group2'
	assert instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_whitelist_precedence(instance, blacklist_ucr):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/whitelist/groups'.format(feature)] = 'selfservice-group1'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'Administrators,Domain Admins,selfservice-group2'
	assert instance.is_blacklisted('hinderkampp', feature)
