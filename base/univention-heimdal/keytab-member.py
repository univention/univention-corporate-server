#!/usr/bin/python3
#
# Univention Heimdal
#  listener script for generating keytab for Managed Nodes
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import pwd
from subprocess import call

import univention.debug as ud

import listener


server_role = listener.configRegistry['server/role']


description = 'Kerberos 5 keytab maintenance for Managed Nodes'
filter = (
    '(&'
    '(objectClass=krb5Principal)'
    '(objectClass=krb5KDCEntry)'
    '(krb5KeyVersionNumber=*)'
    '(objectClass=univentionMemberServer)'
    ')'
)


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    if not new.get('krb5Key'):
        return

    if server_role == 'domaincontroller_master':
        listener.setuid(0)
        try:
            if old:
                cn = old['cn'][0].decode('UTF-8')
                ud.debug(ud.LISTENER, ud.PROCESS, 'Purging krb5.keytab of %s' % (cn,))
                ktab = '/var/lib/univention-heimdal/%s' % (cn,)
                try:
                    os.unlink(ktab)
                except OSError:
                    pass
            if new:
                cn = new['cn'][0].decode('UTF-8')
                ud.debug(ud.LISTENER, ud.PROCESS, 'Generating krb5.keytab for %s' % (cn,))
                ktab = '/var/lib/univention-heimdal/%s' % (cn,)
                # FIXME: otherwise the keytab entry is duplicated
                call(['kadmin', '-l', 'ext', '--keytab=%s' % (ktab,), new['krb5PrincipalName'][0].decode('UTF-8')])
                try:
                    userID = pwd.getpwnam('%s$' % cn)[2]
                    os.chown(ktab, userID, 0)
                    os.chmod(ktab, 0o660)
                except (OSError, KeyError):
                    pass
        finally:
            listener.unsetuid()
