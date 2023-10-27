#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
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

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate


UCS = (5, 0)
POSTGRESQL_VERSION = (11,)
MIGRATION_URL = "https://help.univention.com/t/updating-from-postgresql-9-6-or-9-4-to-postgresql-11/17531"
title = _('Check of the PostgreSQL version')
description = _('''Starting with UCS {ucs[0]}.{ucs[1]}, PostgreSQL should be version {postgresql_version}.
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
run_descr = ['The migration status can be checked by executing: pg_lsclusters -h.']


class PostgresWarning(Warning):

    def __init__(self, msg):
        super().__init__("\n".join([msg, description]), links=links)
        MODULE.error(str(self))


def version_tuple_to_str(version):
    return ".".join(str(v) for v in version)


def run(_umc_instance: Instance) -> None:
    if not which("pg_lsclusters"):
        return
    output = subprocess.check_output(["pg_lsclusters", "-h"]).decode("utf-8")
    versions = [
        (tuple(int(v) for v in ver.split(".")), status == "online")
        for ver, _cluster, _port, status, _owner, _data_dir, _log_file in (
            line.split(" ", 6) for line in output.splitlines()
        )
    ]
    if not versions:
        raise PostgresWarning(_("No PostgreSQL version found."))

    psql_version = max(versions)
    if psql_version[0] != POSTGRESQL_VERSION:
        raise PostgresWarning(_("PostgreSQL version is {current}, should be {desired}.").format(current=version_tuple_to_str(psql_version[0]), desired=version_tuple_to_str(POSTGRESQL_VERSION)))

    if not psql_version[1]:
        raise PostgresWarning(_("PostgreSQL version is up-to-date, but is not online."))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
