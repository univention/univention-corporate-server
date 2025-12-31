#!/usr/bin/python3
#
# Univention AD Connector
#  Univention LDAP Listener script for the ad connector
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import pickle  # noqa: S403
import shutil
import subprocess
import time
from logging import getLogger

from univention.logging import Structured

import listener


log = Structured(getLogger("LDAP").getChild(__name__))

description = 'AD Connector replication'
filter = '(!(objectClass=lock))'
modrdn = "1"

# While initialize copy all group objects into a list:
# https://forge.univention.org/bugzilla/show_bug.cgi?id=18619#c5
init_mode = False
group_objects = []
connector_needs_restart = False

dirs = [listener.configRegistry['connector/ad/listener/dir']]
if listener.configRegistry.get('connector/listener/additionalbasenames'):
    for configbasename in listener.configRegistry['connector/listener/additionalbasenames'].split(' '):
        if listener.configRegistry.get(f'{configbasename}/ad/listener/dir'):
            dirs.append(listener.configRegistry[f'{configbasename}/ad/listener/dir'])
        else:
            log.warning("ad-connector: additional config basename %s given, but %s/ad/listener/dir not set; ignore basename.", configbasename, configbasename)
dirs = [dir_ for dir_ in dirs if dir_]
if not dirs:
    raise ImportError('UCR variable connector/ad/listener/dir needs to be set!')


def _save_old_object(directory: str, dn: str, old: dict[str, list[bytes]] | None) -> None:
    filename = os.path.join(directory, 'tmp', 'old_dn')

    with open(filename, 'wb+') as fd:
        os.chmod(filename, 0o600)
        p = pickle.Pickler(fd)
        p.dump((dn, old))
        p.clear_memo()


def _load_old_object(directory: str) -> tuple[str, dict[str, list[bytes]]]:
    with open(os.path.join(directory, 'tmp', 'old_dn'), 'rb') as fd:
        p = pickle.Unpickler(fd)
        (old_dn, old_object) = p.load()

    return (old_dn, old_object)


def _dump_changes_to_file_and_check_file(directory: str, dn: str, new: dict[str, list[bytes]] | None, old: dict[str, list[bytes]] | None, old_dn: str | None) -> None:
    ob = (dn, new, old, old_dn)

    tmpdir = os.path.join(directory, 'tmp')
    filename = f'{time.time():f}'
    filepath = os.path.join(tmpdir, filename)

    with open(filepath, 'wb+') as fd:
        os.chmod(filepath, 0o600)
        p = pickle.Pickler(fd)
        p.dump(ob)
        p.clear_memo()

    # prevent a race condition between the pickle file is only partly written to disk and then read
    # by moving it to the final location after it is completely written to disk
    shutil.move(filepath, os.path.join(directory, filename))


def _restart_connector() -> None:
    listener.setuid(0)
    try:
        if not subprocess.call(['pgrep', '-f', 'python3.*connector.ad.main']):
            log.process("ad-connector: restarting connector ...")
            subprocess.call(('service', 'univention-ad-connector', 'restart'))
            log.process("ad-connector: ... done")
    finally:
        listener.unsetuid()


def handler(dn: str, new: dict[str, list[bytes]] | None, old: dict[str, list[bytes]] | None, command: str) -> None:
    global connector_needs_restart

    # restart connector on extended attribute changes
    if b'univentionUDMProperty' in new.get('objectClass', []) or b'univentionUDMProperty' in old.get('objectClass', []):
        connector_needs_restart = True
    else:
        if connector_needs_restart is True:
            _restart_connector()
            connector_needs_restart = False

    listener.setuid(0)
    try:
        for directory in dirs:
            if not os.path.exists(os.path.join(directory, 'tmp')):
                os.makedirs(os.path.join(directory, 'tmp'))

            old_dn = None
            old_object: dict[str, list[bytes]] = {}

            if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
                (old_dn, old_object) = _load_old_object(directory)
            if command == 'r':
                _save_old_object(directory, dn, old)
            else:
                # Normally we see two steps for the modrdn operation. But in case of the selective replication we
                # might only see the first step.
                #  https://forge.univention.org/bugzilla/show_bug.cgi?id=32542
                if old_dn and new.get('entryUUID') != old_object.get('entryUUID'):
                    log.process("The entryUUID attribute of the saved object (%s) does not match the entryUUID attribute of the current object (%s). This can be normal in a selective replication scenario.", old_dn, dn)
                    _dump_changes_to_file_and_check_file(directory, old_dn, {}, old_object, None)
                    old_dn = None

                if init_mode and new and b'univentionGroup' in new.get('objectClass', []):
                    group_objects.append((dn, new, old, old_dn))

                _dump_changes_to_file_and_check_file(directory, dn, new, old, old_dn)

                if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
                    os.unlink(os.path.join(directory, 'tmp', 'old_dn'))

    finally:
        listener.unsetuid()


def clean() -> None:
    listener.setuid(0)
    try:
        for directory in dirs:
            for filename in os.listdir(directory):
                if os.path.isfile(filename):
                    os.remove(os.path.join(directory, filename))
            if os.path.exists(os.path.join(directory, 'tmp')):
                for filename in os.listdir(os.path.join(directory, 'tmp')):
                    os.remove(os.path.join(directory, filename))
    finally:
        listener.unsetuid()


def postrun() -> None:
    global init_mode, group_objects, connector_needs_restart
    if init_mode:
        listener.setuid(0)
        try:
            init_mode = False
            for ob in group_objects:
                for directory in dirs:
                    filename = os.path.join(directory, f"{time.time():f}")
                    with open(filename, 'wb+') as fd:
                        os.chmod(filename, 0o600)
                        p = pickle.Pickler(fd)
                        p.dump(ob)
                        p.clear_memo()
            del group_objects
            group_objects = []
        finally:
            listener.unsetuid()
    if connector_needs_restart is True:
        _restart_connector()
        connector_needs_restart = False


def initialize() -> None:
    global init_mode
    init_mode = True
    clean()
