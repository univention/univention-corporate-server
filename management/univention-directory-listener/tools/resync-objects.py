#!/usr/bin/python3
#
# Univention Directory Listener
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Resync objects from Primary to local LDAP database"""


import argparse

import ldap
import ldap.modlist

from univention import uldap
from univention.config_registry import ucr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f", "--filter",
        default='(uid=%(hostname)s$)' % ucr,
        help="resync objects from Primary found by this filter. Default: (uid=<hostname>$)",
    )
    parser.add_argument(
        "-r", "--remove",
        action="store_true",
        help="remove objects in local database before resync",
    )
    parser.add_argument(
        "-s", "--simulate",
        action="store_true",
        help="dry run, do not remove or add",
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="update/modify existing objects",
    )
    opts = parser.parse_args()
    return opts


def main() -> None:
    opts = parse_args()
    base = ucr.get("ldap/base")
    server_role = ucr.get("server/role", "")
    if server_role == 'domaincontroller_master':
        print('local LDAP is Primary server, nothing to do')
        return
    if server_role not in ['domaincontroller_backup', 'domaincontroller_slave']:
        print(f'server role ("{server_role}") has no LDAP, nothing to do')
        return

    # get local and Primary connection
    local = uldap.getRootDnConnection()
    if server_role == "domaincontroller_backup":
        master = uldap.getAdminConnection()
    else:
        master = uldap.getMachineConnection(ldap_master=True)

    # delete local
    if opts.remove:
        res = local.searchDn(base=base, filter=opts.filter)
        if not res:
            print('object does not exist local')
        for dn in res:
            print("remove from local: %s" % (dn,))
            if not opts.simulate:
                local.delete(dn)

    # resync from Primary
    res = master.search(base=base, filter=opts.filter)
    if not res:
        print('object does not exist on Primary')
    for dn, data in res:
        print("resync from Primary: %s" % (dn,))
        try:
            local_res = local.search(base=dn)
        except ldap.NO_SUCH_OBJECT:
            local_res = None
        if local_res and opts.remove and opts.simulate:
            local_res = None
        if not local_res and not opts.update:
            print('  ==> adding object')
            if not opts.simulate:
                local.add(dn, ldap.modlist.addModlist(data))
        elif not local_res and opts.update:
            print('  ==> object does not exist, can not update')
        elif local_res and opts.update:
            modlist = []
            local_data = local_res[0][1]
            for key in set(data.keys()) | set(local_data.keys()):
                if set(local_data.get(key, [])).symmetric_difference(set(data.get(key, []))):
                    modlist.append([key, local_data.get(key, []), data.get(key, [])])
            if not modlist:
                print('  ==> no change')
            else:
                print('  ==> modifying object')
                if not opts.simulate:
                    local.modify(dn, modlist)
        elif local_res and not opts.update:
            print('  ==> object does exist, can not create')


if __name__ == "__main__":
    main()
