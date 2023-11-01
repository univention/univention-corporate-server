#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Resync object from OpenLDAP to S4
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.


import os
import pickle  # noqa: S403
import sys
import time
from argparse import ArgumentParser

import ldap

import univention.uldap
from univention.config_registry import ConfigRegistry


class UCSResync(object):

    def __init__(self, ldap_master=False):
        self.configRegistry = ConfigRegistry()
        self.configRegistry.load()
        self.lo = univention.uldap.getMachineConnection(ldap_master=ldap_master)

    def _get_listener_dir(self):
        return self.configRegistry.get('connector/s4/listener/dir', '/var/lib/univention-connector/s4')

    def _generate_filename(self, first):
        directory = self._get_listener_dir()
        if not first:
            return os.path.join(directory, "%f" % time.time())
        return os.path.join(directory, "-%f" % time.time())

    def _dump_object_to_file(self, object_data, first):
        filename = self._generate_filename(first)
        with open(filename, 'wb+') as fd:
            os.chmod(filename, 0o600)
            p = pickle.Pickler(fd)
            p.dump(object_data)
            p.clear_memo()

    def _search_ldap_object_orig(self, ucs_dn):
        return self.lo.get(ucs_dn, attr=['*', '+'], required=True)

    def resync(self, first, ucs_dns=None, ldapfilter=None):
        treated_dns = []
        for dn, new in self.search_ldap(ucs_dns, ldapfilter):
            object_data = (dn, new, {}, None)
            self._dump_object_to_file(object_data, first)
            treated_dns.append(dn)

        return treated_dns

    def search_ldap(self, ucs_dns=None, ldapfilter=None):
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
                raise ldap.NO_SUCH_OBJECT(1, 'No object: %s' % (missing_dns,), [r[0] for r in ldap_result])
        else:
            ldap_result = self.lo.search(filter=ldapfilter, attr=attr)

        return ldap_result


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--filter", dest="ldapfilter", help="LDAP Filter")
    parser.add_argument("dn", nargs='?', default=None)
    parser.add_argument("--first", dest="first", action='store_true')
    parser.add_argument("-p", "--from-primary", action="store_true", help="use primary node for LDAP lookup (instead of the local LDAP)")
    options = parser.parse_args()

    if not options.dn and not options.ldapfilter:
        parser.print_help()
        sys.exit(2)

    ucs_dns = list(filter(None, [options.dn]))

    treated_dns = []
    try:
        resync = UCSResync(ldap_master=options.from_primary)
        treated_dns = resync.resync(options.first, ucs_dns, options.ldapfilter)
    except ldap.NO_SUCH_OBJECT as ex:
        print('ERROR: The LDAP object not found : %s' % ex.args[1])
        if len(ex.args) == 3:
            treated_dns = ex.args[2]
        sys.exit(1)
    finally:
        for dn in treated_dns:
            print('resync triggered for %s' % dn)

    if not treated_dns:
        print('No matching objects.')

    sys.exit(0)
