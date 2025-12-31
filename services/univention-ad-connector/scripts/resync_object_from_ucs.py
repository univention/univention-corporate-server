#!/usr/bin/python3
#
# Univention AD Connector
#  Resync object from OpenLDAP to AD
#
# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
import pickle  # noqa: S403
import sys
import time
from argparse import ArgumentParser

import ldap

import univention.uldap
from univention.config_registry import ConfigRegistry
from univention.dn import DN


class UCSResync:

    def __init__(self, ldap_master=False):
        self.configRegistry = ConfigRegistry()
        self.configRegistry.load()
        self.lo = univention.uldap.getMachineConnection(ldap_master=ldap_master)

    def _get_listener_dir(self):
        return self.configRegistry.get(f'{options.configbasename}/ad/listener/dir', '/var/lib/univention-connector/ad')

    def _generate_filename(self):
        directory = self._get_listener_dir()
        return os.path.join(directory, f"{time.time():f}")

    def _dump_object_to_file(self, object_data):
        filename = self._generate_filename()
        with open(filename, 'wb+') as fd:
            os.chmod(filename, 0o600)
            p = pickle.Pickler(fd)
            p.dump(object_data)
            p.clear_memo()

    def _search_ldap_object_orig(self, ucs_dn):
        return self.lo.get(ucs_dn, attr=['*', '+'], required=True)

    def resync(self, ucs_dns=None, ldapfilter=None, ldapbase=None):
        search_result = self.search_ldap(ucs_dns, ldapfilter, ldapbase)

        # If a DN to resync happens to be a subtree DN, we might also want to resync the ancestors
        self.prepend_ancestors_of_allowed_subtrees(search_result, ldapfilter, ldapbase)

        treated_dns = []
        for dn, new in search_result:
            object_data = (dn, new, {}, None)
            self._dump_object_to_file(object_data)
            treated_dns.append(dn)

        return treated_dns

    def search_ldap(self, ucs_dns=None, ldapfilter=None, ldapbase=None):
        attr = ('*', '+')

        if ucs_dns:
            if not ldapfilter:
                ldapfilter = '(objectClass=*)'

            ldap_result = []
            missing_dns = []
            for targetdn in ucs_dns:
                try:
                    result = self.lo.search(base=targetdn, scope='base', filter=ldapfilter, attr=attr)
                    ldap_result.extend(result)
                except ldap.NO_SUCH_OBJECT:
                    missing_dns.append(targetdn)
            if missing_dns:
                raise ldap.NO_SUCH_OBJECT(1, f'No object: {missing_dns}', [r[0] for r in ldap_result])
        else:
            if not ldapfilter:
                ldapfilter = '(objectClass=*)'

            if not ldapbase:
                ldapbase = self.configRegistry['ldap/base']

            ldap_result = self.lo.search(base=ldapbase, filter=ldapfilter, attr=attr)

        return ldap_result

    def _get_allowed_subtrees(self) -> list[DN]:
        allowed_subtrees = []
        for key in self.configRegistry:
            if key.startswith(f'{options.configbasename}/ad/mapping/allowsubtree') and key.endswith('/ucs'):
                allowed_subtrees.append(DN(self.configRegistry[key]))

        return allowed_subtrees

    def prepend_ancestors_of_allowed_subtrees(self, ucs_search_result: list[tuple] | None, ldapfilter, ldapbase):
        if self.configRegistry.is_false(f"{options.configbasename}/ad/mapping/allow-subtree-ancestors", False) or ucs_search_result is None:
            return

        ucs_ldap_base = DN(self.configRegistry.get("ldap/base"))

        allowed_subtrees: list[DN] = self._get_allowed_subtrees()

        ancestor_list = []
        for object_dn, _ in ucs_search_result:
            object_dn = DN(object_dn)
            if object_dn not in allowed_subtrees:
                continue

            subtree_dn = object_dn
            parent_dn = object_dn.parent
            while parent_dn and parent_dn != ucs_ldap_base:
                parent = str(parent_dn)
                print(f"{subtree_dn} is an allowed subtree. Adding ancestor DN {parent} to resync list.")
                if parent not in ancestor_list:
                    ancestor_list.insert(0, parent)
                parent_dn = parent_dn.parent
        if not ancestor_list:
            return

        ancestor_ucs_search_result = self.search_ldap(ancestor_list, ldapfilter, ldapbase)
        ancestor_ucs_search_result.sort(key=lambda x: len(x[0]))
        ucs_search_result[:0] = ancestor_ucs_search_result


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--filter", dest="ldapfilter", help="LDAP search filter")
    parser.add_argument("-b", "--base", dest="ldapbase", help="LDAP search base")
    parser.add_argument("-c", "--configbasename", dest="configbasename", metavar="CONFIGBASENAME", default="connector")
    parser.add_argument("-p", "--from-primary", action="store_true", help="use primary node for LDAP lookup (instead of the local LDAP)")
    parser.add_argument("dn", nargs='?', default=None)
    options = parser.parse_args()

    state_directory = f'/etc/univention/{options.configbasename}'
    if not os.path.exists(state_directory):
        parser.error(f"Invalid configbasename, directory {state_directory} does not exist")

    if not options.dn and not options.ldapfilter:
        parser.print_help()
        sys.exit(2)

    ucs_dns = list(filter(None, [options.dn]))

    treated_dns = []
    try:
        resync = UCSResync(ldap_master=options.from_primary)
        treated_dns = resync.resync(ucs_dns, options.ldapfilter, options.ldapbase)
    except ldap.NO_SUCH_OBJECT as ex:
        print(f'ERROR: The LDAP object not found : {ex!s}')
        if len(ex.args) == 3:
            treated_dns = ex.args[2]
        sys.exit(1)
    finally:
        for dn in treated_dns:
            print(f'resync triggered for {dn}')

    if not treated_dns:
        print('No matching objects.')

    sys.exit(0)
