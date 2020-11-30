# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  listener script
#
# Copyright 2004-2021 Univention GmbH
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

import os
from contextlib import contextmanager
from functools import wraps
from pwd import getpwnam
from six import string_types
from univention.config_registry import ConfigRegistry
try:
	from typing import Any, Callable, List, Optional, Text, Type, TypeVar, Union  # noqa F401
	from types import TracebackType  # noqa F401

	_F = TypeVar("_F", bound=Callable[..., Any])
except ImportError:
	pass

configRegistry = ConfigRegistry()
configRegistry.load()

baseConfig = configRegistry


def setuid(uid):  # type: (Union[int, Text]) -> None
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
	if isinstance(uid, string_types):
		uid = getpwnam(uid)[2]
	os.seteuid(uid)


__listener_uid = -1


def unsetuid():  # type: () -> None
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


def run(exe, argv, uid=-1, wait=True):  # type: (str, List[Union[str, Text]], int, bool) -> int
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
		rc = os.spawnv(waitp, exe, argv)
	except:
		rc = 100
	finally:
		if uid > -1:
			setuid(olduid)

	return rc


class SetUID(object):
	"""
	Temporarily change effective UID to given user.

	:param int uid: Numeric user ID. Defaults to `root`.
	"""
	def __init__(self, uid=0):  # type: (int) -> None
		self.uid = uid if os.geteuid() != uid else -1

	def __enter__(self):  # type: () -> None
		if self.uid >= 0:
			setuid(self.uid)

	def __exit__(self, exc_type, exc_value, traceback):  # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		if self.uid >= 0:
			unsetuid()

	def __call__(self, f):  # type: (_F) -> Callable[[_F], _F]
		@wraps(f)
		def wrapper(*args, **kwargs):  # type: (*Any, **Any) -> Any
			with self:
				return f(*args, **kwargs)

		return wrapper
