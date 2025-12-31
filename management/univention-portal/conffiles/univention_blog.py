#!/usr/bin/python3
#
# Univention Blog Portal Entry
#
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Create a portal entry for the Univention Blog for all Core Edition users."""

import subprocess
import sys


def handler(config_registry, changes):
    if config_registry.get('server/role') != 'domaincontroller_master':
        return
    ldap_base = config_registry.get('ldap/base')

    try:
        _, new_val = changes.get('license/base', [None, None])
    except ValueError:  # UCR module initialization
        new_val = changes['license/base']

    if new_val in ("UCS Core Edition", "Free for personal use edition"):
        cmd = ['univention-directory-manager', 'portals/category', 'modify', '--dn', 'cn=domain-admin,cn=category,cn=portals,cn=univention,%s' % (ldap_base,), '--ignore_not_exists', '--append', 'entries=cn=univentionblog,cn=entry,cn=portals,cn=univention,%s' % (ldap_base,)]
        process('Adding blog entry failed', cmd)
    else:
        cmd = ['univention-directory-manager', 'portals/category', 'modify', '--dn', 'cn=domain-admin,cn=category,cn=portals,cn=univention,%s' % (ldap_base,), '--ignore_not_exists', '--remove', 'entries=cn=univentionblog,cn=entry,cn=portals,cn=univention,%s' % (ldap_base,)]
        process('Removing blog entry failed', cmd)


def process(msg, cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    stdout = process.communicate()[0].decode('UTF-8', 'replace')
    if process.returncode:
        print('%s: %d: %s %r' % (msg, process.returncode, stdout, cmd), file=sys.stderr)
