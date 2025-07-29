#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from collections.abc import Iterator  # noqa: F401
from contextlib import contextmanager

from univention.ldap_cache.cache import Shard
from univention.ldap_cache.log import log


CONFIG_FILE = '/usr/share/univention-group-membership-cache/shards.json'


def shards_from_config():
    # type: () -> List[Type[Shard]]
    ret = []  # type: List[Type[Shard]]
    try:
        with open(CONFIG_FILE) as fd:
            config = json.load(fd)
    except (OSError, ValueError) as exc:
        log('Could not load CONFIG_FILE: %s', exc)
    else:
        for data in config:
            try:
                class FromConfig(Shard):
                    db_name = data['db_name']
                    single_value = data['single_value']
                    reverse = data.get('reverse', False)
                    key = data['key']
                    value = data['value']
                    ldap_filter = data['ldap_filter']
                ret.append(FromConfig)
            except (TypeError, KeyError) as exc:
                log('JSON wrong: %s', exc)
    return ret


@contextmanager
def _writing_config():
    # type: () -> Iterator[Any]
    try:
        with open(CONFIG_FILE) as fd:
            shards = json.load(fd)
    except OSError:
        shards = []
    yield shards
    with open(CONFIG_FILE, 'w') as fd:
        json.dump(shards, fd, sort_keys=True, indent=4)


def add_shard_to_config(db_name, single_value, reverse, key, value, ldap_filter):
    # type: (str, bool, bool, str, str, str) -> None
    with _writing_config() as shards:
        shard_config = {
            'db_name': db_name,
            'single_value': single_value and not reverse,
            'reverse': reverse,
            'key': key,
            'value': value,
            'ldap_filter': ldap_filter,
        }
        if shard_config not in shards:
            shards.append(shard_config)


def rm_shard_from_config(db_name, single_value, reverse, key, value, ldap_filter):
    # type: (str, bool, bool, str, str, str) -> None
    with _writing_config() as shards:
        try:
            shards.remove({
                'db_name': db_name,
                'single_value': single_value and not reverse,
                'reverse': reverse,
                'key': key,
                'value': value,
                'ldap_filter': ldap_filter,
            })
        except ValueError:
            pass
