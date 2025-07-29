#!/usr/bin/python3
#
# Univention nss updater
#  Univention Listener Module
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.config_registry

import listener


description = 'Invalidate the nss group cache whenever a group membership has been modified.'
filter = '(objectClass=univentionGroup)'
attributes = ['uniqueMember', 'cn']


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    pass


def postrun() -> None:
    ucr = univention.config_registry.ConfigRegistry()  # TODO: why not listener.configRegistry?
    ucr.load()

    if ucr.is_true('nss/group/cachefile', False) and ucr.is_true('nss/group/cachefile/invalidate_on_changes', True):
        listener.setuid(0)
        try:
            param = ['ldap-group-to-file.py']
            if ucr.is_true('nss/group/cachefile/check_member', False):
                param.append('--check_member')
            listener.run('/usr/lib/univention-pam/ldap-group-to-file.py', param, uid=0)
        finally:
            listener.unsetuid()
