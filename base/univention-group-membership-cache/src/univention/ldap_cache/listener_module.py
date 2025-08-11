#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Mapping, Sequence  # noqa: F401
from logging import getLogger

from univention.ldap_cache.cache import get_cache
from univention.listener.handler import ListenerModuleHandler


class LdapCacheHandler(ListenerModuleHandler):
    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        self._counter = 0
        super().__init__(*args, **kwargs)
        cache_logger = getLogger('univention.ldap_cache')
        cache_logger.setLevel(self.logger.level)
        for handler in self.logger.handlers:
            cache_logger.addHandler(handler)

    def _cleanup_cache_if_needed(self):
        # type: () -> None
        self._counter += 1
        if self._counter % 1000 == 0:
            for _name, db in get_cache():
                db.cleanup()

    def create(self, dn, new):
        # type: (str, Mapping[str, Sequence[bytes]]) -> None
        for shard in get_cache().get_shards_for_query(self.config.get_ldap_filter()):
            shard.add_object((dn, new))
        self._cleanup_cache_if_needed()

    def modify(self, dn, old, new, old_dn):
        # type: (str, Mapping[str, Sequence[bytes]], Mapping[str, Sequence[bytes]], Optional[str]) -> None
        for shard in get_cache().get_shards_for_query(self.config.get_ldap_filter()):
            shard.rm_object((old_dn or dn, old))
            shard.add_object((dn, new))
        self._cleanup_cache_if_needed()

    def remove(self, dn, old):
        # type: (str, Mapping[str, Sequence[bytes]]) -> None
        for shard in get_cache().get_shards_for_query(self.config.get_ldap_filter()):
            shard.rm_object((dn, old))
        self._cleanup_cache_if_needed()

    def post_run(self):
        # type: () -> None
        self._counter = -1
        self._cleanup_cache_if_needed()

    class Configuration(ListenerModuleHandler.Configuration):
        priority = 2.0
