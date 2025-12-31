#!/usr/bin/python3
#
# Univention Heimdal
#  generating keytab entries
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import time
from subprocess import call
from typing import Any

import ldap.dn

import univention.debug as ud

import listener


hostname = listener.configRegistry['hostname']
domainname = listener.configRegistry['domainname']
base_domain = '.'.join(x[0][1] for x in ldap.dn.str2dn(listener.configRegistry['ldap/base']))
realm = listener.configRegistry['kerberos/realm']
server_role = listener.configRegistry['server/role']
ldap_master = listener.configRegistry['ldap/master']
samba4_role = listener.configRegistry.get('samba4/role', '')


description = 'Kerberos 5 keytab maintainance'
filter = (
    '(&'
    '(objectClass=krb5Principal)'
    '(objectClass=krb5KDCEntry)'
    '(krb5KeyVersionNumber=*)'
    '(|'
    '(krb5PrincipalName=host/%(hostname)s@%(realm)s)'
    '(krb5PrincipalName=ldap/%(hostname)s@%(realm)s)'
    '(krb5PrincipalName=host/%(hostname)s.%(domainname)s@%(realm)s)'
    '(krb5PrincipalName=ldap/%(hostname)s.%(domainname)s@%(realm)s)'
    '(krb5PrincipalName=host/%(hostname)s.%(base_domain)s@%(realm)s)'
    '(krb5PrincipalName=ldap/%(hostname)s.%(base_domain)s@%(realm)s)'
    ')'
    ')'
) % locals()

K5TAB = '/etc/krb5.keytab'


def clean() -> None:
    # don't do anything here if this system is joined as a Samba/AD DC
    if samba4_role.upper() in ('DC', 'RODC'):
        return

    listener.setuid(0)
    try:
        if os.path.exists(K5TAB):
            os.unlink(K5TAB)
    finally:
        listener.unsetuid()


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> Any:
    # don't do anything here if this system is joined as a Samba/AD DC
    if samba4_role.upper() in ('DC', 'RODC'):
        return

    if not new.get('krb5Key'):
        return

    if server_role == 'memberserver':
        ud.debug(ud.LISTENER, ud.PROCESS, 'Fetching %s from %s' % (K5TAB, ldap_master))
        listener.setuid(0)
        try:
            if os.path.exists(K5TAB):
                os.remove(K5TAB)
            count = 0
            while not os.path.exists(K5TAB):
                call(['univention-scp', '/etc/machine.secret', '%s$@%s:/var/lib/univention-heimdal/%s' % (hostname, ldap_master, hostname), K5TAB])
                if not os.path.exists(K5TAB):
                    if count > 30:
                        ud.debug(ud.LISTENER, ud.ERROR, 'E: failed to download keytab for Managed Node')
                        return -1
                    ud.debug(ud.LISTENER, ud.WARN, 'W: failed to download keytab for Managed Node, retry')
                    count += 1
                    time.sleep(2)
            os.chown(K5TAB, 0, 0)
            os.chmod(K5TAB, 0o600)
        finally:
            listener.unsetuid()
    else:
        ud.debug(ud.LISTENER, ud.PROCESS, 'Exporting %s on %s' % (K5TAB, server_role))
        listener.setuid(0)
        try:
            if old:
                call(['ktutil', 'remove', '-p', old['krb5PrincipalName'][0].decode('UTF-8')])
            if new:
                call(['kadmin', '-l', 'ext', new['krb5PrincipalName'][0].decode('UTF-8')])
        finally:
            listener.unsetuid()
