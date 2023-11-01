#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple, Type, Union  # noqa: F401

from univention.ldap_cache.log import debug


DB_DIRECTORY = '/usr/share/univention-group-membership-cache/caches'


class Caches(object):
    def __init__(self, db_directory=DB_DIRECTORY):
        # type: (str) -> None
        self._directory = db_directory
        self._caches = {}  # type: Dict[str, Any]

    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Any]]
        yield from self._caches.items()

    def get_shards_for_query(self, query):
        # type: (str) -> List[Shard]
        ret = []
        for cache in self._caches.values():
            for shard in cache.shards:
                if shard.ldap_filter == query:
                    ret.append(shard)
        return ret

    def get_sub_cache(self, name):
        # type: (str) -> Any
        return self._caches.get(name)

    def add(self, klass):
        # type: (Type) -> None
        if not klass.ldap_filter or not klass.value:
            return
        debug('Adding %r', klass)
        name = klass.db_name or klass.__name__
        cache = self.get_sub_cache(name)
        if cache is None:
            cache = self._add_sub_cache(name, klass.single_value, klass.reverse)
        cache.add_shard(klass)

    def _add_sub_cache(self, name, single_value, reverse):
        # type: (str, bool, bool) -> Any
        raise NotImplementedError()


class Shard(object):
    ldap_filter = None  # type: Optional[str]
    db_name = None  # type: Optional[str]
    single_value = False
    key = 'entryUUID'
    value = None  # type: Optional[str]
    attributes = []  # type: List[str]
    reverse = False

    def __init__(self, cache):
        # type: (Any) -> None
        self._cache = cache

    def rm_object(self, obj):
        # type: (Tuple[str, Mapping[str, Sequence[bytes]]]) -> None
        try:
            key = self.get_key(obj)
        except ValueError:
            return
        values = self.get_values(obj)
        debug('Removing %s', key)
        self._cache.delete(key, values)

    def add_object(self, obj):
        # type: (Tuple[str, Mapping[str, Sequence[bytes]]]) -> None
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

    def _get_from_object(self, obj, attr):
        # type: (Tuple[str, Mapping[str, Sequence[bytes]]], str) -> Sequence[Any]
        if attr == 'dn':
            return [obj[0]]
        return obj[1].get(attr, [])

    def get_values(self, obj):
        # type: (Tuple[str, Mapping[str, Sequence[bytes]]]) -> Any
        return _s(self._get_from_object(obj, self.value))

    def get_key(self, obj):
        # type: (Tuple[str, Mapping[str, Sequence[bytes]]]) -> Any
        values = self._get_from_object(obj, self.key)
        if values:
            return _s(values[0]).lower()
        raise ValueError(self.key)


class LdapCache(object):
    def __init__(self, name, single_value, reverse):
        # type: (str, bool, bool) -> None
        self.name = name
        self.single_value = single_value
        self.reverse = reverse
        self.shards = []  # type: List[Shard]

    def add_shard(self, shard_class):
        # type: (Type[Shard]) -> None
        self.shards.append(shard_class(self))


def _s(input):
    # type: (Any) -> Any
    if isinstance(input, (list, tuple)):
        res = []  # type: Any
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
