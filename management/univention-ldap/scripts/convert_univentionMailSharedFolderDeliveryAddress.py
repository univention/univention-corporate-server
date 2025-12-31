#!/usr/bin/python3
#
# Univention LDAP
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import argparse
import sys

import univention.config_registry
import univention.uldap


def run():
    lo = univention.uldap.getAdminConnection()

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()

    searchResult = lo.search(base=ucr.get('ldap/base'), filter='(&(objectClass=univentionMailSharedFolder)(univentionMailSharedFolderDeliveryAddress=*))', attr=['univentionMailSharedFolderDeliveryAddress'])
    for dn, attr in searchResult:
        ml = []
        oldval = attr['univentionMailSharedFolderDeliveryAddress']
        newval = [x.lower() for x in oldval]
        if oldval != newval:
            ml.append(('univentionMailSharedFolderDeliveryAddress', oldval, newval))
            try:
                print('Updating %s' % dn)
                lo.modify(dn, ml)
            except Exception:
                print('E: Failed to modify %s' % dn, file=sys.stderr)

    print('done')


description = '''This script converts LDAP attribute univentionMailSharedFolderDeliveryAddress of
all shared folder LDAP objects to lower case. This script should be called on
UCS Primary Directory Node only.'''

parser = argparse.ArgumentParser(description=description)
args = parser.parse_args()
run()
