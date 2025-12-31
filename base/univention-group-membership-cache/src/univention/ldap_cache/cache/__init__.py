#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# choose a backend
from univention.ldap_cache.cache.backend.gdbm_cache import (  # noqa: F401
    GdbmCache as Cache, GdbmCaches as Caches, GdbmShard as Shard,
)
from univention.ldap_cache.cache.shard_config import shards_from_config
from univention.ldap_cache.log import debug


# from univention.ldap_cache.cache.backend.lmdb_cache import LmdbCaches as Caches, LmdbCache as Cache, LmdbShard as Shard


# Singleton pattern
def get_cache() -> Caches:
    global _cache
    if _cache is None:
        debug('Creating the Caches instance')
        caches = Caches()
        for klass in shards_from_config():
            caches.add(klass)
        _cache = caches
    return _cache


_cache: Caches | None = None
