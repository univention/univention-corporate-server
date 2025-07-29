#!/usr/bin/python3
#
# Univention nscd Updater
#  Univention Listener Module
#
# SPDX-FileCopyrightText: 2001-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.debug as ud
from univention.config_registry import ConfigRegistry

import listener


name = 'nscd_update'
description = 'Invalidate the NSCD group cache whenever a group membership has been modified.'
filter = '(objectClass=univentionGroup)'
attributes = ['uniqueMember', 'cn']


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    pass


def postrun() -> None:
    configRegistry = ConfigRegistry()  # TODO: why not listener.configRegistry?
    configRegistry.load()

    if configRegistry.is_true('nscd/group/invalidate_cache_on_changes', False) and configRegistry.is_false('nss/group/cachefile', True):
        listener.setuid(0)
        try:
            ud.debug(ud.LISTENER, ud.INFO, "calling 'nscd -i group'")
            listener.run('/usr/sbin/nscd', ['nscd', '-i', 'group'], uid=0)
        except Exception:
            ud.debug(ud.LISTENER, ud.ERROR, "nscd -i group was not successful")
        finally:
            listener.unsetuid()
