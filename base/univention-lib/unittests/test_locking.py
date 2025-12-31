#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import subprocess
import sys

import pytest


@pytest.mark.xfail
@pytest.mark.parametrize('nonblocking', [True, False])
def test_locking(locking, nonblocking):
    lock = locking.get_lock('foo', nonblocking)
    try:
        assert os.path.exists('/var/run/foo.pid')
        assert int(open('/var/run/foo.pid').read().strip()) == os.getpid()
        assert subprocess.check_output([sys.executable, '-c', "from univention.lib import locking; print(locking.get_lock('foo', %r))" % (nonblocking,)], shell=True) == b'False'
        locking.release_lock(lock)
    finally:
        os.unlink('/var/run/foo.pid')
