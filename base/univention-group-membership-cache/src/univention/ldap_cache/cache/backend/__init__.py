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

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from univention.ldap_cache.log import debug


DB_DIRECTORY = '/usr/share/univention-group-membership-cache/caches'


class Caches:
    def __init__(self, db_directory: str = DB_DIRECTORY) -> None:
        self._directory = db_directory
        self._caches: dict[str, Any] = {}

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        yield from self._caches.items()

    def get_shards_for_query(self, query: str) -> list['Shard']:
        ret = []
        for cache in self._caches.values():
            for shard in cache.shards:
                if shard.ldap_filter == query:
                    ret.append(shard)
        return ret

    def get_sub_cache(self, name: str) -> Any:
        return self._caches.get(name)

    def add(self, klass: type) -> None:
        if not klass.ldap_filter or not klass.value:
            return
        debug('Adding %r', klass)
        name = klass.db_name or klass.__name__
        cache = self.get_sub_cache(name)
        if cache is None:
            cache = self._add_sub_cache(name, klass.single_value, klass.reverse)
        cache.add_shard(klass)

    def _add_sub_cache(self, name: str, single_value: bool, reverse: bool) -> Any:
        raise NotImplementedError()


class Shard:
    ldap_filter: str | None = None
    db_name: str | None = None
    single_value = False
    key = 'entryUUID'
    value: str | None = None
    attributes: list[str] = []
    reverse = False

    def __init__(self, cache: Any) -> None:
        self._cache = cache

    def rm_object(self, obj: tuple[str, Mapping[str, Sequence[bytes]]]) -> None:
        try:
            key = self.get_key(obj)
        except ValueError:
            return
        values = self.get_values(obj)
        debug('Removing %s', key)
        self._cache.delete(key, values)

    def add_object(self, obj: tuple[str, Mapping[str, Sequence[bytes]]]) -> None:
        try:
            key = self.get_key(obj)
        except ValueError:
            return
        debug('Adding %s', key)
        values = self.get_values(obj)
        if values:
            self._cache.save(key, values)
        else:
            self._cache.delete(key, [])

    def _get_from_object(self, obj: tuple[str, Mapping[str, Sequence[bytes]]], attr: str) -> Sequence[Any]:
        if attr == 'dn':
            return [obj[0]]
        return obj[1].get(attr, [])

    def get_values(self, obj: tuple[str, Mapping[str, Sequence[bytes]]]) -> Any:
        return _s(self._get_from_object(obj, self.value))

    def get_key(self, obj: tuple[str, Mapping[str, Sequence[bytes]]]) -> Any:
        values = self._get_from_object(obj, self.key)
        if values:
            return _s(values[0]).lower()
        raise ValueError(self.key)


class LdapCache:
    def __init__(self, name: str, single_value: bool, reverse: bool) -> None:
        self.name = name
        self.single_value = single_value
        self.reverse = reverse
        self.shards: list[Shard] = []

    def add_shard(self, shard_class: type[Shard]) -> None:
        self.shards.append(shard_class(self))


def _s(input: Any) -> Any:
    if isinstance(input, list | tuple):
        res: Any = []
        for n in input:
            if isinstance(n, bytes):
                res.append(n.decode('utf-8'))
            elif isinstance(list, tuple):
                res.append(_s(n))
            else:
                res.append(n)
    elif isinstance(input, bytes):
        res = input.decode('utf-8')
    else:
        res = input
    return res
