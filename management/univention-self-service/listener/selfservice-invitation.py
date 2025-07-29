#!/usr/bin/python3
#
# Univention LDAP
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os

import univention.debug as ud

import listener


# `pwdChangeNextLogin=1` should be set for the created user.
# When this listener module was created, it was assumed that this results
# in either `shadowMax=1` or `shadowLastChange=0`.
# But this is only true if there is no password policy applied during creation -
# the filter was changed to require `sambaPwdLastSet=0` instead. (Bug #57226)
name = 'selfservice-invitation'
description = 'trigger selfservice email for new users with PasswordRecoveryEmail'
filter = '(&(univentionPasswordSelfServiceEmail=*)(uid=*)(sambaPwdLastSet=0))'
modrdn = '1'
cache_dir = '/var/cache/univention-directory-listener/selfservice-invitation'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]], command: str) -> None:
    if not listener.configRegistry.is_true('umc/self-service/invitation/enabled', True):
        return

    if listener.configRegistry.get('server/role', 'undefined') != 'domaincontroller_master':
        return

    if new and not old and command == 'a':
        filename = os.path.join(cache_dir, new.get('uid')[0].decode('UTF-8').replace('/', '') + '.send')
        ud.debug(ud.LISTENER, ud.PROCESS, '%s: trigger selfservice invitation for %r' % (name, dn))
        try:
            os.mknod(filename)
        except OSError as exc:
            if hasattr(exc, 'errno') and exc.errno == 17:
                pass
            else:
                raise
