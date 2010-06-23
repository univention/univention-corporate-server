#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Python
#  miscellaneous utilities
#
# Copyright 2002-2010 Univention GmbH
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

import os

def filemax():
	return int(open('/proc/sys/fs/file-max').read()[0:-1])

def close_fd_spawn(file, args):
	pid = os.fork()
	if pid == 0:
		for i in range(0, filemax()):
			try:
				os.close(i)
			except OSError:
				pass
		os.open('/dev/null', os.O_RDONLY)
		os.open('/dev/null', os.O_WRONLY)
		os.open('/dev/null', os.O_WRONLY)
		os.execv(file, args)
	elif pid > 0:
		os.waitpid(pid, 0)
