#!/usr/bin/python3
#
# Univention Samba
#  listener module: manage idmap
#
# SPDX-FileCopyrightText: 2001-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import argparse
import sys

import ldb
from samba import Ldb
from samba.auth import system_session
from samba.param import LoadParm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-H", dest="ldburl", help="LDB Url")
    parser.add_argument("--prepend", action="append", help="Prepend LDB module", default=[])
    parser.add_argument("--append", action="append", help="Append LDB module", default=[])
    parser.add_argument("--remove", action="append", help="Append LDB module", default=[])
    parser.add_argument("--check", action="store_true", help="Check registered LDB modules", default=[])
    parser.add_argument("--ignore-exists", action="store_true", help="Don't add LDB modules already registered")
    parser.add_argument("--dry-run", action="store_true", help="Dry run")
    opts = parser.parse_args()

    if not (opts.prepend or opts.append or opts.remove or opts.check):
        parser.print_help()
        sys.exit(1)

    lp = LoadParm()
    lp.load('/etc/samba/smb.conf')

    ldb_object = Ldb(opts.ldburl, lp=lp, session_info=system_session())
    msg = ldb_object.search(base="@MODULES", scope=ldb.SCOPE_BASE, attrs=['@LIST'])

    assert len(msg) == 1
    assert "@LIST" in msg[0]

    if opts.verbose:
        print("Current @LIST:", msg[0]["@LIST"])
    if opts.check and not opts.dry_run:
        sys.exit(0)

    if len(msg[0]["@LIST"]) == 1:
        modules_0 = msg[0]["@LIST"][0].decode('UTF-8')
        modules_list_0 = modules_0.split(',')

        if opts.remove:
            # LDB Modules are organised as a stack, remove the last occurrence
            modules_list_0.reverse()
            for module in opts.remove:
                try:
                    modules_list_0.remove(module)
                except ValueError:
                    print("Module %s not in @LIST, ignoring" % module)
            modules_list_0.reverse()

        updated_modules = []
        for module in opts.prepend:
            if opts.ignore_exists and module in modules_list_0:
                continue
            else:
                updated_modules.append(module)
        updated_modules.extend(modules_list_0)
        for module in opts.append:
            if opts.ignore_exists and module in modules_list_0:
                continue
            else:
                updated_modules.append(module)
        updated_modules_str = ','.join(updated_modules)

        if opts.dry_run:
            print("Dry run @LIST:", updated_modules_str)
            sys.exit(0)

        modify_msg = ldb.Message()
        modify_msg.dn = ldb.Dn(ldb_object, "@MODULES")
        modify_msg["@LIST"] = ldb.MessageElement([updated_modules_str.encode('UTF-8')], ldb.FLAG_MOD_REPLACE, "@LIST")
        ldb_object.modify(modify_msg)
        if opts.verbose:
            msg = ldb_object.search(base="@MODULES", scope=ldb.SCOPE_BASE, attrs=['@LIST'])
            print("Updated @LIST:", msg[0]["@LIST"])
    else:
        print("Current @LIST attribute is multivalued, can't handle this")
        sys.exit(1)
