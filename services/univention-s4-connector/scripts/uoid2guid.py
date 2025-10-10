#!/usr/bin/python3
#
# Univention S4 Connector
#  check univentionObjectIdentifier 2 objectGUID mapping table
#
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
from argparse import ArgumentParser

import univention.s4connector.s4
from univention.config_registry import ConfigRegistry
from univention.s4connector import decode_guid


def list_mapping(con, opts):
    if opts.verbose:
        con.init_ldap_connections()
    for uoid, guid, deleted, create_date, delete_date in con._get_config_items('uoid2guid'):
        if opts.verbose:
            ucs_dn = con._get_dn_by_univention_object_identifier(uoid)
            ad_dn = con._get_dn_by_object_guid(guid)
            print(f'uoid: {uoid}, guid: {guid}')
            print(f'\tucs dn: {ucs_dn}')
            print(f'\tad dn: {ad_dn}')
            print(f'\tdeleted: {bool(deleted)}')
            print(f'\tcreated at: {create_date}')
            print(f'\tdeleted at: {delete_date}')
        else:
            print(uoid, guid, bool(deleted), create_date, delete_date)


def import_mapping(con, opts):
    con.init_ldap_connections()
    for ad_dn, ucs_dn in con._get_config_items('DN Mapping CON'):
        uoid = con.lo.getAttr(ucs_dn, attr='univentionObjectIdentifier')
        guid = con.lo_s4.getAttr(ad_dn, attr='objectGUID')
        if uoid and guid:
            uoid = uoid[0].decode('UTF-8')
            guid = decode_guid(guid[0])
            if not con.uoid2guid_exists(uoid=uoid):
                print(f'add mapping {uoid}:{guid} for {ucs_dn}:{ad_dn}')
                if opts.do_it:
                    con.uoid2guid_add_mapping(uoid=uoid, guid=guid)


def purge_mapping(con, opts):
    print('WARNING: purging this mapping table is just for testing, do not run this in production, connector might no longer work!')
    for uoid, guid, deleted, create_date, delete_date in con._get_config_items('uoid2guid'):
        if not opts.everything and not deleted:
            continue
        print(f'purge mapping {uoid}:{guid} deleted:{bool(deleted)}')
        if opts.do_it:
            con.uoid2guid_remove_mapping(uoid=uoid, lazy_delete=False)


if __name__ == '__main__':
    parser = ArgumentParser(description="check univentionObjectIdentifier 2 objectGUID mapping table")
    parser.add_argument("-c", "--configbasename", help="Config basename", metavar="CONFIGBASENAME", default="connector")
    commands_parsers = parser.add_subparsers(title="subcommands", description="valid subcommands", required=True, dest="command")
    list_parser = commands_parsers.add_parser("list", help="list mappings")
    list_parser.add_argument("-v", "--verbose", help="verbose output", default=False, action="store_true")
    list_parser.set_defaults(func=list_mapping)
    import_parser = commands_parsers.add_parser("import", help="import mapping from 'DN MAPPING CON'")
    import_parser.add_argument("--do-it", default=False, action="store_true", help="do the import instead of dry-run")
    import_parser.set_defaults(func=import_mapping)
    purge_parser = commands_parsers.add_parser("purge", help="delete entries form the mapping table that are marked as deleted")
    purge_parser.add_argument("--do-it", default=False, action="store_true", help="do the purge instead of dry-run")
    purge_parser.add_argument("--everything", default=False, action="store_true", help="remove everything from the mapping table")
    purge_parser.set_defaults(func=purge_mapping)
    options = parser.parse_args()

    state_directory = f'/etc/univention/{options.configbasename}'
    if not os.path.exists(state_directory):
        parser.error(f"Invalid configbasename, directory {state_directory} does not exist")

    configRegistry = ConfigRegistry()
    configRegistry.load()
    con = univention.s4connector.s4.s4.main(configRegistry, options.configbasename)
    options.func(con, options)
