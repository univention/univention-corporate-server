# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import shutil


CUR = '/etc/apt/mirror.list'
BAK = CUR + '.old'


def preinst(ucr, changes):
    if os.path.exists(BAK):
        os.remove(BAK)

    if os.path.exists(CUR):
        shutil.copy2(CUR, BAK)

    if 'local/repository' in changes:
        """Immediately resolve pending policy changes if local/repository is changed (Bug #16646)"""
        os.system('/usr/lib/univention-directory-policy/univention-policy-set-repository-server >>/var/log/univention/repository.log')  # noqa: S605


def postinst(ucr, changes):
    if not os.path.exists(CUR):
        return

    res = open(CUR).readlines()
    if len(res) <= 1 and os.path.exists(BAK):
        os.rename(BAK, CUR)

    if os.path.exists(BAK):
        os.remove(BAK)
