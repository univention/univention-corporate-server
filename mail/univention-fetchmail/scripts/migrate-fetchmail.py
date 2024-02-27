#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
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

"""Update old fetchmail configurations."""
import argparse
import json
import re
import sys

import univention.admin.uldap
import univention.debug as ud
from univention.config_registry import ConfigRegistry


FETCHMAILRC = '/etc/fetchmailrc'
PASSWORD_REGEX = re.compile("^poll .*? there with password '(.*?)' is '[^']+' here")
FETCHMAIL_PROPERTIES = {'fetchmailUseSSL', 'fetchmailKeep', 'fetchmailPassword', 'fetchmailUsername', 'fetchmailProtocol', 'fetchmailServer'}


def load_rc(ofile):
    """open an textfile with setuid(0) for root-action"""
    rc = None
    try:
        with open(ofile) as fd:
            rc = fd.readlines()
    except OSError as exc:
        ud.debug(ud.PROCESS, ud.ERROR, 'Failed to open %r: %s' % (ofile, exc))
    return rc


def get_pw_from_rc(lines, uid):
    """get current password of a user from fetchmailrc"""
    if not uid:
        return None
    for line in lines:
        line = line.rstrip()
        if line.endswith("#UID='%s'" % uid):
            match = PASSWORD_REGEX.match(line)
            if match:
                return match.group(1)
    return None


def map_fetchmail(value):
    ret = []
    for elem in value:
        entry = []
        for param in elem:
            entry.append(param if isinstance(param, str) else param.decode())
        ret.append(json.dumps(entry).encode('UTF-8'))
    return ret


def unmap_fetchmail(value):
    try:
        entries = [json.loads(v) for v in value]
    except ValueError:
        # try the previous format. This should only happen once as
        # the next time the values will be already json formatted (#56008).
        entries = [[w.strip('"') for w in v.decode('UTF-8').split('";"')] for v in value]
    return entries


class Converter(object):
    def __init__(self):
        self.ucr = ConfigRegistry()
        self.ucr.load()
        self.access = None
        self.position = None
        self.ret = 0

    def parse_cmdline(self):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--binddn', help='LDAP bind dn')
        parser.add_argument('--bindpwdfile', help='LDAP bind password file for bind dn')
        parser.add_argument('--dry-run', action='store_true', help='perform dry run without changes')
        parser.add_argument('--dn', help='Perform the conversion for an specific DN')
        self.args = parser.parse_args()

    def main(self, cmdline=True):
        if cmdline:
            self.parse_cmdline()
            self.get_ldap()
        ret = self.convert(self.args.dn)

        return ret

    def get_ldap(self):
        if self.args.binddn and self.args.bindpwdfile:
            with open(self.args.bindpwdfile) as fp:
                bindpwd = fp.read().strip()

            self.access = univention.admin.uldap.access(
                host=self.ucr["ldap/master"],
                port=int(self.ucr.get('ldap/master/port', '7389')),
                base=self.ucr['ldap/base'],
                binddn=self.args.binddn,
                bindpw=bindpwd,
            )
            self.position = univention.admin.uldap.position(self.ucr['ldap/base'])
        else:
            self.access, self.position = univention.admin.uldap.getAdminConnection()

    def details_complete(self, **kwargs):
        missing = [key for key in kwargs if not kwargs[key]]
        return (len(missing) == 0, missing)

    def remaining_attributes(self, missing, keep, ssl):
        rem = FETCHMAIL_PROPERTIES - set(missing)
        if not keep:
            rem.remove('fetchmailUseSSL')
        if not ssl:
            rem.remove('fetchmailKeep')
        return rem

    def convert(self, user_dn=None):
        self.debug("Converting old fetchmail configuration...")
        file = load_rc(FETCHMAILRC)
        if file is None:
            return

        ret = []
        if not user_dn:
            ldap_filter = '(&(objectClass=univentionFetchmail)(univentionObjectType=users/user))'
            ldap_base = self.ucr['ldap/base']
        else:
            ldap_filter = '(&(objectClass=univentionFetchmail)(univentionObjectType=users/user))'
            ldap_base = user_dn
        for dn, attrs in self.access.search(
            filter=ldap_filter,
            attr=['uid', 'univentionFetchmailAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailPasswd', 'univentionFetchmailKeepMailOnServer', 'univentionFetchmailUseSSL', 'univentionFetchmailSingle'],
            base=ldap_base
        ):
            uid = attrs['uid'][0].decode('UTF-8')
            server = attrs.get('univentionFetchmailServer', [])
            protocol = attrs.get('univentionFetchmailProtocol', [])
            passwd = attrs.get('univentionFetchmailPasswd', [])
            address = attrs.get('univentionFetchmailAddress', [])
            keep = attrs.get('univentionFetchmailKeepMailOnServer', [])
            ssl = attrs.get('univentionFetchmailUseSSL', [])

            res, missing = self.details_complete(fetchmailServer=server,
                                                 fetchmailProtocol=protocol,
                                                 fetchmailPassword=passwd,
                                                 fetchmailUsername=address)

            not_already_migrated = len(missing) < 4
            # The old listener removed the univentionFetchmailPasswd when possible and used the password from
            # /etc/fetchmailrc file.
            if not passwd:
                password = get_pw_from_rc(file, uid)
                if password and not_already_migrated:
                    missing.remove('fetchmailPassword')
                    res = len(missing) == 0
            else:
                password = passwd[0]

            if not res:
                if not_already_migrated or keep or ssl:
                    self.debug("Cannot migrate object with dn: %r. Remaining fetchmail attributes: %s" % (dn, ", ".join(self.remaining_attributes(missing, keep, ssl))))
                    if self.args.dry_run:
                        ret.append((dn, self.remaining_attributes(missing, keep, ssl)))
                continue
            else:
                password = password.encode('UTF-8') if isinstance(password, str) else password
                old_fetchmail_new = attrs.get('univentionFetchmailSingle', [])
                updated_fetchmail_new = unmap_fetchmail(old_fetchmail_new)
                updated_fetchmail_new.append([
                    server[0] if server else b'',
                    protocol[0] if protocol else b'',
                    address[0] if address else b'',
                    password,
                    keep[0] if keep else b'0',
                    ssl[0] if ssl else b'0',
                ])

                changes = [
                    ('univentionFetchmailServer', server, []), ('univentionFetchmailProtocol', protocol, []),
                    ('univentionFetchmailAddress', address, []), ('univentionFetchmailKeepMailOnServer', keep, []),
                    ('univentionFetchmailUseSSL', ssl, []), ('univentionFetchmailPasswd', passwd, []),
                    ('univentionFetchmailSingle', old_fetchmail_new, map_fetchmail(updated_fetchmail_new)),
                ]
                try:
                    self.debug('Updating %s' % (dn,))
                    if not self.args.dry_run:
                        self.access.modify(dn, changes, ignore_license=1)
                    else:
                        ret.append((dn, self.remaining_attributes(missing, keep, ssl)))
                except Exception as ex:
                    self.error('Failed to modify %s: %s, changes: %s' % (dn, ex, changes))
        self.debug("Done.")
        return ret

    def debug(self, msg):
        print(msg, file=sys.stderr)

    def error(self, msg):
        print(msg, file=sys.stderr)
        self.ret = 1


def main():
    c = Converter()
    c.main()
    sys.exit(c.ret)


if __name__ == '__main__':
    main()
