# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  listener script
#
# Copyright 2004-2015 Univention GmbH
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
import os, pwd, types
import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

baseConfig=configRegistry

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
