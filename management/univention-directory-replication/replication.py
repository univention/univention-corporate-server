#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Replication
#  listener module for Directory replication
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
# Univention Directory Listener replication module

# Possible initialization scenarios:
# 1. New Replica
#    pull complete database from Primary
# 2. Primary is degraded to Replica
#    use existing database

from __future__ import annotations

import base64
import os
import re
import smtplib
import subprocess
import sys
import time
from email.mime.text import MIMEText
from errno import ENOENT
from typing import Any, Dict, List, Tuple

import ldap
import ldap.schema
# import ldif as ldifparser since the local module already uses ldif as variable
import ldif as ldifparser

import univention.debug as ud

import listener


description = 'LDAP Replica Node replication'
filter = '(objectClass=*)'  # default filter - may be overwritten later
modrdn = '1'
priority = 0.0


slave = listener.configRegistry['ldap/server/type'] == 'slave'

if listener.configRegistry['ldap/slave/filter']:
    filter = listener.configRegistry['ldap/slave/filter']

LDAP_DIR = '/var/lib/univention-ldap/'
STATE_DIR = '/var/lib/univention-directory-replication'
BACKUP_DIR = '/var/univention-backup/replication'
LDIF_FILE = os.path.join(STATE_DIR, 'failed.ldif')
ROOTPW_FILE = '/etc/ldap/rootpw.conf'
CURRENT_MODRDN = os.path.join(STATE_DIR, 'current_modrdn')
MAX_LDAP_RETRIES = int(listener.configRegistry.get('replication/ldap/retries', '30'))

EXCLUDE_ATTRIBUTES = {attr.lower() for attr in (
    'subschemaSubentry',
    'hasSubordinates',
    'entryDN',
    'authTimestamp',
    'pwdChangedTime',
    'pwdAccountLockedTime',
    'pwdFailureTime',
    'pwdHistory',
    'pwdGraceUseTime',
    'pwdReset',
    'pwdPolicySubentry',
)}
ud.debug(ud.LISTENER, ud.ALL, 'replication: EXCLUDE_ATTRIBUTES=%r' % (EXCLUDE_ATTRIBUTES,))

# exclude built-in OIDs from slapd
BUILTIN_OIDS = {line.strip() for line in open("/usr/share/univention-ldap/oid_skip")}


class LDIFObject(object):

    def __init__(self, filename: str) -> None:
        self.fp = open(filename, 'ab')
        os.chmod(filename, 0o600)

    def __print_attribute(self, attribute: str, value: Any) -> None:
        pos = len(attribute) + 2  # +colon+space
        encode = b'\n' in value
        try:
            if isinstance(value, tuple):
                (newval, leng) = value
            else:
                newval = value
            newval.decode('ascii')
        except UnicodeDecodeError:
            encode = True
        if encode:
            pos += 1  # value will be base64 encoded, thus two colons
            self.fp.write(b'%s::' % attribute.encode('UTF-8'))
            value = base64.b64encode(value)
        else:
            self.fp.write(b'%s:' % attribute.encode('UTF-8'))

        if not value:
            self.fp.write(b'\n')

        while value:
            if pos == 1:
                # first column is space
                self.fp.write(b' ')
            self.fp.write(b'%s\n' % (value[0:60 - pos],))
            value = value[60 - pos:]
            pos = 1

    def __new_entry(self, dn: str) -> None:
        self.__print_attribute('dn', dn.encode('UTF-8'))

    def __end_entry(self) -> None:
        self.fp.write(b'\n')
        self.fp.flush()

    def __new_section(self) -> None:
        pass

    def __end_section(self) -> None:
        self.fp.write(b'-\n')

    def add_s(self, dn: str, al: List[Tuple[str, Any]]) -> None:
        self.__new_entry(dn)
        self.__print_attribute('changetype', b'add')
        for attr, vals in al:
            for val in vals:
                self.__print_attribute(attr, val)
        self.__end_entry()

    def modify_s(self, dn: str, ml: List[Tuple[int, str, Any]]) -> None:
        self.__new_entry(dn)
        self.__print_attribute('changetype', b'modify')
        for ldap_op, attr, vals in ml:
            self.__new_section()
            if ldap_op == ldap.MOD_REPLACE:
                op = 'replace'
            elif ldap_op == ldap.MOD_ADD:
                op = 'add'
            elif ldap_op == ldap.MOD_DELETE:
                op = 'delete'
            self.__print_attribute(op, attr.encode('UTF-8'))
            for val in vals:
                self.__print_attribute(attr, val)
            self.__end_section()
        self.__end_entry()

    def delete_s(self, dn: str) -> None:
        self.__new_entry(dn)
        self.__print_attribute('changetype', b'delete')
        self.__end_entry()

    def rename_s(self, dn: str, newrdn: str, newsuperior: str | None = None, delold: int = 1, serverctrls=None, clientctrls=None) -> None:
        self.__new_entry(dn)
        self.__print_attribute('changetype', b'modrdn')
        self.__print_attribute('newrdn', newrdn.encode('UTF-8'))
        if newsuperior:
            self.__print_attribute('newsuperior', newsuperior.encode('UTF-8'))
        self.__print_attribute('deleteoldrdn', b'1' if delold else b'0')
        self.__end_entry()


reconnect: bool = False
connection: ldap.ldapobject | None = None


def connect(ldif: bool = False) -> ldap.ldapobject:
    global connection
    global reconnect

    if connection and not reconnect:
        return connection

    if not os.path.exists(LDIF_FILE) and not ldif:
        # ldap connection
        if not os.path.exists('/etc/ldap/rootpw.conf'):
            pw = new_password()
            init_slapd('restart')
        else:
            pw = get_password()
            if not pw:
                pw = new_password()
                init_slapd('restart')

        local_port = int(listener.configRegistry.get('slapd/port', '7389').split(',')[0])
        connection = ldap.initialize('ldap://127.0.0.1:%d' % (local_port,))
        connection.simple_bind_s('cn=update,' + listener.configRegistry['ldap/base'], pw)
    else:
        connection = LDIFObject(LDIF_FILE)

    reconnect = False
    return connection


def addlist(new: Dict[str, List[bytes]]) -> List[Tuple[str, List[bytes]]]:
    return [kv for kv in new.items() if kv[0].lower() not in EXCLUDE_ATTRIBUTES]


def modlist(old: Dict[str, List[bytes]], new: Dict[str, List[bytes]]) -> List[Tuple[int, str, List[bytes]]]:
    ml: List[Tuple[int, str, List[bytes]]] = []
    for key, values in new.items():
        if key.lower() in EXCLUDE_ATTRIBUTES:
            continue

        if key not in old:
            ml.append((ldap.MOD_ADD, key, values))
            continue

        set_old = set(old[key])
        set_new = set(values)
        if set_old == set_new:
            continue

        if key == 'uniqueMember':
            # triggers slapd-memberof, where REPLACE is inefficient (Bug #48545)
            added_items = set_new - set_old
            removed_items = set_old - set_new
            if removed_items:
                ml.append((ldap.MOD_DELETE, key, list(removed_items)))
            if added_items:
                ml.append((ldap.MOD_ADD, key, list(added_items)))
            continue

        ml.append((ldap.MOD_REPLACE, key, values))

    for key in old:
        if key.lower() in EXCLUDE_ATTRIBUTES:
            continue
        if key not in new:
            ml.append((ldap.MOD_DELETE, key, []))

    return ml


def subschema_oids_with_sup(subschema: ldap.schema.subentry.SubSchema, ldap_type: ldap.schema.SchemaElement, oid: str, result: List[str]) -> None:
    if oid in BUILTIN_OIDS or oid in result:
        return

    obj = subschema.get_obj(ldap_type, oid)
    for i in obj.sup:
        sup_obj = subschema.get_obj(ldap_type, i)
        subschema_oids_with_sup(subschema, ldap_type, sup_obj.oid, result)
    result.append(oid)


def subschema_sort(subschema: ldap.schema.subentry.SubSchema, ldap_type: ldap.schema.SchemaElement) -> List[str]:
    result: List[str] = []
    for oid in subschema.listall(ldap_type):
        subschema_oids_with_sup(subschema, ldap_type, oid, result)
    return result


def update_schema(attr: Dict[str, List[bytes]]) -> None:
    def _insert_linebreak(obj: str) -> str:
        # Bug 46743: Ensure lines are not longer than 2000 characters or slapd fails to start
        max_length = 2000
        obj_lines = []
        while len(obj) > max_length:
            linebreak_postion = obj.rindex(' ', 0, max_length)
            obj_lines.append(obj[:linebreak_postion])
            obj = obj[linebreak_postion + 1:]
        obj_lines.append(obj)
        return '\n '.join(obj_lines)

    listener.setuid(0)
    try:
        fp = open('/var/lib/univention-ldap/schema.conf.new', 'w')
    finally:
        listener.unsetuid()

    print('# This schema was automatically replicated from the Primary Directory Node', file=fp)
    print('# Please do not edit this file\n', file=fp)
    subschema = ldap.schema.SubSchema(attr)

    for oid in subschema_sort(subschema, ldap.schema.AttributeType):
        if oid in BUILTIN_OIDS:
            continue
        obj = _insert_linebreak(str(subschema.get_obj(ldap.schema.AttributeType, oid)))
        print('attributetype %s' % (obj,), file=fp)

    for oid in subschema_sort(subschema, ldap.schema.ObjectClass):
        if oid in BUILTIN_OIDS:
            continue
        obj = _insert_linebreak(str(subschema.get_obj(ldap.schema.ObjectClass, oid)))
        print('objectclass %s' % (obj,), file=fp)

    fp.close()

    # move temporary file
    listener.setuid(0)
    try:
        os.rename('/var/lib/univention-ldap/schema.conf.new', '/var/lib/univention-ldap/schema.conf')
    finally:
        listener.unsetuid()

    init_slapd('restart')


def getOldValues(ldapconn: ldap.ldapobject, dn: str) -> Dict[str, List[bytes]]:
    """
    get "old" from local ldap server
    "ldapconn": connection to local ldap server
    """
    if not isinstance(ldapconn, LDIFObject):
        try:
            res = ldapconn.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['*', '+'])
        except ldap.NO_SUCH_OBJECT as ex:
            ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL not found: %s %s" % (dn, ex))
            old = {}
        else:
            try:
                ((_dn, old),) = res
                entryCSN = old.get('entryCSN', None)
                ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL found result: %s %s" % (dn, entryCSN))
            except (TypeError, ValueError) as ex:
                ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL empty result: %s: %s" % (dn, ex))
                old = {}
    else:
        ud.debug(ud.LISTENER, ud.ALL, "replication: LDIF empty result: %s" % (dn,))
        old = {}

    return old


def _delete_dn_recursive(lo: ldap.ldapobject, dn: str) -> None:
    try:
        lo.delete_s(dn)
    except ldap.NOT_ALLOWED_ON_NONLEAF:
        ud.debug(ud.LISTENER, ud.WARN, 'replication: Failed to delete non leaf object: dn=[%s];' % dn)
        dns = [dn2 for dn2, _attr in lo.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)', attrlist=['dn'], attrsonly=1)]
        dns.reverse()
        for dn in dns:
            lo.delete_s(dn)
    except ldap.NO_SUCH_OBJECT:
        pass


def _backup_dn_recursive(lo: ldap.ldapobject, dn: str) -> None:
    if isinstance(lo, LDIFObject):
        return

    backup_file = os.path.join(BACKUP_DIR, str(time.time()))
    ud.debug(ud.LISTENER, ud.PROCESS, 'replication: dump %s to %s' % (dn, backup_file))
    with open(backup_file, 'w+') as fd:
        os.fchmod(fd.fileno(), 0o600)
        ldif_writer = ldifparser.LDIFWriter(fd)
        for dn, entry in lo.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)', attrlist=['*', '+']):
            ldif_writer.unparse(dn, entry)


def _remove_file(pathname: str) -> None:
    ud.debug(ud.LISTENER, ud.ALL, 'replication: removing %s' % (pathname,))
    try:
        os.remove(pathname)
    except OSError as ex:
        if ex.errno != ENOENT:
            ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to remove %s: %s' % (pathname, ex))


def _add_object_from_new(lo: ldap.ldapobject, dn: str, new: Dict[str, List[bytes]]) -> None:
    al = addlist(new)
    try:
        lo.add_s(dn, al)
    except ldap.OBJECT_CLASS_VIOLATION as ex:
        log_ldap(ud.ERROR, 'object class violation while adding', ex, dn=dn)


def _modify_object_from_old_and_new(lo: ldap.ldapobject, dn: str, old: Dict[str, List[bytes]], new: Dict[str, List[bytes]]) -> None:
    ml = modlist(old, new)
    if ml:
        ud.debug(ud.LISTENER, ud.ALL, 'replication: modify: %s' % dn)
        lo.modify_s(dn, ml)


def _read_dn_from_file(filename: str) -> str | None:
    old_dn = None

    try:
        with open(filename) as fd:
            old_dn = fd.read()
    except OSError as ex:
        ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to open/read modrdn file %s: %s' % (filename, ex))

    return old_dn


def check_file_system_space() -> None:
    if not listener.configRegistry.is_true('ldap/replication/filesystem/check'):
        return

    stat = os.statvfs(LDAP_DIR)
    free_space = stat.f_bavail * stat.f_frsize
    limit = float(listener.configRegistry.get('ldap/replication/filesystem/limit', '10')) * 1024.0 * 1024.0
    if free_space >= limit:
        return

    fqdn = '%(hostname)s.%(domainname)s' % listener.configRegistry
    ud.debug(ud.LISTENER, ud.ERROR, 'replication: Critical disk space. The Univention LDAP Listener was stopped')
    msg = MIMEText(
        'The Univention LDAP Listener process was stopped on %s.\n\n\n'
        'The result of statvfs(%s):\n'
        ' %r\n\n'
        'Please free up some disk space and restart the Univention LDAP Listener with the following command:\n'
        'systemctl restart univention-directory-listener' % (fqdn, LDAP_DIR, stat))
    msg['Subject'] = 'Alert: Critical disk space on %s' % (fqdn,)
    sender = 'root'
    recipient = listener.configRegistry.get('ldap/replication/filesystem/recipient', sender)

    msg['From'] = sender
    msg['To'] = recipient

    s = smtplib.SMTP()
    s.connect()
    s.sendmail(sender, [recipient], msg.as_string())
    s.close()

    listener.run('/usr/bin/systemctl', ['systemctl', 'stop', 'univention-directory-listener'], uid=0, wait=True)


def handler(dn: str, new: Dict[str, List[bytes]], listener_old: Dict[str, List[bytes]], operation: str) -> Any:
    global reconnect
    if not slave:
        return 1

    check_file_system_space()

    ud.debug(ud.LISTENER, ud.INFO, 'replication: Running handler %s for: %s' % (operation, dn))
    if dn == 'cn=Subschema':
        return update_schema(new)

    connect_count = 0
    connected = 0

    while connect_count <= MAX_LDAP_RETRIES and not connected:
        try:
            lo = connect()
        except ldap.LDAPError as ex:
            connect_count += 1
            if connect_count > MAX_LDAP_RETRIES:
                log_ldap(ud.ERROR, 'going into LDIF mode', ex)
                reconnect = True
                lo = connect(ldif=True)
            else:
                log_ldap(ud.WARN, 'Can not connect LDAP Server, retry in 10 seconds', ex)
                reconnect = True
                time.sleep(10)
        else:
            connected = 1

    if 'pwdAttribute' in new and new['pwdAttribute'][0] == b'userPassword':
        new['pwdAttribute'] = [b'2.5.4.35']

    try:
        # Read old entry directly from LDAP server
        if not isinstance(lo, LDIFObject):
            old = getOldValues(lo, dn)

            if ud.get_level(ud.LISTENER) >= ud.INFO:
                # Check if both entries really match
                match = True
                if len(old) != len(listener_old):
                    ud.debug(ud.LISTENER, ud.INFO, 'replication: LDAP keys=%s; listener keys=%s' % (list(old.keys()), list(listener_old.keys())))
                    match = False
                else:
                    for k in old:
                        if k in EXCLUDE_ATTRIBUTES:
                            continue
                        if k not in listener_old:
                            ud.debug(ud.LISTENER, ud.INFO, 'replication: listener does not have key %s' % (k,))
                            match = False
                            break
                        if len(old[k]) != len(listener_old[k]):
                            ud.debug(ud.LISTENER, ud.INFO, 'replication: LDAP and listener values diff for %s' % (k,))
                            match = False
                            break
                        for v in old[k]:
                            if v not in listener_old[k]:
                                ud.debug(ud.LISTENER, ud.INFO, 'replication: listener does not have value for key %s' % (k,))
                                match = False
                                break
                if not match:
                    ud.debug(ud.LISTENER, ud.INFO, 'replication: old entries from LDAP server and Listener do not match')
        else:
            old = listener_old

        # add
        if new:
            if os.path.exists(CURRENT_MODRDN) and not isinstance(lo, LDIFObject):
                target_uuid_file = os.readlink(CURRENT_MODRDN)
                old_dn = _read_dn_from_file(CURRENT_MODRDN)

                new_entryUUID = new['entryUUID'][0].decode('ASCII')
                modrdn_cache = os.path.join(STATE_DIR, new_entryUUID)
                if modrdn_cache == target_uuid_file:
                    ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename phase II: %s (entryUUID=%s)' % (dn, new_entryUUID))

                    if old:
                        # this means the target already exists, we have to delete this old object
                        ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the rename target already exists in the local LDAP, backup and remove the dn: %s' % (dn,))
                        _backup_dn_recursive(lo, dn)
                        _delete_dn_recursive(lo, dn)

                    if getOldValues(lo, old_dn):  # FIXME: mypy old_dn ? None
                        # the normal rename is possible
                        new_dn = ldap.dn.str2dn(dn)
                        new_parent = ldap.dn.dn2str(new_dn[1:])
                        new_rdn = ldap.dn.dn2str([new_dn[0]])

                        delold = 0
                        for (key, value, _typ) in ldap.dn.str2dn(old_dn)[0]:
                            if key not in new:
                                ud.debug(ud.LISTENER, ud.ALL, 'replication: move: attr %s not present' % (key,))
                                delold = 1
                            elif value not in new[key]:
                                ud.debug(ud.LISTENER, ud.ALL, 'replication: move: val %s not present in attr %s' % (value, new[key]))
                                delold = 1

                        ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename from %s to %s' % (old_dn, dn))
                        lo.rename_s(old_dn, new_rdn, new_parent, delold=delold)
                        _remove_file(modrdn_cache)
                    else:
                        # the old object does not exists, so we have to re-create the new object
                        ud.debug(ud.LISTENER, ud.ALL, 'replication: the local target does not exist, so the object will be added: %s' % dn)
                        _add_object_from_new(lo, dn, new)
                        _remove_file(modrdn_cache)
                else:  # current_modrdn points to a different file
                    ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the current modrdn points to a different entryUUID: %s' % (target_uuid_file,))

                    if old_dn:
                        ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the DN %s from the %s has to be backuped and removed' % (old_dn, CURRENT_MODRDN))
                        _backup_dn_recursive(lo, old_dn)
                        _delete_dn_recursive(lo, old_dn)
                    else:
                        ud.debug(ud.LISTENER, ud.WARN, 'replication: no old dn has been found')

                    if not old:
                        _add_object_from_new(lo, dn, new)
                    elif old:
                        _modify_object_from_old_and_new(lo, dn, old, new)

                _remove_file(CURRENT_MODRDN)

            elif old:  # modify: new and old
                _modify_object_from_old_and_new(lo, dn, old, new)

            else:  # add: new and not old
                _add_object_from_new(lo, dn, new)

        # delete
        elif old and not new:
            if operation == 'r':  # check for modrdn phase 1
                old_entryUUID = old['entryUUID'][0].decode('ASCII')
                ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename phase I: %s (entryUUID=%s)' % (dn, old_entryUUID))
                modrdn_cache = os.path.join(STATE_DIR, old_entryUUID)
                try:
                    with open(modrdn_cache, 'w') as fd:
                        os.fchmod(fd.fileno(), 0o600)
                        fd.write(dn)
                    _remove_file(CURRENT_MODRDN)
                    os.symlink(modrdn_cache, CURRENT_MODRDN)
                    # that's it for now for command 'r' ==> modrdn will follow in the next step
                    return
                except OSError as ex:
                    # d'oh! output some message and continue doing a delete+add instead
                    ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to open/write modrdn file %s: %s' % (modrdn_cache, ex))

            ud.debug(ud.LISTENER, ud.ALL, 'replication: delete: %s' % dn)
            _delete_dn_recursive(lo, dn)
    except ldap.SERVER_DOWN as ex:
        log_ldap(ud.WARN, 'retrying', ex)
        reconnect = True
        handler(dn, new, listener_old, operation)
    except ldap.ALREADY_EXISTS as ex:
        log_ldap(ud.WARN, 'trying to apply changes', ex, dn=dn)
        try:
            cur = lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)')[0][1]
        except ldap.LDAPError as ex:
            log_ldap(ud.ERROR, 'going into LDIF mode', ex)
            reconnect = True
            connect(ldif=True)
            handler(dn, new, listener_old, operation)
        else:
            handler(dn, new, cur, operation)
    except ldap.CONSTRAINT_VIOLATION as ex:
        log_ldap(ud.ERROR, 'Constraint violation', ex, dn=dn)
    except ldap.LDAPError as ex:
        log_ldap(ud.ERROR, 'Error', ex, dn=dn)
        if listener.configRegistry.get('ldap/replication/fallback', 'ldif') == 'restart':
            ud.debug(ud.LISTENER, ud.ERROR, 'replication: Uncaught LDAPError. Exiting Univention Directory Listener to retry replication with an updated copy of the current upstream object.')
            sys.exit(1)  # retry a bit later after restart via runsv
        else:
            reconnect = True
            connect(ldif=True)
            handler(dn, new, listener_old, operation)


def log_ldap(severity: int, msg: str, ex: ldap.LDAPError, dn: str | None = None) -> None:
    """
    Log LDAP exception with details.

    :param int severity: Severity level of message.
    :param str msg: Additional message text.
    :param ldap.LDAPError ex: the LDAP exception to log.
    :param str dn: Distinguished name which triggered the exception.

    >>> ud.debug = lambda facility, level, txt: sys.stdout.write(txt.lstrip()+chr(10))

    >>> # ldap.initialize('xxx')
    >>> log_ldap(ud.ALL, 'MSG', ldap.LDAPError(2, 'No such file or directory'))
    replication: LDAPError(2, 'No such file or directory'): MSG

    >>> # ldap.initialize('ldap://localhost:9').whoami_s()
    >>> log_ldap(ud.ALL, 'MSG', ldap.SERVER_DOWN({
    ...         'info': 'Transport endpoint is not connected',
    ...         'errno': 107,
    ...         'desc': u"Can't contact LDAP server",
    ...     },))
    replication: Can't contact LDAP server: MSG
    additional info: Transport endpoint is not connected

    >>> log_ldap(ud.ALL, 'MSG', ldap.LDAPError({'errnum': 42}))
    replication: LDAPError({'errnum': 42},): MSG

    >>> # ldap.dn.str2dn('x')
    >>> log_ldap(ud.ALL, 'MSG', ldap.DECODING_ERROR())
    replication: DECODING_ERROR(): MSG
    """
    try:
        args, = ex.args
        desc = args['desc']
    except (ValueError, LookupError):
        args = {}
        desc = '%s%r' % (type(ex).__name__, ex.args)

    ud.debug(ud.LISTENER, severity, 'replication: %s%s: %s' % (desc, '; dn="%s"' % (dn,) if dn else '', msg))

    try:
        ud.debug(ud.LISTENER, severity, '\tadditional info: %(info)s' % args)
    except LookupError:
        pass

    try:
        ud.debug(ud.LISTENER, severity, '\tmachted dn: %(matched)s' % args)
    except LookupError:
        pass


def clean() -> Any:
    if not slave:
        return 1
    ud.debug(ud.LISTENER, ud.INFO, 'replication: removing cache')
    # init_slapd('stop')

    # FIXME
    listener.run('/usr/bin/killall', ['killall', '-9', 'slapd'], uid=0)
    time.sleep(1)  # FIXME

    dirname = '/var/lib/univention-ldap/ldap'
    listener.setuid(0)
    try:
        for filename in os.listdir(dirname):
            filename = os.path.join(dirname, filename)
            try:
                os.unlink(filename)
            except OSError:
                pass
        if os.path.exists(LDIF_FILE):
            os.unlink(LDIF_FILE)
    finally:
        listener.unsetuid()
    listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry', 'commit', '/var/lib/univention-ldap/ldap/DB_CONFIG'], uid=0)


def initialize() -> Any:
    ud.debug(ud.LISTENER, ud.INFO, 'replication: initialize')
    if not slave:
        ud.debug(ud.LISTENER, ud.INFO, 'replication: not a Replica Node')
        return 1
    clean()
    ud.debug(ud.LISTENER, ud.INFO, 'replication: initializing cache')
    new_password()
    init_slapd('start')


def randpw(length: int = 64) -> str:
    """
    Create random password.
    >>> randpw().isalnum()
    True
    """
    password = subprocess.check_output([
        'pwgen',
        '--numerals',
        '--capitalize',
        '--secure',
        str(length),
        '1',
    ]).decode('ASCII').strip()
    return password


def new_password() -> str:
    pw = randpw()

    listener.setuid(0)
    try:
        with open(ROOTPW_FILE, 'w') as fd:
            os.fchmod(fd.fileno(), 0o600)
            print('rootpw "%s"' % (pw.replace('\\', '\\\\').replace('"', '\\"'),), file=fd)
    finally:
        listener.unsetuid()

    return pw


def get_password() -> str:
    listener.setuid(0)
    try:
        with open(ROOTPW_FILE) as fd:
            for line in fd:
                match = get_password.RE_ROOTDN.match(line)
                if match:
                    return match.group(1).replace('\\"', '"').replace('\\\\', '\\')
            return ''
    finally:
        listener.unsetuid()


get_password.RE_ROOTDN = re.compile(r'^rootpw[ \t]+"((?:[^"\\]|\\["\\])+)"')


def init_slapd(arg: str) -> None:
    listener.run('/etc/init.d/slapd', ['slapd', arg], uid=0)
    time.sleep(1)
