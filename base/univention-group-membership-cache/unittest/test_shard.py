#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest
from univentionunittests import import_module


@pytest.fixture(scope="module")
def ldap_cache():
    module = import_module("univention.ldap_cache.cache", "src/", "univention.ldap_cache.cache", use_installed=False)
    return module


def test_init_shard(ldap_cache):
    # TODO: Finish this test
    caches = ldap_cache.LmdbCaches()
    cache0 = caches.add_cache_class(ldap_cache.EntryUUID)
    cache0.add_shard(ldap_cache.UserEntryUUIDShard)
    cache0.add_shard(ldap_cache.GroupEntryUUIDShard)
    # cache1 = caches.add_full_shard(UsersInGroup)
    # cache2 = caches.add_full_shard(GroupsInGroup)
