#!/usr/bin/python3
#
# Univention Updater
#  collect statistics
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import TYPE_CHECKING, Any, NoReturn

from univention.admin.license import _license
from univention.admin.uldap import access, getAdminConnection, position
from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update


if TYPE_CHECKING:
    from collections.abc import Callable


def encode_number(number: int, significant_digits: int = 3) -> str:
    assert 0 <= number <= int('9' * 26)
    assert significant_digits > 1
    string = str(number)
    return string[:significant_digits] + ' abcdefghijklmnopqrstuvwxyz'[len(string)]


def encode_users(users: int) -> str:
    return encode_number(users)


def encode_role(role: str) -> str:
    if role == 'domaincontroller_master':
        return 'M'
    if role == 'domaincontroller_backup':
        return 'B'
    if role == 'domaincontroller_slave':
        return 'S'
    if role == 'memberserver':
        return 'm'
    if role == 'basesystem':
        return 'b'
    raise ValueError('Invalid role %r' % (role, ))


def encode_additional_info(users: int | None = None, role: str | None = None) -> str:
    data: list[tuple[str, Callable[[Any], str], Any]] = [
        ('U', encode_users, users),
        ('R', encode_role, role),
    ]
    return ",".join(
        "%s:%s" % (key, encoder(datum))
        for key, encoder, datum in data
        if datum is not None
    )


def getReadonlyAdminConnection() -> tuple[access, position]:
    def do_nothing(*a: Any, **kw: Any) -> NoReturn:
        raise AssertionError('readonly connection')

    lo, position = getAdminConnection()
    lo.add = lo.modify = lo.rename = lo.delete = do_nothing
    return lo, position


def main() -> None:
    def get_role() -> str | None:
        return configRegistry.get('server/role', None)

    def get_users() -> int | None:
        if get_role() != 'domaincontroller_master':
            return None
        lo, _ = getReadonlyAdminConnection()
        filter = _license.filters['2'][_license.USERS]
        return len(lo.searchDn(filter=filter))

    configRegistry = ConfigRegistry()
    configRegistry.load()
    ucr_update(
        configRegistry,
        {
            'updater/statistics': encode_additional_info(users=get_users(), role=get_role()),
        },
    )


if __name__ == "__main__":
    main()
