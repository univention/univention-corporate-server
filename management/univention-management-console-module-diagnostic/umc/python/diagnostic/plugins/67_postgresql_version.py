#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
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

import subprocess
from shutil import which
from typing import Tuple

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate


UCS = (5, 0)
POSTGRESQL_VERSION = (11,)
MIGRATION_URL = "https://help.univention.com/t/updating-from-postgresql-9-6-or-9-4-to-postgresql-11/17531"
title = _('Check currently installed PostgreSQL version')
description = _('''As of UCS {ucs[0]}.{ucs[1]}, PostgreSQL {postgresql_version[0]} should be used.
This step has to be performed manually as described in''').format(
    ucs=UCS, postgresql_version=POSTGRESQL_VERSION,
)

links = [
    {
        "name": "postgresql-migration",
        "href": MIGRATION_URL,
        "label": _("Updating from PostgreSQL 9.6 or 9.4 to PostgreSQL 11"),
    },
]
run_descr = [_('The migration status can be checked by executing: pg_lsclusters -h.')]


def warning(msg: str) -> Warning:
    text = "\n".join([msg, description])
    MODULE.error(text)
    return Warning(text, links=links)


def version_tuple_to_str(version: Tuple[int, ...]) -> str:
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
