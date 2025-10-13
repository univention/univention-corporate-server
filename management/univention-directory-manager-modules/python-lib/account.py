#!/usr/bin/python3
#
# Univention Common Python Library
#
# SPDX-FileCopyrightText: 2010-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

'''python3 -m univention.lib.account lock --dn "$user_dn" --lock-time "$(date --utc '+%Y%m%d%H%M%SZ')"'''

import argparse
from logging import getLogger

import univention.admin.modules
import univention.admin.uldap
import univention.debug as ud


univention.admin.modules.update()


# Ensure univention debug is initialized
def initialize_debug():  # type: () -> None
    # Use a little hack to determine if univention.debug has been initialized
    # get_level(..) returns always ERROR if univention.debug is not initialized
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


def lock(userdn, lock_timestamp):  # type: (str, str) -> None
    """
    Lock a user account

    * used by ppolicy OpenLDAP overlay
    * used by PAM faillock

    >>> from univention.lib.account import lock  # doctest: +SKIP
    >>> lock('uid=user1,dc=example,dc=com', '20141006192950Z')  # doctest: +SKIP
    """
    if not lock_timestamp:  # timed unlocking via ppolicy not implemented yet, so block it.
        return

    try:
        lo, pos = univention.admin.uldap.getAdminConnection()
    except Exception:
        lo, pos = univention.admin.uldap.getMachineConnection()

    module = univention.admin.modules._get('users/user')

    univention.admin.modules.init(lo, pos, module)

    object = module.object(None, lo, pos, userdn)
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
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers()
    subparser = subparsers.add_parser('lock', help='Locks a user account')
    subparser.add_argument('--dn', required=True, help='The DN of the user account to be locked.')
    subparser.add_argument('--lock-time', required=True, help='The time when the user account was locked.')
    args = parser.parse_args()

    initialize_debug()
    getLogger('ADMIN').info("univention.lib.account.lock was called for %s (%s)", args.dn, args.lock_time)
    lock(args.dn, args.lock_time)
