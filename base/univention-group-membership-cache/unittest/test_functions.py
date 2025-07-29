#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest
from univentionunittests import import_module


@pytest.fixture(scope="module")
def ldap_cache():
    module = import_module("univention.ldap_cache", "src/", "univention.ldap_cache", use_installed=False)
    return module

# mock the cache imported in the module


def test_groups_for_user(ldap_cache):
    """Test if groups_for_user() returns the correct groups."""
    groups_for_user = ldap_cache.groups_for_user
    groups = groups_for_user("cn=user,dc=example,dc=com")
    assert groups == ["cn=group1,dc=example,dc=com", "cn=group2,dc=example,dc=com"]


def test_users_in_group(ldap_cache):
    """Test if users_in_group() returns the correct users."""
    users_in_group = ldap_cache.users_in_group
    users = users_in_group("cn=group1,dc=example,dc=com")
    assert users == ["cn=user,dc=example,dc=com"]
