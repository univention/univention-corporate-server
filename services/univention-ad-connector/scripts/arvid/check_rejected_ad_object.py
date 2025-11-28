#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Check rejected AD object
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
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

from __future__ import print_function

import base64
import os
import sys
import time
from argparse import ArgumentParser

import ldap
from samba.dcerpc import misc
from samba.ndr import ndr_unpack

import univention.connector.ad
import univention.debug2 as ud
from univention.config_registry import ConfigRegistry
from univention.dn import DN


class GUIDNotFound(BaseException):
    pass


class DNNotFound(BaseException):
    pass


class ad(univention.connector.ad.ad):

    def initialize_udm(self):
        # load UCS Modules
        self.modules = {}
        self.modules_others = {}
        position = univention.admin.uldap.position(self.lo.base)

        for key, mapping in self.property.items():
            if mapping.ucs_module:
                self.modules[key] = univention.admin.modules.get(mapping.ucs_module)
                if hasattr(mapping, 'identify'):
                    ud.debug(ud.LDAP, ud.INFO, "Override identify function for %s" % key)
                    self.modules[key].identify = mapping.identify
            else:
                self.modules[key] = None
            univention.admin.modules.init(self.lo, position, self.modules[key])

            self.modules_others[key] = []
            if mapping.ucs_module_others:
                for m in mapping.ucs_module_others:
                    if m:
                        self.modules_others[key].append(univention.admin.modules.get(m))
                for m in self.modules_others[key]:
                    if m:
                        univention.admin.modules.init(self.lo, position, m)

    def _ad_rejected_generator(self):
        cursor = self.config._dbcon.execute("SELECT * FROM 'AD rejected'")
        for row in cursor:
            yield (self.__decode_GUID(row[0]), row[1])

    def _ad_rejected_check(self, condn):
        cursor = self.config._dbcon.execute("SELECT * FROM 'AD rejected' WHERE lower(value)=lower(?)'", (condn,))
        return bool(cursor.fetchall())

    def _ad_guid_entry(self, guid_blob):
        code = base64.b64encode(guid_blob).decode('ASCII')
        cursor = self.config._dbcon.execute("SELECT value FROM 'AD GUID' where key=?", (code,))
        ad_dn = list(cursor.fetchall())
        if ad_dn:
            return ad_dn[0]

    def _check_ad_guid_entry(self, guid_blob, ad_dn):
        return ad_dn in self._get_DN_for_GUID(guid_blob)

    def _check_dn_mapping_entries(self, ad_dn, ucs_dn):
        cursor = self.config._dbcon.execute("SELECT * FROM 'DN Mapping CON' WHERE key=?", (ad_dn.lower(),))
        rows = cursor.fetchall()
        if rows and rows[0][1] != ucs_dn.lower():
            print("DN Mapping CON not correct for key %s : %s" % (ad_dn, rows[0][1]))
            if options.resync:
                self.config._dbcon.execute("UPDATE 'DN Mapping CON' SET value=? WHERE key=?", (ucs_dn.lower(), ad_dn.lower()))
                self.config._dbcon.commit()

        cursor = self.config._dbcon.execute("SELECT * FROM 'DN Mapping UCS' WHERE key=?", (ucs_dn.lower(),))
        rows = cursor.fetchall()
        if rows and rows[0][1] != ad_dn.lower():
            print("DN Mapping UCS not correct for key %s : %s" % (ucs_dn, rows[0][1]))
            if options.resync:
                self.config._dbcon.execute("UPDATE 'DN Mapping CON' SET value=? WHERE key=?", (ucs_dn.lower(), ad_dn.lower()))
                self.config._dbcon.commit()

        cursor = self.config._dbcon.execute("SELECT * FROM 'DN Mapping UCS' WHERE value=?", (ad_dn.lower(),))
        rows = cursor.fetchall()
        if rows and rows[0][0] != ucs_dn.lower():
            print("DN Mapping UCS not correct for value %s : %s" % (ad_dn, rows[0][0]))
            if options.resync:
                self.config._dbcon.execute("DELETE FROM 'DN Mapping UCS' where key=?", (rows[0][0],))
                self.config._dbcon.execute("INSERT OR REPLACE INTO 'DN Mapping UCS' (key, value) VALUES (?, ?)", (ucs_dn.lower(), ad_dn.lower()))
                self.config._dbcon.commit()

    def resync_to_ucs(self, msg):
        ad_object = self.__object_from_element(msg)
        property_key = self.__identify_ad_type(ad_object)
        ad_dn = msg[0]
        if not property_key:
            ud.debug(ud.LDAP, ud.INFO, "AD object type not recognized: %s" % (ad_dn,))
            return
        mapped_object = self._object_mapping(property_key, ad_object)
        try:
            if not self._ignore_object(property_key, mapped_object) and not self._ignore_object(property_key, ad_object):
                sync_successfull = self.sync_to_ucs(property_key, mapped_object, ad_dn, ad_object)
            else:
                sync_successfull = True
        except ldap.SERVER_DOWN:
            raise
        except Exception:  # FIXME: which exception is to be caught?
            print("Resync of object failed \n\t%s" % (ad_object['dn']))
            sync_successfull = False
        if sync_successfull:
            # self._remove_rejected(change_usn)
            self._set_DN_for_GUID(msg[1]['objectGUID'][0], msg[0])
            if property_key in ("ou", "container") and 'olddn' in ad_object:  # move or rename
                # should we really update the AD GUIDs for the subtree or rather leave it up for resyncing them all?
                pass
                # self._update_subtree_in_ad_guids(ad_object['olddn'], elements[0][0])

    def check(self, ad_dns=None, ldapfilter=None, ldapbase=None):
        result = self.search_ad(ad_dns, ldapfilter, ldapbase)

        treated_dns = []
        for guid_blob, msg in result:
            ad_dn = msg[0]
            # useful?
            _ad_dn = self._ad_guid_entry(guid_blob)
            if not _ad_dn:
                print("AD DN not in 'AD GUID' table: %s" % (ad_dn,))

            guid = ndr_unpack(misc.GUID, guid_blob)
            ldapfilter = '(univentionObjectIdentifier=%s)' % guid
            res = self.lo.search(scope='sub', filter=ldapfilter, attr=['1.1'])
            if not res:
                print("UCS DN not found for AD object: %s (%s)" % (guid, ad_dn))
                continue

            ucs_dn = res[0][0]
            self._check_dn_mapping_entries(ad_dn, ucs_dn)

            if options.resync:
                self.resync_to_ucs(msg)
            treated_dns.append(ad_dn)

        return treated_dns

    def search_ad(self, ad_dns=None, ldapfilter=None, ldapbase=None):
        search_result = []
        if ad_dns:
            if not ldapfilter:
                ldapfilter = '(objectClass=*)'

            error_dns = []
            missing_dns = []
            for targetdn in ad_dns:
                guid_blob = None
                try:
                    res = self.__search_ad(base=targetdn, scope=ldap.SCOPE_BASE, filter=ldapfilter)

                    for msg in res:
                        if not msg[0]:  # Referral
                            continue
                        guid_blob = msg[1]["objectGUID"][0]
                        search_result.append((guid_blob, msg))
                    if not guid_blob:
                        missing_dns.append(targetdn)
                except ldap.NO_SUCH_OBJECT as ex:
                    error_dns.append((targetdn, str(ex)))
                except (ldap.REFERRAL, ldap.INVALID_DN_SYNTAX) as ex:
                    error_dns.append((targetdn, str(ex)))
            if error_dns:
                raise DNNotFound(1, error_dns, [r[0] for r in search_result])
            if missing_dns:
                raise GUIDNotFound(1, missing_dns, [r[0] for r in search_result])
        else:
            if not ldapfilter:
                ldapfilter = '(objectClass=*)'

            if not ldapbase:
                ldapbase = self.configRegistry['%s/ad/ldap/base' % CONFIGBASENAME]

            guid_blob = None
            try:
                res = self.__search_ad(base=ldapbase, scope=ldap.SCOPE_SUBTREE, filter=ldapfilter)

                for msg in res:
                    if not msg[0]:  # Referral
                        continue
                    guid_blob = msg[1]["objectGUID"][0]
                    search_result.append((guid_blob, msg))
            except (ldap.REFERRAL, ldap.INVALID_DN_SYNTAX):
                raise DNNotFound(2, ldapbase)

            if not guid_blob:
                raise GUIDNotFound(2, "No match")

        return search_result

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
                raise ldap.NO_SUCH_OBJECT(1, 'No object: %s' % (missing_dns,), [r[0] for r in ldap_result])
        else:
            if not ldapfilter:
                ldapfilter = '(objectClass=*)'

            if not ldapbase:
                ldapbase = self.configRegistry['ldap/base']

            ldap_result = self.lo.search(base=ldapbase, filter=ldapfilter, attr=attr)

        return ldap_result

    def _get_allowed_subtrees(self):
        allowed_subtrees = []

        for key in self.configRegistry:
            if key.startswith(f'{CONFIGBASENAME}/ad/mapping/allowsubtree') and key.endswith('/ad'):
                allowed_subtrees.append(DN(self.configRegistry[key]))

        return allowed_subtrees


if __name__ == '__main__':
    parser = ArgumentParser(description="Resync object from AD to UCS")
    parser.add_argument("-f", "--filter", dest="ldapfilter", help="LDAP search filter")
    parser.add_argument("-b", "--base", dest="ldapbase", help="LDAP search base")
    parser.add_argument("-c", "--configbasename", help="Config basename", metavar="CONFIGBASENAME", default="connector")
    parser.add_argument("--resync", action='store_true')
    parser.add_argument("dn", nargs='*', help="Active Directory DN to resync")
    options = parser.parse_args()

    CONFIGBASENAME = options.configbasename
    state_directory = '/etc/univention/%s' % CONFIGBASENAME
    if not os.path.exists(state_directory):
        parser.error("Invalid configbasename, directory %s does not exist" % state_directory)

    if not options.dn and not options.ldapfilter:
        parser.print_help()
        sys.exit(2)

    configRegistry = ConfigRegistry()
    configRegistry.load()

    poll_sleep = int(configRegistry['%s/ad/poll/sleep' % CONFIGBASENAME])

    ad_dns = options.dn

    treated_dns = []

    try:
        resync = ad.main(configRegistry, CONFIGBASENAME)
        resync.init_ldap_connections()
        resync.initialize_udm()
        treated_dns = resync.check(ad_dns, options.ldapfilter, options.ldapbase)
    except ldap.SERVER_DOWN:
        print("Warning: Can't initialize LDAP-Connections, wait...")
        sys.stdout.flush()
        time.sleep(poll_sleep)
    except DNNotFound as ex:
        print('ERROR: The AD object was not found: %s' % (ex.args[1],))
        if len(ex.args) == 3:
            treated_dns = ex.args[2]
        sys.exit(1)
    except GUIDNotFound as ex:
        print('ERROR: The AD search for objectGUID failed: %s' % (ex.args[1],))
        if len(ex.args) == 3:
            treated_dns = ex.args[2]
        sys.exit(1)

    if not treated_dns:
        print('No matching objects.')

    sys.exit(0)
