#!/usr/bin/python2.6
#
# Univention Common Python Library
#
# Copyright 2011-2012 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import fcntl
import os

def get_lock(name, nonblocking=False):
	"""
	get_lock() returns a filedescriptor for a lock file after the file
	has been locked exclusively. In non-blocking mode None is returned
	if the lock cannot be gained.
	The returned filedescriptor has to be kept. Otherwise the lock will
	be release automatically on filedescriptor's destruction.

	>>> fd = get_lock('myapp')
	>>> ...... do some critical stuff ......
	>>> release_lock(fd)
	>>>
	>>> fd = get_lock('myapp', nonblocking=True)
	>>> if not fd:
	>>>     print 'cannot get lock'
	>>> else:
	>>>     ...... do some critical stuff ......
	>>>     release_lock(fd)
	"""
	fn = "/var/run/%s.pid" % name
	fd = open(fn, 'w')
	try:
		if nonblocking:
			fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
		else:
			fcntl.lockf(fd, fcntl.LOCK_EX)
	except IOError, e:
		if e.errno == 11:
			return None
		raise
	print >>fd, '%s\n' % os.getpid()
	return fd


def release_lock(fd):
	"""
	release_lock() releases a previously gained lock.
	"""
	fcntl.lockf(fd, fcntl.LOCK_UN)
	fd.close()
