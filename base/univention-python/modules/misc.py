#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Python
#  miscellaneous utilities
#
# Copyright (C) 2002, 2003, 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
