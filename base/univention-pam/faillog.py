#!/usr/bin/python3
#
# Univention PAM
#  Listener module for faillog
#
# SPDX-FileCopyrightText: 2001-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.debug as ud
from univention.admin.handlers.users.user import unmapLocked

import listener


description = 'The listener module resets the faillog count'
filter = '(objectClass=shadowAccount)'


def __login_is_locked(attrs: dict[str, list[bytes]]) -> bool:
    return unmapLocked(attrs) == '1'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    uid = new['uid'][0].decode('UTF-8')
    if new and old and __login_is_locked(old) and not __login_is_locked(new):
        # reset local bad password count
        ud.debug(ud.LISTENER, ud.PROCESS, 'Reset faillog for user %s' % uid)
        with listener.SetUID(0):
            listener.run('/usr/sbin/faillock', ['faillock', '--user', uid, '--reset'])
    elif __login_is_locked(new) and not __login_is_locked(old):
        if listener.configRegistry.is_true('auth/faillog'):
            # set local bad password count high enough for this system:
            limit = listener.configRegistry.get_int('auth/faillog/limit', 5)
            ud.debug(ud.LISTENER, ud.PROCESS, 'Trigger faillog for user %r' % uid)
            with listener.SetUID(0):
                listener.run('/usr/sbin/faillock', ['faillock', '--user', uid, '--reset=%s' % (limit + 1,)])  # FIXME: doesn't work
    elif old:
        # clean up on delete: reset local bad password count
        ud.debug(ud.LISTENER, ud.PROCESS, 'Reset faillog for user %r' % uid)
        with listener.SetUID(0):
            listener.run('/usr/sbin/faillock', ['faillock', '--user', uid, '--reset'])
