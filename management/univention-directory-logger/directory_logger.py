#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  listener script for directory transaction logging
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

from __future__ import absolute_import, annotations

import base64
import grp
import hashlib
import os
import re
import subprocess
import syslog
import time
from typing import Dict, List, Tuple

import univention.debug as ud

from listener import SetUID, configRegistry


name = 'directory_logger'
description = 'Log directory transactions'
filter = '(!(objectClass=lock))'  # log all objects by default, but skip temporary lock objects

logname = '/var/log/univention/directory-logger.log'
excludeKeyPattern = re.compile(r'ldap/logging/exclude\d+')
cachename = '/var/lib/univention-directory-logger/cache'
notifier_id = '/var/lib/univention-directory-listener/notifier_id'

headerfmt = '''START\nOld Hash: %s\nDN: %s\nID: %s\nModifier: %s\nTimestamp: %s\nAction: %s\n'''
newtag = '\nNew values:\n'
oldtag = '\nOld values:\n'
endtag = 'END\n--\n'
logmsgfmt = '''DN=%s\nID=%s\nModifier=%s\nTimestamp=%s\nNew Hash=%s\n'''
timestampfmt = '''%d.%m.%Y %H:%M:%S'''
uidNumber = 0
preferedGroup = "adm"
gidNumber = 0  # fallback
filemode = 0o640
digest = configRegistry.get('ldap/logging/hash', 'md5')

SAFE_STRING_RE = re.compile(r'^(?:\000|\n|\r| |:|<)|[\000\n\r\200-\377]+|[ ]+$'.encode('ASCII'))
DELLOG_FILE_LINE_NUMBERS = 5


def ldapEntry2string(entry: Dict[str, List[bytes]]) -> str:
    # TODO: we don't know the encoding of the attribute, therefore every non-ASCII value must be base64
    return ''.join(
        '%s:: %s\n' % (key, base64.standard_b64encode(value).decode('ASCII'))
        if not value.isascii() or SAFE_STRING_RE.search(value) else
        '%s: %s\n' % (key, value.decode('ASCII'))
        for key, values in entry.items()
        for value in values
    )


def ldapTime2string(timestamp: str) -> str:
    try:
        timestruct = time.strptime(timestamp, "%Y%m%d%H%M%SZ")
    except ValueError:
        ud.debug(ud.LISTENER, ud.ERROR, '%r: could not parse timestamp %r, expected LDAP format' % (name, timestamp))
        return timestamp  # return it as it was
    return time.strftime(timestampfmt, timestruct)


def filterOutUnchangedAttributes(old_copy: Dict[str, List[bytes]], new_copy: Dict[str, List[bytes]]) -> None:
    for key in list(old_copy):
        if key not in new_copy:
            continue
        if new_copy[key] == old_copy[key]:
            del old_copy[key]
            del new_copy[key]
            continue
        removelist = []
        for value in old_copy[key]:
            for value2 in new_copy[key]:
                if value == value2:
                    removelist.append(value)
                    continue
        for value in removelist:
            old_copy[key].remove(value)
            new_copy[key].remove(value)


def _parse_dellog_file(pathname: str) -> None:
    """Extract data from a dellog file."""
    with open(pathname) as f:
        lines = f.readlines()
        # A dellog file must have DELLOG_FILE_LINE_NUMBERS lines
        if len(lines) == DELLOG_FILE_LINE_NUMBERS:
            return [line.rstrip() for line in lines]
        else:
            raise ValueError('Expected 5 lines, but received %d' % len(lines))


def process_dellog(dn: str) -> Tuple[str, str, str, str]:
    dellog = configRegistry['ldap/logging/dellogdir']

    dellist = sorted(os.listdir(dellog))

    for filename in dellist:
        pathname = os.path.join(dellog, filename)
        try:
            try:
                if pathname.endswith(".fail"):
                    continue
                (dellog_stamp, dellog_id, dellog_dn, modifier, action) = _parse_dellog_file(pathname)
            except EnvironmentError:
                ud.debug(ud.LISTENER, ud.ERROR, 'EnvironmentError: Renaming %s to %s.fail' % (filename, filename))
                os.rename(pathname, '%s.fail' % pathname)
                continue
            except ValueError as exc:
                ud.debug(ud.LISTENER, ud.ERROR, 'Corrupted file: %r: %s' % (filename, exc))
                os.unlink(pathname)
                continue
            if dellog_dn == dn:
                os.unlink(pathname)
                timestamp = ldapTime2string(dellog_stamp)
                break
            # this unlink is actually needed because not all objects that are documented through dellog
            # are actually processed by the listener. Namely the grandchildren of the cn=temporary container.
            # since the files are basically timestamps, and we sort them, we can delete all the ones older
            # than the one we are handeling right now
            os.unlink(pathname)

        except Exception as exc:
            ud.debug(ud.LISTENER, ud.ERROR, 'Unknown Exception: %s.' % (exc,))
            ud.debug(ud.LISTENER, ud.ERROR, 'Renaming %s to %s.fail' % (filename, filename))
            os.rename(pathname, '%s.fail' % pathname)
            continue
    else:
        ud.debug(ud.LISTENER, ud.ERROR, 'Did not find matching dn %r in dellog directory %r.' % (dn, dellog))
        timestamp = time.strftime(timestampfmt, time.gmtime())
        dellog_id = '<NoID>'
        modifier = '<unknown>'
        action = '<unknown>'

    return (timestamp, dellog_id, modifier, action)


def prefix_record(record: str, identifier: int) -> str:
    if not configRegistry.is_true('ldap/logging/id-prefix', False):
        return record
    return '\n'.join('ID %s: %s' % (identifier, line) for line in record.splitlines()) + '\n'


def handler(dn: str, new_copy: Dict[str, List[bytes]], old_copy: Dict[str, List[bytes]]) -> None:
    if not configRegistry.is_true('ldap/logging'):
        return

    with SetUID(0):
        # check for exclusion
        if any(
                value in dn
                for key, value in configRegistry.items()
                if excludeKeyPattern.match(key)
        ):
            # only deletes are dumped as files by the dellog overlay module
            # we delete those files silently
            if not new_copy:
                process_dellog(dn)
            # important: don't return a thing, otherwise this dn
            # seems to get excluded from future processing by this module
            return

        # Start processing
        # 1. read previous hash
        if not os.path.exists(cachename):
            ud.debug(ud.LISTENER, ud.ERROR, '%s: %s vanished mid-run, stop.' % (name, cachename))
            return  # really bad, stop it.
        cachefile = open(cachename, 'r+')
        previoushash = cachefile.read()

        # get ID
        with open(notifier_id) as f:
            nid = int(f.readline()) + 1
        # matches notifier transaction nid. Tested for UCS 1.3-2 and 2.0.
        # Note about 1.3-2:
        # For user removal this matches with ++last_id as seen by the dellog overlay,
        # but for user create dellog sees nid-1, i.e. last_id has already been incremented before
        # we see it here

        # 2. generate log record
        if new_copy:
            try:
                modifier = new_copy['modifiersName'][0].decode('UTF-8')
            except LookupError:
                modifier = '<unknown>'
            try:
                timestamp = ldapTime2string(new_copy['modifyTimestamp'][0].decode('ASCII'))
            except LookupError:
                timestamp = '<unknown>'

            if not old_copy:  # create branch
                record = headerfmt % (previoushash, dn, nid, modifier, timestamp, 'add')
                record += newtag
                record += ldapEntry2string(new_copy)
            else:  # modify branch
                # filter out unchanged attributes
                filterOutUnchangedAttributes(old_copy, new_copy)
                record = headerfmt % (previoushash, dn, nid, modifier, timestamp, 'modify')
                record += oldtag
                record += ldapEntry2string(old_copy)
                record += newtag
                record += ldapEntry2string(new_copy)
        else:  # delete branch
            (timestamp, _dellog_id, modifier, _action) = process_dellog(dn)

            record = headerfmt % (previoushash, dn, nid, modifier, timestamp, 'delete')
            record += oldtag
            record += ldapEntry2string(old_copy)
        record += endtag

        # 3. write log file record
        with open(logname, 'a') as logfile:  # append
            logfile.write(prefix_record(record, nid))
        # 4. calculate nexthash, omitting the final line break to make validation of the
        #    record more intituive
        nexthash = hashlib.new(digest, record[:-1].encode('UTF-8')).hexdigest()
        # 5. cache nexthash (the actual logfile might be logrotated away..)
        cachefile.seek(0)
        cachefile.write(nexthash)
        cachefile.close()
        # 6. send log message including nexthash
        syslog.openlog(name, 0, syslog.LOG_DAEMON)
        syslog.syslog(syslog.LOG_INFO, logmsgfmt % (dn, nid, modifier, timestamp, nexthash))
        syslog.closelog()


def createFile(filename: str) -> int:
    global gidNumber

    if gidNumber == 0:
        try:
            gidNumber = int(grp.getgrnam(preferedGroup)[2])
        except Exception:
            ud.debug(ud.LISTENER, ud.WARN, '%s: Failed to get groupID for "%s"' % (name, preferedGroup))
            gidNumber = 0

    basedir = os.path.dirname(filename)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    if subprocess.call(["/bin/touch", filename]) or not os.path.exists(filename):
        ud.debug(ud.LISTENER, ud.ERROR, '%s: %s could not be created.' % (name, filename))
        return 1
    os.chown(filename, uidNumber, gidNumber)
    os.chmod(filename, filemode)
    return 0


def initialize() -> None:
    timestamp = time.strftime(timestampfmt, time.gmtime())
    ud.debug(ud.LISTENER, ud.INFO, 'init %s' % name)

    with SetUID(0):
        if not os.path.exists(logname):
            createFile(logname)

        if not os.path.exists(cachename):
            createFile(cachename)
        size = os.path.getsize(cachename)
        cachefile = open(cachename, 'r+')

        # generate log record
        if size == 0:
            action = 'Initialize'
            record = 'START\nTimestamp: %s\nAction: %s %s\n' % (timestamp, action, name)
        else:
            # read previous hash
            previoushash = cachefile.read()
            action = 'Reinitialize'
            record = 'START\nOld Hash: %s\nTimestamp: %s\nAction: %s %s\n' % (previoushash, timestamp, action, name)
        record += endtag

        # 3. write log file record
        with open(logname, 'a') as logfile:  # append
            logfile.write(prefix_record(record, 0))
        # 4. calculate initial hash
        nexthash = hashlib.new(digest, record.encode('UTF-8')).hexdigest()
        # 5. cache nexthash (the actual logfile might be logrotated away..)
        cachefile.seek(0)
        cachefile.write(nexthash)
        cachefile.close()
        # 6. send log message including nexthash
        syslog.openlog(name, 0, syslog.LOG_DAEMON)
        syslog.syslog(syslog.LOG_INFO, '%s\nTimestamp=%s\nNew Hash=%s' % (action, timestamp, nexthash))
        syslog.closelog()


# --- initialize on load:
with SetUID(0):
    if not os.path.exists(logname):
        createFile(logname)
    if not os.path.exists(cachename):
        ud.debug(ud.LISTENER, ud.WARN, '%s: %s vanished, creating it' % (name, cachename))
        createFile(cachename)
