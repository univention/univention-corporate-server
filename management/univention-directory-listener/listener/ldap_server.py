#!/usr/bin/python3
#
# Univention Directory Listener
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""listener script for setting ldap server."""

from __future__ import annotations

import univention.config_registry
import univention.debug as ud

import listener


description = 'Update upstream LDAP server list'
filter = '(&(objectClass=univentionDomainController)(|(univentionServerRole=master)(univentionServerRole=backup)))'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    """Handle change in LDAP."""
    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()

    if ucr['server/role'] == 'domaincontroller_master':
        return

    listener.setuid(0)
    try:
        if 'univentionServerRole' in new:
            try:
                domain = new['associatedDomain'][0].decode('UTF-8')
            except LookupError:
                domain = ucr['domainname']
            add_ldap_server(ucr, new['cn'][0].decode('UTF-8'), domain, new['univentionServerRole'][0].decode('UTF-8'))
        elif 'univentionServerRole' in old and not new:
            try:
                domain = old['associatedDomain'][0].decode('UTF-8')
            except LookupError:
                domain = ucr['domainname']
            remove_ldap_server(ucr, old['cn'][0].decode('UTF-8'), domain, old['univentionServerRole'][0].decode('UTF-8'))
    finally:
        listener.unsetuid()


def add_ldap_server(ucr: dict[str, str], name: str, domain: str, role: str) -> None:
    """Add LDAP server."""
    ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Add ldap_server %s' % name)

    server_name = "%s.%s" % (name, domain)

    if role == 'master':
        old_master = ucr.get('ldap/master')

        changes = ['ldap/master=%s' % server_name]

        if ucr.get('kerberos/adminserver') == old_master:
            changes.append('kerberos/adminserver=%s' % server_name)

        if ucr.get('ldap/server/name') == old_master:
            changes.append('ldap/server/name=%s' % server_name)

        univention.config_registry.handler_set(changes)

    if role == 'backup':
        backup_list = ucr.get('ldap/backup', '').split()
        if server_name not in backup_list:
            backup_list.append(server_name)
            univention.config_registry.handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])


def remove_ldap_server(ucr: dict[str, str], name: str, domain: str, role: str) -> None:
    """Remove LDAP server."""
    ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Remove ldap_server %s' % name)

    server_name = "%s.%s" % (name, domain)

    if role == 'backup':
        backup_list = ucr.get('ldap/backup', '').split()
        if server_name in backup_list:
            backup_list.remove(server_name)
            univention.config_registry.handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])
