#
# Univention Directory Listener
#  listener script
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from collections.abc import Callable
from functools import wraps
from pwd import getpwnam
from types import TracebackType
from typing import Any, TypeVar

from univention.config_registry import ConfigRegistry


_F = TypeVar("_F", bound=Callable[..., Any])

configRegistry = ConfigRegistry()
configRegistry.load()


def setuid(uid: int | str) -> None:
    """
    Set the current process’s effective user id.
    Use :py:func:`unsetuid()` to return to the listeners UID.

    When used with any other user than `root`. Be aware that
    :py:func:`listener.unsetuid()` will *not* be possible afterwards, as that
    requires root privileges.

    :param uid: UID the process should have
    :type uid: int or str
    :return: None
    """
    if isinstance(uid, str):
        uid = getpwnam(uid)[2]
    assert isinstance(uid, int)
    os.seteuid(uid)


__listener_uid = -1


def unsetuid() -> None:
    """
    Return the current process’s effective user id to the listeners UID.
    Only possible if the current effective user id is `root`.

    :return: None
    """
    global __listener_uid
    if __listener_uid == -1:
        try:
            __listener_uid = getpwnam('listener')[2]
        except KeyError:
            __listener_uid = 0
    os.seteuid(__listener_uid)


def run(exe: str, argv: list[str], uid: int = -1, wait: bool = True) -> int:
    """
    Execute a the program `exe` with arguments `argv` and effective user id
    `uid`.

    :param str exe: path to executable
    :param argv: arguments to pass to executable
    :type argv: list(str)
    :param int uid: effective user id the process should be started with
    :param bool wait: if true will block until the process has finished and return either its exit code or the signal that lead to its stop (a negative number), see :py:const:`os.P_WAIT`. If false will return as soon as the new process has been created, with the process id as the return value (see :py:const:`os.P_NOWAIT`).
    :return: exit code or signal number or process id
    :rtype: int

    .. warning::
       Not waiting for the sub-process leads to zombie processes.
    """
    if uid > -1:
        olduid = os.getuid()
        setuid(uid)

    waitp = os.P_WAIT if wait else os.P_NOWAIT
    try:
        rc = os.spawnv(waitp, exe, argv)  # noqa: S606
    except BaseException:
        rc = 100
    finally:
        if uid > -1:
            setuid(olduid)

    return rc


class SetUID:
    """
    Temporarily change effective UID to given user.

    :param int uid: Numeric user ID. Defaults to `root`.
    """

    def __init__(self, uid: int = 0) -> None:
        self.uid = uid if os.geteuid() != uid else -1

    def __enter__(self) -> None:
        if self.uid >= 0:
            setuid(self.uid)

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        if self.uid >= 0:
            unsetuid()

    def __call__(self, f: _F) -> Callable[[_F], _F]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return f(*args, **kwargs)

        return wrapper
