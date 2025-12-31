#
# Univention Admin Diary
# Listener module to set up Admin Diary configuration
#
# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import subprocess

from univention.config_registry import ConfigRegistry, handler_set

import listener


description = 'Manage admin/diary/backend variable'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']

service_name = b"Admin Diary Backend"


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    listener.setuid(0)
    try:
        change = False
        new_has_service = service_name in new.get('univentionService', [])
        old_has_service = service_name in old.get('univentionService', [])
        if new_has_service and not old_has_service:
            try:
                fqdn = b'%s.%s' % (new['cn'][0], new['associatedDomain'][0])
            except (KeyError, IndexError):
                return

            ucr = ConfigRegistry()
            ucr.load()
            old_ucr_value = ucr.get('admin/diary/backend', '')
            fqdn_set = set(old_ucr_value.split())
            fqdn_set.add(fqdn.decode('utf-8'))
            new_ucr_value = ' '.join(fqdn_set)
            handler_set(['admin/diary/backend=%s' % (new_ucr_value,)])
            change = True
        elif old_has_service:
            try:
                fqdn = b'%s.%s' % (old['cn'][0], old['associatedDomain'][0])
            except (KeyError, IndexError):
                return

            ucr = ConfigRegistry()
            ucr.load()
            old_ucr_value = ucr.get('admin/diary/backend', '')
            fqdn_set = set(old_ucr_value.split())
            fqdn_set.discard(fqdn.decode('UTF-8'))
            new_ucr_value = ' '.join(fqdn_set)
            handler_set(['admin/diary/backend=%s' % (new_ucr_value,)])
            change = True

        if change:
            subprocess.call(['invoke-rc.d', 'rsyslog', 'try-restart'])
    finally:
        listener.unsetuid()
