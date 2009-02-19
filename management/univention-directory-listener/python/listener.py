# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  listener script
#
# Copyright (C) 2004-2009 Univention GmbH
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
import os, pwd, types, univention_baseconfig

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

def setuid(uid):
	if type(uid) == types.StringType:
		uid = pwd.getpwnam(uid)[2]
	os.seteuid(uid)

__listener_uid=-1
def unsetuid():
	global __listener_uid
	if __listener_uid == -1:
		try:
			__listener_uid = pwd.getpwnam('listener')[2]
		except KeyError:
			__listener_uid = 0
	os.seteuid(__listener_uid)

def run(file, argv, uid=-1, wait=1):
	if uid > -1:
		olduid=os.getuid()
		setuid(uid)
	try:
		if wait:
			waitp = os.P_WAIT
		else:
			waitp = os.P_NOWAIT
		rc = os.spawnv(waitp, file, argv)
	except:
		rc = 100
		if uid > -1:
			setuid(olduid)
	if uid > -1:
		setuid(olduid)
	return rc
