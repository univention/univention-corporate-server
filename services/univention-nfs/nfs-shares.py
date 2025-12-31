#!/usr/bin/python3
#
# Univention NFS
#  listener module: update configuration of local NFS shares
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import operator
import os
import pickle  # noqa: S403
import re

import univention.debug as ud
import univention.lib.listenerSharePath
from univention.config_registry.interfaces import Interfaces

import listener


hostname = listener.configRegistry['hostname']
domainname = listener.configRegistry['domainname']
interfaces = Interfaces(listener.configRegistry)
ip = interfaces.get_default_ip_address().ip

name = 'nfs-shares'
description = 'Create configuration for NFS shares'
filter = '(&(objectClass=univentionShare)(|(univentionShareHost=%s.%s)(univentionShareHost=%s)))' % (hostname, domainname, ip)
modrdn = '1'

__exports = '/etc/exports'
__comment_pattern = re.compile('^"*/.*#[ \t]*LDAP:[ \t]*(.*)')

tmpFile = '/var/cache/univention-directory-listener/nfs-shares.oldObject'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]], command: str) -> None:
    # create tmp dir
    tmpDir = os.path.dirname(tmpFile)
    listener.setuid(0)
    try:
        if not os.path.exists(tmpDir):
            os.makedirs(tmpDir)
    except Exception as exc:
        ud.debug(ud.LISTENER, ud.ERROR, "%s: could not create tmp dir %s (%s)" % (name, tmpDir, exc))
        return
    finally:
        listener.unsetuid()

    # modrdn stuff
    # 'r'+'a' -> renamed
    # command='r' and "not new and old"
    # command='a' and "new and not old"

    # write old object to pickle file
    oldObject = {}
    listener.setuid(0)
    try:
        # object was renamed -> save old object
        if command == "r" and old:
            with open(tmpFile, "wb") as fp:
                os.chmod(tmpFile, 0o600)
                pickle.dump({"dn": dn, "old": old}, fp)
        elif command == "a" and not old and os.path.isfile(tmpFile):
            with open(tmpFile, "rb") as fp:
                p = pickle.load(fp)
            oldObject = p.get("old", {})
            os.remove(tmpFile)
    except Exception as exc:
        if os.path.isfile(tmpFile):
            os.remove(tmpFile)
        ud.debug(ud.LISTENER, ud.ERROR, "%s: could not read/write tmp file %s (%s)" % (name, tmpFile, exc))
    finally:
        listener.unsetuid()

    # update exports file
    lines = _read(lambda match: not match or match.group(1) != _quote(dn))

    if new and b'univentionShareNFS' in new.get('objectClass', []):
        path = new['univentionSharePath'][0].decode('UTF-8')
        options = [
            'rw' if new.get('univentionShareWriteable', [b''])[0] == b'yes' else 'ro',
            'root_squash' if new.get('univentionShareNFSRootSquash', [b''])[0] == b'yes' else 'no_root_squash',
            'async' if new.get('univentionShareNFSSync', [b''])[0] == b'async' else 'sync',
            'subtree_check' if new.get('univentionShareNFSSubTree', [b''])[0] == b'yes' else 'no_subtree_check',
        ] + [cs.decode('UTF-8') for cs in new.get('univentionShareNFSCustomSetting', [])]
        lines.append('%s -%s %s # LDAP:%s' % (
            _exports_escape(path),
            _quote(','.join(options)),
            _quote(' '.join(nfs_allowed.decode('ASCII') for nfs_allowed in new.get('univentionShareNFSAllowed', [b'*']))),
            _quote(dn),
        ))

        _write(lines)

        listener.setuid(0)
        try:
            # object was renamed
            if not old and oldObject and command == "a":
                old = oldObject
            ret = univention.lib.listenerSharePath.createOrRename(old, new, listener.configRegistry)
            if ret:
                ud.debug(ud.LISTENER, ud.ERROR, "%s: rename/create of sharePath for %s failed (%s)" % (name, dn, ret))
        finally:
            listener.unsetuid()
    else:
        _write(lines)


def clean() -> None:
    # clear exports file
    lines = _read(operator.not_)
    _write(lines)


def _read(keep=lambda match: True):
    with open(__exports) as fp:
        return [line.strip() for line in fp if keep(__comment_pattern.match(line))]


def _write(lines: list[str]) -> None:
    listener.setuid(0)
    try:
        ud.debug(ud.LISTENER, ud.PROCESS, 'Writing /etc/exports with %d lines' % (len(lines),))
        with open(__exports, 'w') as fp:
            fp.write('\n'.join(lines) + '\n')
    finally:
        listener.unsetuid()


def _exports_escape(text: str) -> str:
    r"""
    Escape path for /etc/exports.

    According to nfs-utils/support/nfs/xio.c:82 xgettok().
    Bug in parser: r'\134042' double-unescaped '\'

    >>> _exports_escape('foo')
    '"foo"'
    >>> _exports_escape('a b')
    '"a b"'
    >>> _exports_escape('a"b')
    '"a\\042b"'
    """
    return '"%s"' % (''.join(r'\%03o' % (ord(c),) if c < ' ' or c == '"' else c for c in text),)


def _quote(text: str) -> str:
    return _exports_escape(text)[1:-1]


def postrun() -> None:
    listener.run('/bin/systemctl', ['systemctl', 'reload-or-restart', 'nfs-kernel-server.service'], uid=0)
