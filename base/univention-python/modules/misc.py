# -*- coding: utf-8 -*-
#
# Univention Python
#  miscellaneous utilities
#
# Copyright 2002-2019 Univention GmbH
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

import platform
import os
import resource


def filemax_global():
	"""
	Get maximum number of files the kernel can open.

	>>> filemax_global() #doctest: +ELLIPSIS
	...
	"""
	f = open('/proc/sys/fs/file-max', 'r')
	try:
		s = f.read()
		return int(s[:-1])
	finally:
		f.close()


def filemax():
	"""
	Get maximum number of files a process can open.

	>>> filemax() #doctest: +ELLIPSIS
	...
	"""
	return resource.getrlimit(resource.RLIMIT_NOFILE)[1]


def close_fds():
	"""
	Close all open file descriptors and open /dev/null as stdin, stdout, and stderr.

	>>> close_fds()
	"""
	if platform.system() == 'Linux':
		fds = map(int, os.listdir('/proc/%d/fd' % os.getpid()))
	else:
		fds = xrange(0, filemax())
	for i in fds:
		try:
			os.close(i)
		except OSError:
			pass
	assert 0 == os.open(os.path.devnull, os.O_RDONLY)
	assert 1 == os.open(os.path.devnull, os.O_WRONLY)
	assert 2 == os.open(os.path.devnull, os.O_WRONLY)


def close_fd_spawn(file, args):
	"""
	Close all open file descriptors before doing execv().

	>>> close_fd_spawn("/bin/bash", ["bash", "-c", "exit `find /proc/$$/fd -mindepth 1 -lname /dev/null | wc -l`"])
	3
	"""
	pid = os.fork()
	if pid == 0:  # child
		close_fds()
		os.execv(file, args)
		os._exit(127)
	elif pid > 0:  # parent
		pid, status = os.waitpid(pid, 0)
		if os.WIFEXITED(status):
			return os.WEXITSTATUS(status)
		elif os.WIFSIGNALED(status):
			return -os.WTERMSIG(status)
		else:
			raise OSError('Child %d terminated by unknown cause: %04x' % (pid, status))
	else:
		raise OSError('Failed to fork child process.')


if __name__ == '__main__':
	import doctest
	doctest.testmod()
