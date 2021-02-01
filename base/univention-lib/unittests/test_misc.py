#!/usr/bin/python2.7
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

import pytest

from .conftest import import_lib_module

misc = import_lib_module('misc')


@pytest.fixture
def lib_ucr(mocker, ucr):
	mock_config_registry = mocker.Mock(return_value=ucr)
	mocker.patch.object(misc, 'ConfigRegistry', mock_config_registry)
	return ucr


@pytest.fixture
def ucr0():
	"""
	Non-empty fake UCR.
	"""
	return {"key": "value"}


def test_username(ucr0):
	assert misc.custom_username('domain admin', ucr0) == 'domain admin'


def test_username_empty():
	with pytest.raises(ValueError):
		misc.custom_username('')


def test_username_custom(lib_ucr):
	lib_ucr['users/default/domainadmin'] = 'new_name'
	assert misc.custom_username('domain admin', lib_ucr) == 'new_name'
	assert misc.custom_username('domain admin') == 'new_name'


def test_groupname(ucr0):
	assert misc.custom_groupname('domain admins', ucr0) == 'domain admins'


def test_groupname_empty():
	with pytest.raises(ValueError):
		misc.custom_groupname('')


def test_groupname_custom(lib_ucr):
	lib_ucr['groups/default/domainadmins'] = 'new_name'
	assert misc.custom_groupname('domain admins', lib_ucr) == 'new_name'
	assert misc.custom_groupname('domain admins') == 'new_name'


def test_password(lib_ucr):
	lib_ucr['machine/password/length'] = '30'
	assert len(misc.createMachinePassword()) == 30


def test_ldap_uris(lib_ucr):
	lib_ucr['ldap/server/port'] = '6389'
	lib_ucr['ldap/server/name'] = 'ldap1.intranet.example.de'
	assert misc.getLDAPURIs(lib_ucr) == 'ldap://ldap1.intranet.example.de:6389'
	assert misc.getLDAPURIs() == 'ldap://ldap1.intranet.example.de:6389'
	lib_ucr['ldap/server/addition'] = 'ldap2.intranet.example.de ldap3.intranet.example.de'
	assert misc.getLDAPURIs() == 'ldap://ldap1.intranet.example.de:6389 ldap://ldap2.intranet.example.de:6389 ldap://ldap3.intranet.example.de:6389'


def test_ldap_servers(lib_ucr):
	lib_ucr['ldap/server/name'] = 'ldap1.intranet.example.de'
	lib_ucr['ldap/server/addition'] = 'ldap2.intranet.example.de ldap3.intranet.example.de'
	assert misc.getLDAPServersCommaList(lib_ucr) == 'ldap1.intranet.example.de,ldap2.intranet.example.de,ldap3.intranet.example.de'
	assert misc.getLDAPServersCommaList() == 'ldap1.intranet.example.de,ldap2.intranet.example.de,ldap3.intranet.example.de'
