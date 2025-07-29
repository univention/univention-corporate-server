#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate


UCS = (5, 2)
MIGRATION_URL = "https://help.univention.com/t/22821"
title = _('Checking Samba database type')
description = _('''As of UCS {ucs[0]}.{ucs[1]}, Samba should use mdb as for its database.
The steps to migrate the Samba database from tdb to mdb can be found in:''').format(ucs=UCS)

links = [
    {
        "name": "samba-mdb-migration",
        "href": MIGRATION_URL,
        "label": _("Migrate Samba database from tdb to mdb"),
    },
]


def warning(msg: str) -> Warning:
    text = f'{msg}\n{description}'
    MODULE.error(text)
    return Warning(text, links=links)


def version_tuple_to_str(version: tuple[int, ...]) -> str:
    return ".".join(str(v) for v in version)


def run(_umc_instance: Instance) -> None:
    if ucr.get('samba4/role', '') not in ['DC', 'RODC']:
        return
    if ucr.get('samba/database/backend/store', '') == 'tdb':
        raise warning(_("Deprecated Samba database type tdb."))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
