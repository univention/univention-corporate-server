#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


@pytest.fixture
def lib_ucr(misc, mocker, mock_ucr):
    mock_config_registry = mocker.Mock(return_value=mock_ucr)
    mocker.patch.object(misc, 'ConfigRegistry', mock_config_registry)
    return mock_ucr


@pytest.fixture
def ucr0():
    """Non-empty fake UCR."""
    return {"key": "value"}


def test_username(misc, ucr0):
    assert misc.custom_username('domain admin', ucr0) == 'domain admin'


def test_username_empty(misc):
    with pytest.raises(ValueError):
        misc.custom_username('')


def test_username_custom(misc, lib_ucr):
    lib_ucr['users/default/domainadmin'] = 'new_name'
    assert misc.custom_username('domain admin', lib_ucr) == 'new_name'
    assert misc.custom_username('domain admin') == 'new_name'


def test_groupname(misc, ucr0):
    assert misc.custom_groupname('domain admins', ucr0) == 'domain admins'


def test_groupname_empty(misc):
    with pytest.raises(ValueError):
        misc.custom_groupname('')


def test_groupname_custom(misc, lib_ucr):
    lib_ucr['groups/default/domainadmins'] = 'new_name'
    assert misc.custom_groupname('domain admins', lib_ucr) == 'new_name'
    assert misc.custom_groupname('domain admins') == 'new_name'


def test_password(misc, lib_ucr):
    lib_ucr['machine/password/length'] = '30'
    assert len(misc.createMachinePassword()) == 30


def test_ldap_uris(misc, lib_ucr):
    lib_ucr['ldap/server/port'] = '6389'
    lib_ucr['ldap/server/name'] = 'ldap1.intranet.example.de'
    assert misc.getLDAPURIs(lib_ucr) == 'ldap://ldap1.intranet.example.de:6389'
    assert misc.getLDAPURIs() == 'ldap://ldap1.intranet.example.de:6389'
    lib_ucr['ldap/server/addition'] = 'ldap2.intranet.example.de ldap3.intranet.example.de'
    assert misc.getLDAPURIs() == 'ldap://ldap1.intranet.example.de:6389 ldap://ldap2.intranet.example.de:6389 ldap://ldap3.intranet.example.de:6389'


def test_ldap_servers(misc, lib_ucr):
    lib_ucr['ldap/server/name'] = 'ldap1.intranet.example.de'
    lib_ucr['ldap/server/addition'] = 'ldap2.intranet.example.de ldap3.intranet.example.de'
    assert misc.getLDAPServersCommaList(lib_ucr) == 'ldap1.intranet.example.de,ldap2.intranet.example.de,ldap3.intranet.example.de'
    assert misc.getLDAPServersCommaList() == 'ldap1.intranet.example.de,ldap2.intranet.example.de,ldap3.intranet.example.de'
