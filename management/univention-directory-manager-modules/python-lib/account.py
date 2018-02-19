#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2010-2018 Univention GmbH
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

import time
import argparse

import univention.admin.uldap
import univention.admin.objects
import univention.admin.modules
import univention.admin.handlers.users.user
import univention.debug as ud

univention.admin.modules.update()

# Ensure unviention debug is initialized
def initialize_debug():
	# Use a little hack to determine if univention.debug has been initialized
	# get_level(..) returns always ud.ERROR if univention.debug is not initialized
	with open("/tmp/3", "a") as f:
		f.write("ud.ADMIN: %s\n" % (ud.ADMIN,))
	oldLevel = ud.get_level(ud.ADMIN)
	if oldLevel == ud.PROCESS:
		ud.set_level(ud.ADMIN, ud.DEBUG)
		is_ready = (ud.get_level(ud.ADMIN) == ud.DEBUG)
	else:
		ud.set_level(ud.ADMIN, ud.PROCESS)
		is_ready = (ud.get_level(ud.ADMIN) == ud.PROCESS)
	if not is_ready:
		ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
		ud.set_level(ud.LDAP, ud.PROCESS)
		ud.set_level(ud.ADMIN, ud.PROCESS)
	else:
		ud.set_level(ud.ADMIN, oldLevel)


def lock(userdn, lock_timestamp):
	"""
	Lock a user account

	* used by ppolicy OpenLDAP overlay
	* used by PAM tally

	>>> import univention.lib.account
	>>> univention.lib.account.lock('uid=user1,dc=example,dc=com', '20141006192950Z')
	>>>

	"""

	if not lock_timestamp:  # timed unlocking via ppolicy not implemented yet, so block it.
		return

	initialize_debug()
	ud.debug(ud.ADMIN, ud.PROCESS, "univention.lib.account.lock was called for %s" % (userdn,))

	co = None
	try:
		lo, pos = univention.admin.uldap.getAdminConnection()
	except:
		lo, pos = univention.admin.uldap.getMachineConnection()

	module = univention.admin.modules.get('users/user')

	univention.admin.modules.init(lo, pos, module)

	object = module.object(co, lo, pos, userdn)
	object.open()
	states = (object.descriptions['locked'].editable, object.descriptions['locked'].may_change, object.descriptions['lockedTime'].editable, object.descriptions['lockedTime'].may_change)
	object.descriptions['locked'].editable, object.descriptions['locked'].may_change, object.descriptions['lockedTime'].editable, object.descriptions['lockedTime'].may_change = (True, True, True, True)
	object['locked'] = "1"
	try:
		if lock_timestamp:
			object['lockedTime'] = lock_timestamp
		object.modify()
	finally:
		object.descriptions['locked'].editable, object.descriptions['locked'].may_change, object.descriptions['lockedTime'].editable, object.descriptions['lockedTime'].may_change = states


if __name__ == '__main__':
	"""Usage:
		python -m univention.lib.account lock --dn "$user_dn" --lock-time "$(date --utc '+%Y%m%d%H%M%SZ')"
	"""
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers()
	subparser = subparsers.add_parser('lock', help='Locks a user account')
	subparser.add_argument('--dn', required=True, help='The DN of the user account to be locked.')
	subparser.add_argument('--lock-time', required=True, help='The time when the user account was locked.')
	args = parser.parse_args()
	lock(args.dn, args.lock_time)
