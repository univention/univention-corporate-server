# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manages samba privileges
#
# Copyright 2011-2019 Univention GmbH
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

from __future__ import absolute_import

import listener
import univention.debug
import tdb

SAMBA_PRIVILEGES = {
	"SeMachineAccountPrivilege": {"number": 16, "index": 0},
	"SeAddUsersPrivilege": {"number": 64, "index": 0},
	"SeTakeOwnershipPrivilege": {"number": 8, "index": 1},
	"SeBackupPrivilege": {"number": 2, "index": 1},
	"SeRestorePrivilege": {"number": 4, "index": 1},
	"SeRemoteShutdownPrivilege": {"number": 1, "index": 1},
	"SeSecurityPrivilege": {"number": 16, "index": 1},
	"SePrintOperatorPrivilege": {"number": 32, "index": 0},
	"SeDiskOperatorPrivilege": {"number": 128, "index": 0},
}

ALL_SAMBA_PRIVILEGES = SAMBA_PRIVILEGES.keys()

SAMBA_POLICY_TDB = "/var/lib/samba/account_policy.tdb"

name = 'samba-privileges'
description = 'Manages samba privileges'
filter = '(&(objectClass=univentionSambaPrivileges)(sambaSID=*))'
atributes = ['univentionSambaPrivilegeList', 'sambaSID']


def handler(dn, new, old):

	where = univention.debug.LISTENER
	level = univention.debug.INFO

	# deleted -> remove all privileges
	if old and not new:
		if old.get("univentionSambaPrivilegeList") and old.get("sambaSID"):
			univention.debug.debug(where, level, "%s: remove all samba privs (%s)" % (name, old["sambaSID"][0]))
			removePrivileges(old["sambaSID"][0], ALL_SAMBA_PRIVILEGES)

	# created
	if new and not old:
		if new.get("univentionSambaPrivilegeList") and new.get("sambaSID"):
			univention.debug.debug(where, level, "%s: add new samba privs (%s)" % (name, new["sambaSID"][0]))
			addPrivileges(new["sambaSID"][0], new["univentionSambaPrivilegeList"])

	# modified
	if new and old:

		newPrivs = new.get("univentionSambaPrivilegeList")
		oldPrivs = old.get("univentionSambaPrivilegeList")
		sid = new["sambaSID"][0]

		# removed
		if not newPrivs and oldPrivs:
			univention.debug.debug(where, level, "%s: remove all samba privs (%s)" % (name, sid))
			removePrivileges(sid, oldPrivs)
		# added
		if newPrivs and not oldPrivs:
			univention.debug.debug(where, level, "%s: add new samba privs (%s)" % (name, sid))
			addPrivileges(sid, newPrivs)

		# modified
		if newPrivs and oldPrivs and not newPrivs == oldPrivs:
			univention.debug.debug(where, level, "%s: modify samba privs (%s)" % (name, sid))
			removePrivileges(sid, oldPrivs)
			addPrivileges(sid, newPrivs)


def initialize():
	pass


def clean():
	pass


def postrun():
	pass


def addPrivileges(sambaSID, privileges):

	listener.setuid(0)

	try:
		tdbKey = 'PRIV_%s\x00' % (sambaSID)
		tdbFile = tdb.Tdb(SAMBA_POLICY_TDB)
		tdbFile.lock_all()
		privs = tdbFile.get(tdbKey)
		if not privs:
			privs = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

		for privilege in privileges:
			if SAMBA_PRIVILEGES.get(privilege, ""):
				index = SAMBA_PRIVILEGES[privilege].get("index", 0)
				number = SAMBA_PRIVILEGES[privilege].get("number", 0)
				if (ord(privs[index]) & number) == 0:
					new = chr(ord(privs[index]) + number)
					privs = privs[0:index] + new + privs[(index + 1):len(privs)]

		tdbFile[tdbKey] = privs
		tdbFile.unlock_all()
		tdbFile.close()
	finally:
		listener.unsetuid()


def removePrivileges(sambaSID, privileges):

	listener.setuid(0)

	try:
		tdbKey = 'PRIV_%s\x00' % (sambaSID)
		tdbFile = tdb.Tdb(SAMBA_POLICY_TDB)
		tdbFile.lock_all()
		privs = tdbFile.get(tdbKey)

		if privs:
			for privilege in privileges:
				if SAMBA_PRIVILEGES.get(privilege, ""):
					index = SAMBA_PRIVILEGES[privilege].get("index", "")
					number = SAMBA_PRIVILEGES[privilege].get("number", "")
					if ord(privs[index]) & number:
						new = chr(ord(privs[index]) - number)
						privs = privs[0:index] + new + privs[(index + 1):len(privs)]
						tdbFile[tdbKey] = privs

			# delete key if no privileges are assigned
			if privs == '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
				tdbFile.delete(tdbKey)

		tdbFile.unlock_all()
		tdbFile.close()
	finally:
		listener.unsetuid()
