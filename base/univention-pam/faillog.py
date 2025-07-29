#!/usr/bin/python3
#
# Univention PAM
#  Listener module for faillog
#
# SPDX-FileCopyrightText: 2001-2025 Univention GmbH
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
    if new and old and __login_is_locked(old) and not __login_is_locked(new):
        # reset local bad password count
        ud.debug(ud.LISTENER, ud.PROCESS, 'Reset faillog for user %s' % new['uid'][0].decode('UTF-8'))
        listener.setuid(0)
        try:
            listener.run('/usr/sbin/faillock', ['faillock', '--user', new['uid'][0].decode('UTF-8'), '--reset'])
        finally:
            listener.unsetuid()
