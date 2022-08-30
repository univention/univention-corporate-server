#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2023 Univention GmbH
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

from logging import getLogger
from typing import Any, Mapping, Optional, Sequence  # noqa: F401

from univention.ldap_cache.cache import get_cache
from univention.listener.handler import ListenerModuleHandler


class LdapCacheHandler(ListenerModuleHandler):
    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        self._counter = 0
        super(LdapCacheHandler, self).__init__(*args, **kwargs)
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
