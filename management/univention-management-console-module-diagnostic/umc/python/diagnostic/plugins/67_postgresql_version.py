#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
from shutil import which

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate


UCS = (5, 2)
POSTGRESQL_VERSION = (15,)
MIGRATION_URL = "https://help.univention.com/t/updating-from-postgresql-11-to-postgresql-15/22162"
title = _('Check currently installed PostgreSQL version')
description = _('''As of UCS {ucs[0]}.{ucs[1]}, PostgreSQL {postgresql_version[0]} should be used.
This step has to be performed manually as described in''').format(
    ucs=UCS, postgresql_version=POSTGRESQL_VERSION,
)

links = [
    {
        "name": "postgresql-migration",
        "href": MIGRATION_URL,
        "label": _("Updating from PostgreSQL 11 to PostgreSQL 15"),
    },
]
run_descr = [_('The migration status can be checked by executing: pg_lsclusters -h.')]


def warning(msg: str) -> Warning:
    text = f'{msg}\n{description}'
    MODULE.error(text)
    return Warning(text, links=links)


def version_tuple_to_str(version: tuple[int, ...]) -> str:
    return ".".join(str(v) for v in version)


def run(_umc_instance: Instance) -> None:
    if not which("pg_lsclusters"):
        return
    output = subprocess.check_output(["pg_lsclusters", "-h"]).decode("utf-8")
    versions = [
        tuple(int(v) for v in ver.split("."))
        for ver, _cluster, _port, status, _owner, _data_dir, _log_file in (
            line.split(" ", 6) for line in output.splitlines()
        )
    ]
    if not versions:
        raise warning(_("No PostgreSQL version found."))

    psql_version = max(versions)
    if psql_version != POSTGRESQL_VERSION:
        raise warning(_("PostgreSQL version is {current}, should be {desired}.").format(current=version_tuple_to_str(psql_version), desired=version_tuple_to_str(POSTGRESQL_VERSION)))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
