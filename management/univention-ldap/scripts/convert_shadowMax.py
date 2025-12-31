#!/usr/bin/python3
#
# Univention LDAP
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.uldap
from univention.config_registry import ConfigRegistry


lo = univention.uldap.getAdminConnection()

ucr = ConfigRegistry()
ucr.load()

searchResult = lo.search(base=ucr['ldap/base'], filter='(&(objectClass=shadowAccount)(shadowLastChange=*)(shadowMax=*))', attr=['shadowLastChange', 'shadowMax'])

for dn, attributes in searchResult:
    ml = []
    if 'shadowLastChange' in attributes and 'shadowMax' in attributes:
        try:
            lastChange = int(attributes['shadowLastChange'][0])
            maximum = int(attributes['shadowMax'][0])
            if maximum >= lastChange:
                new_max = maximum - lastChange
                if new_max == 0:
                    ml.append(('shadowMax', attributes['shadowMax'], []))
                else:
                    ml.append(('shadowMax', attributes['shadowMax'], [str(new_max).encode('ASCII')]))
                lo.modify(dn, ml)
        except Exception:
            pass
