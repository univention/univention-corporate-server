# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2004-2023 Univention GmbH

import os
import time

lockfile = '/var/lock/univention-lilo'


def lock():
    if os.path.exists(lockfile):
        return False
    os.system(f'touch {lockfile}')
    return True


def lilo():
    time.sleep(2)
    os.system('/sbin/lilo')


def unlock():
    os.remove(lockfile)


def handler(baseConfig, changes):
    rc = lock()
    if not rc:
        return False
    if baseConfig.get('lilo/boot') and baseConfig.get('lilo/root'):
        lilo()
    unlock()
