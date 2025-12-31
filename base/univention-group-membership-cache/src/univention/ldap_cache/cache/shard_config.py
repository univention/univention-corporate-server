#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from univention.ldap_cache.cache import Shard
from univention.ldap_cache.log import log


if TYPE_CHECKING:
    from collections.abc import Iterator


CONFIG_FILE = '/usr/share/univention-group-membership-cache/shards.json'


def shards_from_config() -> list[type[Shard]]:
    ret: list[type[Shard]] = []
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
def _writing_config() -> Iterator[Any]:
    try:
        with open(CONFIG_FILE) as fd:
            shards = json.load(fd)
    except OSError:
        shards = []
    yield shards
    with open(CONFIG_FILE, 'w') as fd:
        json.dump(shards, fd, sort_keys=True, indent=4)


def add_shard_to_config(db_name: str, single_value: bool, reverse: bool, key: str, value: str, ldap_filter: str) -> None:
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


def rm_shard_from_config(db_name: str, single_value: bool, reverse: bool, key: str, value: str, ldap_filter: str) -> None:
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
