#!/usr/bin/python3
#
# Univention LDAP
"""listener script for ldap schema extensions."""
#
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import subprocess

import univention.debug as ud
from univention.lib import ldap_extension

import listener


name = 'ldap_extension'
description = 'Configure LDAP schema and ACL extensions'
filter = '(|(objectClass=univentionLDAPExtensionSchema)(objectClass=univentionLDAPExtensionACL))'

schema_handler = ldap_extension.UniventionLDAPSchema(listener.configRegistry)
acl_handler = ldap_extension.UniventionLDAPACL(listener.configRegistry)


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    """Handle LDAP schema extensions on Primary and Backup"""
    if new:
        ocs = new.get('objectClass', [])
    elif old:
        ocs = old.get('objectClass', [])

    if b'univentionLDAPExtensionSchema' in ocs:
        schema_handler.handler(dn, new, old, name=name)
    elif b'univentionLDAPExtensionACL' in ocs:
        acl_handler.handler(dn, new, old, name=name)
    else:
        ud.debug(ud.LISTENER, ud.ERROR, '%s: Undetermined error: unknown objectclass: %s.' % (name, ocs))


def postrun() -> None:
    """Restart LDAP server Primary and mark new extension objects active"""
    server_role = listener.configRegistry.get('server/role')
    if server_role != "domaincontroller_master":
        if not acl_handler._todo_list:
            # In case of schema changes only restart slapd on Primary
            return
        # Only set active flags on Primary
        schema_handler._todo_list = []
        acl_handler._todo_list = []

    slapd_running = not subprocess.call(['pidof', 'slapd'])
    initscript = '/etc/init.d/slapd'
    if os.path.exists(initscript) and slapd_running:
        listener.setuid(0)
        try:
            if schema_handler._do_reload or acl_handler._do_reload:
                ud.debug(ud.LISTENER, ud.PROCESS, '%s: Reloading LDAP server.' % (name,))
                for handler_object in (schema_handler, acl_handler):
                    handler_object._do_reload = False
                p = subprocess.Popen(
                    [initscript, 'graceful-restart'], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                stdout, stderr = out.decode('UTF-8', 'replace'), err.decode('UTF-8', 'replace')
                if p.returncode != 0:
                    ud.debug(ud.LISTENER, ud.ERROR, f'{name}: LDAP server restart returned {stderr} {stdout} ({p.returncode}).')
                    for handler_object in (schema_handler, acl_handler):
                        if handler_object._todo_list:
                            for object_dn in handler_object._todo_list:
                                ldap_extension.set_handler_message(name, object_dn, f'LDAP server restart returned {stderr} {stdout} ({p.returncode}).')
                    return

            # Only set active flags on Primary
            if server_role == 'domaincontroller_master':
                for handler_object in (schema_handler, acl_handler):
                    handler_object.mark_active(handler_name=name)
        finally:
            listener.unsetuid()
