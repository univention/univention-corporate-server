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

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate


UCS = (5, 2)
MIGRATION_URL = "https://help.univention.com/t/pre-update-checks-for-ucs-5-0-0-aborts-warning-about-a-very-large-samba-tdb-database/18014"
title = _('Checking samba database type')
description = _('''As of UCS {ucs[0]}.{ucs[1]}, samba should use mdb as for its database.
The steps to migrate the samba database from tdb to mdb can be found in:''').format(ucs=UCS)

links = [
    {
        "name": "samba-mdb-migration",
        "href": MIGRATION_URL,
        "label": _("Migrate samba database from tdb to mdb"),
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
        raise warning(_("Deprecated samba database type tdb."))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
