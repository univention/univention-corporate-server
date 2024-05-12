#!/usr/share/ucs-test/runner python3
## desc: Modify and move an object while the listener is stopped
## tags:
##  - replication
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
##  - domaincontroller_slave
## packages:
##  - univention-config
##  - univention-directory-manager-tools
##  - ldap-utils
## bugs:
##  - 34355
## exposure: dangerous

import sys
from contextlib import contextmanager, suppress
from pathlib import Path
from tempfile import mkdtemp
from typing import Iterator

import ldap

import univention.testing.udm as udm_test
from univention import uldap
from univention.config_registry import ucr
from univention.testing.strings import random_name
from univention.testing.utils import restart_listener, start_listener, stop_listener, wait_for_replication


success = True


def get_entryUUID(lo: uldap.access, dn: str) -> bytes:
    result = lo.search(base=dn, scope=ldap.SCOPE_BASE, attr=['*', '+'])
    print(f'DN: {dn}\n{result}')
    return result[0][1].get('entryUUID')[0]


@contextmanager
def create_listener(computer_name: str) -> Iterator[Path]:
    tmp = Path(mkdtemp())
    flag = tmp / "flag"

    fname = Path('/usr/lib/univention-directory-listener/system') / f'{computer_name}-test.py'
    fname.write_text('''
from __future__ import absolute_import, annotations

import univention.debug as ud

modrdn = "1"
name = "%(computer_name)s-test"
description = "%(computer_name)s"
filter = "(cn=%(computer_name)s)"

def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]], command: str) -> None:
    if command == 'r':
        return
    ud.debug(ud.LISTENER, ud.PROCESS, "ucs-test debug: dn: %%s" %% dn)
    ud.debug(ud.LISTENER, ud.PROCESS, "ucs-test debug: old: %%s" %% old)
    ud.debug(ud.LISTENER, ud.PROCESS, "ucs-test debug: new: %%s" %% new)
    if old and not new:
        fd = open('%(flag)s', 'w')
''' % {'computer_name': computer_name, 'flag': flag.as_posix()})
    restart_listener()

    try:
        yield flag
    finally:
        fname.unlink()
        restart_listener()
        with suppress(FileNotFoundError):
            flag.unlink()  # Py3.8+: missing_ok=True
        tmp.rmdir()

# create computer


container_name = random_name()
computer_name = random_name()

with create_listener(computer_name) as delete_handler_file, udm_test.UCSTestUDM() as udm:
    position = 'cn=memberserver,cn=computers,%s' % (ucr.get('ldap/base'))
    container = udm.create_object('container/cn', name=container_name, position=position, wait_for_replication=True)
    computer = udm.create_object('computers/linux', name=computer_name, position=container, wait_for_replication=True)

    lo = uldap.getMachineConnection()

    # read computer uuid
    computer_UUID = get_entryUUID(lo, computer)

    # Stop listener
    stop_listener()

    udm.modify_object('computers/linux', dn=computer, description=computer_name, wait_for_replication=False)

    # move container to the same position of the new container
    new_computer_dn = f'cn={computer_name},{position}'
    udm.move_object('computers/linux', dn=computer, position=position, wait_for_replication=False)

    start_listener()

    wait_for_replication()

    new_computer_UUID = get_entryUUID(lo, new_computer_dn)

    # The container should have be replaced by the computer object
    if computer_UUID != new_computer_UUID:
        print('ERROR: entryUUID of moved object do not match')
        success = False

    if delete_handler_file.exists():
        print('ERROR: the delete handler was called for the modified and moved object')
        success = False

wait_for_replication()

sys.exit(0 if success else 1)

# vim: set ft=python :
