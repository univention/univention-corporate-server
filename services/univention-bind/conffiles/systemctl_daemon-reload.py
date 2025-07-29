#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from os import unlink
from subprocess import call


COND = '/var/lib/univention-bind/ldap'


def postinst(ucr, changes):
    dns_backend = ucr.get('dns/backend', 'ldap').lower()
    if dns_backend == 'ldap':
        with open(COND, 'w') as fd:
            fd.write('1')
    else:
        try:
            unlink(COND)
        except OSError:
            pass
    call(['systemctl', 'daemon-reload'])
