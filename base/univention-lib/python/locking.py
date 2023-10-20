#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2023 Univention GmbH
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

"""Univention Common Python Library for file locking"""

from __future__ import print_function

import fcntl
import os
from typing import IO, Optional  # noqa: F401


def get_lock(name: str, nonblocking: bool=False) -> "Optional[IO[str]]":
    """
    Get a exclusive lock.

    :param str name: The name for the lock file.
    :param bool nonblocking: Return `None` instead of waiting indefinitely to get the exclusive lock if the lock is already taken.

    :returns: a file descriptor for a lock file after the file has been locked exclusively. In non-blocking mode `None` is returned if the lock cannot be gained.
    :rtype: file or None

    The returned file descriptor has to be kept. Otherwise the lock will
    be release automatically on file descriptor's destruction.

    >>> fd = get_lock('myapp')
    >>> # ...... do some critical stuff ......
    >>> release_lock(fd)
    >>>
    >>> fd = get_lock('myapp', nonblocking=True)
    >>> if not fd:
    >>>     print('cannot get lock')
    >>> else:
    >>>     # ...... do some critical stuff ......
    >>>     release_lock(fd)
    """
    fn = f"/var/run/{name}.pid"
    fd = open(fn, 'w')
    try:
        if nonblocking:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            fcntl.lockf(fd, fcntl.LOCK_EX)
    except IOError as e:
        if e.errno == 11:
            return None
        raise
    fd.write(f'{os.getpid()}\n')
    fd.flush()
    return fd


def release_lock(fd: "IO[str]") -> None:
    """
    Releases the previously gained lock.

    :param file fd: The file descriptor of the lock file.
    """
    fcntl.lockf(fd, fcntl.LOCK_UN)
    fd.close()
