#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention Updater locking
"""
# Copyright 2008-2019 Univention GmbH
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

from __future__ import absolute_import
from __future__ import print_function

import os
from sys import (exit, stderr)
from time import (time, sleep)
from errno import (EEXIST, ESRCH, ENOENT)
from .errors import LockingError


class UpdaterLock(object):
    """
    Context wrapper for updater-lock :file:`/var/lock/univention-updater`.
    """

    __UPDATER_LOCK_FILE_NAME = '/var/lock/univention-updater'

    def __init__(self, timeout=0):
        self.timeout = timeout
        self.lock = 0

    def __enter__(self):
        try:
            self.lock = self.updater_lock_acquire()
        except LockingError as ex:
            print(ex, file=stderr)
            exit(5)

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.updater_lock_release():
            print('WARNING: updater-lock already released!', file=stderr)

    def updater_lock_acquire(self):
        '''
        Acquire the updater-lock.

        :returns: 0 if it could be acquired within <timeout> seconds, >= 1 if locked by parent.
        :rtype: int
        :raises LockingError: otherwise.
        '''
        deadline = time() + self.timeout
        my_pid = "%d\n" % os.getpid()
        parent_pid = "%d\n" % os.getppid()
        while True:
            try:
                lock_fd = os.open(
                    self.__UPDATER_LOCK_FILE_NAME,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o644)
                bytes_written = os.write(lock_fd, my_pid)
                assert bytes_written == len(my_pid)
                os.close(lock_fd)
                return 0
            except OSError as ex:
                if ex.errno != EEXIST:
                    raise
                try:
                    lock_fd = os.open(
                        self.__UPDATER_LOCK_FILE_NAME,
                        os.O_RDONLY | os.O_EXCL)
                    try:
                        lock_pid = os.read(
                            lock_fd, 11)  # sizeof(s32) + len('\n')
                    finally:
                        os.close(lock_fd)
                    if my_pid == lock_pid:
                        return 0
                    if parent_pid == lock_pid:  # u-repository-* called from u-updater
                        return 1
                    try:
                        lock_pid = lock_pid.strip() or '?'
                        lock_pid = int(lock_pid)
                        os.kill(lock_pid, 0)
                    except ValueError:
                        msg = 'Invalid PID %s in lockfile %s.' % (
                            lock_pid,
                            self.__UPDATER_LOCK_FILE_NAME,
                        )
                        raise LockingError(msg)
                    except OSError as ex:
                        if ex.errno == ESRCH:
                            print('Stale PID %s in lockfile %s, removing.' % (
                                lock_pid,
                                self.__UPDATER_LOCK_FILE_NAME,
                            ), file=stderr)
                            os.remove(self.__UPDATER_LOCK_FILE_NAME)
                            continue  # redo acquire
                    # PID is valid and process is still alive...
                except OSError:
                    pass
                if time() > deadline:
                    if self.timeout > 0:
                        msg = 'Timeout: still locked by PID %s. Check lockfile %s' % (
                            lock_pid,
                            self.__UPDATER_LOCK_FILE_NAME,
                        )
                    else:
                        msg = 'Locked by PID %s. Check lockfile %s' % (
                            lock_pid or '?',
                            self.__UPDATER_LOCK_FILE_NAME,
                        )
                    raise LockingError(msg)
                else:
                    sleep(1)

    def updater_lock_release(self):
        '''
        Release the updater-lock.

        :returns: True if it has been unlocked (or decremented when nested), False if it was already unlocked.
        :rtype: bool
        '''
        if self.lock > 0:
            # parent process still owns the lock, do nothing and just return success
            return True
        try:
            os.remove(self.__UPDATER_LOCK_FILE_NAME)
            return True
        except OSError as error:
            if error.errno == ENOENT:
                return False
            else:
                raise


if __name__ == '__main__':
    import doctest
    exit(doctest.testmod()[0])
