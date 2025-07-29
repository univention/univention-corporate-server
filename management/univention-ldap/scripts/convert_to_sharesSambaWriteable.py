#!/usr/bin/python3
#
# Univention LDAP
#  set the new attribute sambaWriteable to the same value as writeable
#  to get the same system-behavior
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.debug as ud


try:
    lo, position = univention.admin.uldap.getAdminConnection()
except Exception as exc:
    ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % (exc, ))
    print('authentication error: %s' % (exc,))
    sys.exit(1)


univention.admin.modules.update()
module = univention.admin.modules.get('shares/share')
univention.admin.modules.init(lo, position, module)

for obj in univention.admin.modules.lookup(module, None, lo, scope='sub'):
    obj.open()
    print('work on DN:', obj.dn)

    if obj['writeable'] and obj['sambaWriteable']:
        obj['sambaWriteable'] = obj['writeable']
        dn = obj.modify()
        lo.modify(dn, [])
    else:
        print("WARNING: Object is missing attributes writeable and/or sambaWriteable ! Did you already update univention-ldap ?")
