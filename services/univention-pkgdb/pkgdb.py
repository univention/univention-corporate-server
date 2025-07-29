#
# Univention Package Database
#  listener module
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import subprocess

import univention.debug as ud

from listener import SetUID, configRegistry


description = 'Package-Database'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionClient)(objectClass=univentionMemberServer))'
attributes = ['uid']

ADD_DIR = '/var/lib/univention-pkgdb/add'
DELETE_DIR = '/var/lib/univention-pkgdb/delete'


def exec_pkgdb(args: list[str]) -> int:
    ud.debug(ud.LISTENER, ud.INFO, "exec_pkgdb args=%s" % args)

    with SetUID(0):
        cmd = ['univention-pkgdb-scan', '--db-server=%(hostname)s.%(domainname)s' % configRegistry]
        cmd += args
        retcode = subprocess.call(cmd)

    ud.debug(ud.LISTENER, ud.INFO, "pkgdb: return code %d" % retcode)
    return retcode


def add_system(sysname: str) -> int:
    retcode = exec_pkgdb(['--add-system', sysname])
    if retcode != 0:
        ud.debug(ud.LISTENER, ud.ERROR, "error while adding system=%s to pkgdb" % sysname)
    else:
        ud.debug(ud.LISTENER, ud.INFO, "successful added system=%s" % sysname)
    return retcode


def del_system(sysname: str) -> int:
    retcode = exec_pkgdb(['--del-system', sysname])
    if retcode != 0:
        ud.debug(ud.LISTENER, ud.ERROR, "error while deleting system=%s to pkgdb" % sysname)
    else:
        ud.debug(ud.LISTENER, ud.INFO, "successful added system=%s" % sysname)
    return retcode


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    ud.debug(ud.LISTENER, ud.INFO, "pkgdb handler dn=%s" % (dn))

    with SetUID(0):
        if old and not new:
            if 'uid' in old:
                uid = old['uid'][0].decode('UTF-8')
                if del_system(uid) != 0:
                    with open(os.path.join(DELETE_DIR, uid), 'w') as fd:
                        fd.write(uid + '\n')

        elif new and not old and 'uid' in new:
            uid = new['uid'][0].decode('UTF-8')
            if add_system(uid) != 0:
                with open(os.path.join(ADD_DIR, uid), 'w') as fd:
                    fd.write(uid + '\n')
