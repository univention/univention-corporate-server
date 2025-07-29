#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
from shutil import which

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate


DEFRAGMENTATION_ARTICLE_URL = "https://help.univention.com/t/24105"
title = _('Check fragmentation of LMDB databases')
description = _('''
LMDB (https://www.symas.com/mdb) is a key value store with B+-tree structure and MVCC.
During normal oparation, the on disk file may get fragmented and it can be beneficial
for performance to defragment the file by running "mdb_copy -c".
This step has to be performed manually as described in''')

links = [
    {
        "name": "lmdb-defragmentation",
        "href": DEFRAGMENTATION_ARTICLE_URL,
        "label": _("Defragmentation of LMDB databases"),
    },
]
# run_descr = [_('The migration status can be checked by executing: pg_lsclusters -h.')]


def warning(msg: str) -> Warning:
    text = f'{msg}\n{description}'
    MODULE.error(text)
    return Warning(text, links=links)


def run(_umc_instance: Instance) -> None:
    if not which("univention-lmdb-fragmentation"):
        msg = "univention-lmdb-fragmentation not found"
        MODULE.error(msg)
        raise Warning(msg, links=[])

    error_descriptions = []
    try:
        subprocess.check_output(["univention-lmdb-fragmentation"])
    except subprocess.CalledProcessError as exc:
        error_descriptions.extend(exc.output.decode("utf-8").splitlines())

    if error_descriptions:
        raise warning(_("LMDB fragmentation above threshold.") + "\n" + "\n".join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
