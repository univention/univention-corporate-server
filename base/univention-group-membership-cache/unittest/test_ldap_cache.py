#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest
from univentionunittests import import_module


@pytest.fixture(scope="module")
def ldap_membership_cache():
    module = import_module("univention.ldap_cache.membership_cache", "src/", "univention.ldap_cache.membership_cache", use_installed=False)
    return module

# mock the cache imported in the module


def test_relevant_for_group(ldap_membership_cache):
    """Test if there's relevant element in cache"""
    cache = ldap_membership_cache.MembershipCache()
    cache.add("cn=test,dc=ucs,dc=test", "cn=test,dc=ucs,dc=test")
    assert cache.relevant_for_group("cn=test,dc=ucs,dc=test") == ["cn=test,dc=ucs,dc=test"]


def test_update_user_cache():
    """Test if the cache is updated"""
    cache = ldap_membership_cache.MembershipCache()
    cache.update_user_cache("cn=test,dc=ucs,dc=test", ["cn=test,dc=ucs,dc=test"])
    assert cache.relevant_for_group("cn=test,dc=ucs,dc=test") == ["cn=test,dc=ucs,dc=test"]
