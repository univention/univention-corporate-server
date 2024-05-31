#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2024 Univention GmbH
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

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

from univention.ldap_cache.cache import get_cache
from univention.ldap_cache.frontend import _extract_id_from_dn
from univention.provisioning.consumer import AsyncClient, MessageHandler, Settings
from univention.provisioning.models import Message


class CacheConsumer:
    def __init__(self):
        self._counter = 0
        self._filter = "(univentionObjectType=groups/group)"
        self._logger = logging.getLogger('univention.ldap_cache')
        self._logger.setLevel(logging.INFO)  # FIXME: do not hardcode log level

    def _cleanup_cache_if_needed(self):
        # type: () -> None
        self._counter += 1
        if self._counter % 1000 == 0:
            for _name, db in get_cache():
                db.cleanup()

    @staticmethod
    def _map_udm_into_ldap(obj: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        """Partial mapping of a UDM object into an LDAP object for the univention-group-membership-member cache."""
        if obj is None:
            return None

        properties = obj.get("properties", {})
        users = properties.get("users", [])
        hosts = properties.get("hosts", [])
        nested_groups = properties.get("nestedGroup", [])

        ldap_obj = {
            "dn": obj["dn"],
            "uniqueMember": users + hosts + nested_groups,
            "memberUid": [_extract_id_from_dn(user_dn) for user_dn in users],
        }
        return ldap_obj

    async def start_listening_for_changes(self) -> None:
        settings = Settings()

        self._logger.info("Listening for changes in the groups for the univention-group-membership-member cache")
        async with AsyncClient() as client:
            await MessageHandler(
                client, settings.provisioning_api_username, [self.handle_message],
            ).run()

    async def handle_message(self, message: Message):
        body = message.body
        self._logger.info("Received the message with the body: %s", body)

        new_obj = self._map_udm_into_ldap(body.get("new"))
        old_obj = self._map_udm_into_ldap(body.get("old"))

        if old_obj and new_obj:
            self.modify(old_obj, new_obj)
        elif old_obj:
            self.remove(old_obj)
        else:
            self.create(new_obj)
        self._cleanup_cache_if_needed()

    def create(self, new: Mapping[str, Any]):
        for shard in get_cache().get_shards_for_query(self._filter):
            shard.add_object((new["dn"], new))

    def modify(self, old: Mapping[str, Any], new: Mapping[str, Any]):
        for shard in get_cache().get_shards_for_query(self._filter):
            shard.rm_object((old["dn"], old))
            shard.add_object((new["dn"], new))

    def remove(self, old: Mapping[str, Any]):
        for shard in get_cache().get_shards_for_query(self._filter):
            shard.rm_object((old["dn"], old))


def run() -> None:
    consumer = CacheConsumer()
    asyncio.run(consumer.start_listening_for_changes())


if __name__ == "__main__":
    run()
