#!/usr/bin/python3
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import subprocess

import univention.debug as ud

import listener


description = 'Tell portal server to refresh when something important changed'
filter = '(|(univentionObjectType=portals/portal)(univentionObjectType=portals/category)(univentionObjectType=portals/entry)(univentionObjectType=portals/folder)(univentionObjectType=portals/announcement))'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    listener.setuid(0)
    try:
        attrs = new or old
        object_type = attrs.get('univentionObjectType', [])
        if object_type:
            module = object_type[0].decode('utf-8').split('/')[-1]
        else:
            module = 'unknown'
        reason = f'ldap:{module}:{dn}'
        ud.debug(ud.LISTENER, ud.PROCESS, "Updating portal. Reason: %s" % reason)
        subprocess.call(['/usr/sbin/univention-portal', 'update', '--reason', reason], stdout=subprocess.PIPE)
    finally:
        listener.unsetuid()
