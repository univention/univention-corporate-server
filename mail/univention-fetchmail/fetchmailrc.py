#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
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
#
from __future__ import absolute_import, annotations

import os
import re
from functools import reduce
from typing import Dict, Iterable, List

from six.moves import cPickle as pickle

import univention.debug as ud

import listener


description = 'write user-configuration to fetchmailrc'
filter = '(objectClass=univentionFetchmail)'

modrdn = "1"

fn_fetchmailrc = '/etc/fetchmailrc'
__initscript = '/etc/init.d/fetchmail'
FETCHMAIL_OLD_PICKLE = "/var/spool/univention-fetchmail/fetchmail_old_dn"

UID_REGEX = re.compile("#UID='(.+)'[ \t]*$")


def _split_file(fetch_list, new_line):
    if new_line.startswith('set') or new_line.startswith('#'):
        fetch_list.append(new_line)
    elif fetch_list:
        if UID_REGEX.search(fetch_list[-1]) or fetch_list[-1].startswith('set'):
            fetch_list.append(new_line)
        else:
            fetch_list[-1] += (new_line)
    return fetch_list


def load_rc(ofile: str) -> List[str] | None:
    """open an textfile with setuid(0) for root-action"""
    rc = None
    listener.setuid(0)
    try:
        with open(ofile) as fd:
            rc = reduce(_split_file, fd, [])
    except EnvironmentError as exc:
        ud.debug(ud.LISTENER, ud.ERROR, 'Failed to open "%s": %s' % (ofile, exc))
    listener.unsetuid()
    return rc


def write_rc(flist: Iterable[str], wfile: str) -> None:
    """write to an textfile with setuid(0) for root-action"""
    listener.setuid(0)
    try:
        with open(wfile, "w") as fd:
            fd.writelines(flist)
    except EnvironmentError as exc:
        ud.debug(ud.LISTENER, ud.ERROR, 'Failed to write to file "%s": %s' % (wfile, exc))
    listener.unsetuid()


def objdelete(dlist: Iterable[str], old: Dict[str, List[bytes]]) -> List[str]:
    """delete an object in filerepresenting-list if old settings are found"""
    if old.get('uid'):
        return [line for line in dlist if not re.search("#UID='%s'[ \t]*$" % re.escape(old['uid'][0].decode('UTF-8')), line)]
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'Removal of user in fetchmailrc failed: %r' % old.get('uid'))


def objappend_single(flist: List[str], new: Dict[str, List[bytes]], password: str | None = None) -> None:
    """add user's single fetchmail entries to flist"""
    entries = [[w.strip('\"') for w in v.decode('UTF-8').split(';')] for v in new.get('univentionFetchmailSingle', [])]
    for entry in entries:
        server, protocol, username, passwd, ssl, keep = entry
        flag_ssl = 'ssl' if ssl == '1' else ''
        flag_keep = 'keep' if keep == '1' else 'nokeep'
        mail_address = new['mailPrimaryAddress'][0].decode('UTF-8')
        uid = new['uid'][0].decode('UTF-8')
        flist.append(f"poll '{server}' with proto {protocol} auth password user '{username}' there with password '{passwd}' is '{mail_address}' here {flag_keep} {flag_ssl} #UID='{uid}'\n")


def objappend_multi(flist: List[str], new: Dict[str, List[bytes]], password: str | None = None) -> None:
    """add user's multi fetchmail entries to flist"""
    entries = [[w.strip('\"') for w in v.decode('UTF-8').split(';')] for v in new.get('univentionFetchmailMulti', [])]
    for entry in entries:
        server, protocol, username, passwd, localdomains, qmailprefix, envelope_header, ssl, keep = entry
        flag_ssl = 'ssl' if ssl == '1' else ''
        flag_keep = 'keep' if keep == '1' else 'nokeep'
        uid = new['uid'][0].decode('UTF-8')

        if not localdomains:
            localdomains = listener.configRegistry['mail/hosteddomains']

        if qmailprefix:
            qmailprefix = f'qvirtual {qmailprefix}'

        flist.append(f"""poll '{server}' with proto {protocol} envelope {envelope_header} {qmailprefix} no dns
    localdomains {localdomains}:
    user '{username}' there with password '{passwd}' is * here {flag_keep} {flag_ssl} #UID='{uid}'\n""")


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], command: str) -> None:
    if os.path.exists(FETCHMAIL_OLD_PICKLE):
        with open(FETCHMAIL_OLD_PICKLE, 'rb') as fd:
            p = pickle.Unpickler(fd)
            try:
                old = p.load()
            except EOFError:
                pass
        os.unlink(FETCHMAIL_OLD_PICKLE)
    if command == 'r':
        with open(FETCHMAIL_OLD_PICKLE, 'wb+') as fd:
            os.chmod(FETCHMAIL_OLD_PICKLE, 0o600)
            p = pickle.Pickler(fd)
            old = p.dump(old)
            p.clear_memo()

    flist = load_rc(fn_fetchmailrc)
    if new:
        old_single = old.get('univentionFetchmailSingle', [])
        new_single = new.get('univentionFetchmailSingle', [])
        old_multi = old.get('univentionFetchmailMulti', [])
        new_multi = new.get('univentionFetchmailMulti', [])
        old_uid = old['uid'][0]
        new_uid = new['uid'][0]

        if old_single != new_single or old_multi != new_multi or old_uid != new_uid:
            flist = objdelete(flist, old)
            objappend_single(flist, new)
            objappend_multi(flist, new)
            write_rc(flist, fn_fetchmailrc)
    elif old and command != 'r':
        ud.debug(ud.LISTENER, ud.INFO, 'fetchmail: User deleted. Removing from fetchmailrc.')
        flist = objdelete(flist, old)
        write_rc(flist, fn_fetchmailrc)


def postrun() -> None:
    initscript = __initscript
    ud.debug(ud.LISTENER, ud.INFO, 'Restarting fetchmail-daemon')
    listener.setuid(0)
    try:
        listener.run(initscript, ['fetchmail', 'restart'], uid=0)
    finally:
        listener.unsetuid()
