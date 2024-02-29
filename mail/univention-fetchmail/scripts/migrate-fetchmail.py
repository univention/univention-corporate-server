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
        self.args = parser.parse_args()

    def main(self):
        self.parse_cmdline()
        self.get_ldap()
        ret = self.convert()

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

    def convert(self):
        self.debug("Converting old fetchmail configuration...")
        file = load_rc(FETCHMAILRC)
        if not file:
            return

        for dn, attrs in self.access.search(
            filter='(&(objectClass=univentionFetchmail)(univentionObjectType=users/user))',
            attr=['uid', 'univentionFetchmailAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailPasswd', 'univentionFetchmailKeepMailOnServer', 'univentionFetchmailUseSSL', 'univentionFetchmailSingle'],
        ):
            uid = attrs['uid'][0].decode('UTF-8')
            server = attrs.get('univentionFetchmailServer', [])
            protocol = attrs.get('univentionFetchmailProtocol', [])
            passwd = attrs.get('univentionFetchmailPasswd', [get_pw_from_rc(file, uid)])[0]
            address = attrs.get('univentionFetchmailAddress', [])
            keep = attrs.get('univentionFetchmailKeepMailOnServer', [])
            ssl = attrs.get('univentionFetchmailUseSSL', [])

            if not server:
                self.debug('Skip object with uid "%s". Already migrated or incomplete configuration' % (uid,))
                continue

            if not passwd:
                self.debug('Skip object with uid "%s". Unable to retrieve univentionFetchmailPasswd attribute from /etc/fetchmailrc file' % (uid,))
                continue

            passwd = passwd.encode('UTF-8') if isinstance(passwd, str) else passwd
            old_fetchmail_new = attrs.get('univentionFetchmailSingle', [])
            updated_fetchmail_new = unmap_fetchmail(old_fetchmail_new)
            updated_fetchmail_new.append([
                server[0] if server else b'',
                protocol[0] if protocol else b'',
                address[0] if address else b'',
                passwd,
                keep[0] if keep else b'0',
                ssl[0] if ssl else b'0',
            ])

            changes = [
                ('univentionFetchmailServer', server, []), ('univentionFetchmailProtocol', protocol, []),
                ('univentionFetchmailAddress', address, []), ('univentionFetchmailKeepMailOnServer', keep, []),
                ('univentionFetchmailUseSSL', ssl, []), ('univentionFetchmailSingle', old_fetchmail_new, map_fetchmail(updated_fetchmail_new)),
            ]
            try:
                self.debug('Updating %s' % (dn,))
                self.access.modify(dn, changes, ignore_license=1)
            except Exception as ex:
                self.error('Failed to modify %s: %s, changes: %s' % (dn, ex, changes))
        self.debug("Done.")

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
