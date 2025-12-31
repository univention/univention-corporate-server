#
# Univention Software-Monitor
#  listener module that watches the availability of the software monitor service
#
# SPDX-FileCopyrightText: 2010-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from typing import Any

import univention.config_registry as ucr
import univention.debug as ud
import univention.uldap

from listener import SetUID


description = 'watches the availability of the software monitor service'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']

ldap_info: dict[str, Any] = {}


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    if new and b'Software Monitor' in new.get('univentionService', ()):
        with SetUID(0):
            ucr.handler_set(('pkgdb/scan=yes', ))
    elif old and b'Software Monitor' in old.get('univentionService', ()):
        if not ldap_info['lo']:
            ldap_reconnect()
        if ldap_info['lo'] and not ldap_info['lo'].search(filter='(&%s(univentionService=Software Monitor))' % filter, attr=['univentionService']):
            with SetUID(0):
                ucr.handler_set(('pkgdb/scan=no', ))


def ldap_reconnect() -> None:
    ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: ldap reconnect triggered')
    if 'ldapserver' in ldap_info and 'basedn' in ldap_info and 'binddn' in ldap_info and 'bindpw' in ldap_info:
        try:
            ldap_info['lo'] = univention.uldap.access(host=ldap_info['ldapserver'], base=ldap_info['basedn'], binddn=ldap_info['binddn'], bindpw=ldap_info['bindpw'])
        except ValueError as ex:
            ud.debug(ud.LISTENER, ud.ERROR, 'pkgdb-watch: ldap reconnect failed: %s' % (ex,))
            ldap_info['lo'] = None
        else:
            if ldap_info['lo'] is None:
                ud.debug(ud.LISTENER, ud.ERROR, 'pkgdb-watch: ldap reconnect failed')


def setdata(key: str, value: str) -> None:
    if key == 'bindpw':
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed key="%s" value="<HIDDEN>"' % key)
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed key="%s" value="%s"' % (key, value))

    if key in ['ldapserver', 'basedn', 'binddn', 'bindpw']:
        ldap_info[key] = value
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed unknown data (key="%s" value="%s")' % (key, value))

    if key == 'ldapserver':
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: ldap server changed to %s' % value)
        ldap_reconnect()
