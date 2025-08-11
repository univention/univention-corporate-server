#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Common Python Library for file locking"""


import fcntl
import os
from typing import IO, Optional  # noqa: F401


def get_lock(name, nonblocking=False):
    # type: (str, bool) -> Optional[IO[str]]
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
    fn = "/var/run/%s.pid" % name
    fd = open(fn, 'w')
    try:
        if nonblocking:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            fcntl.lockf(fd, fcntl.LOCK_EX)
    except OSError as e:
        if e.errno == 11:
            return None
        raise
    fd.write('%s\n' % os.getpid())
    fd.flush()
    return fd


def release_lock(fd):
    # type: (IO[str]) -> None
    """
    Releases the previously gained lock.

    :param file fd: The file descriptor of the lock file.
    """
    fcntl.lockf(fd, fcntl.LOCK_UN)
    fd.close()
