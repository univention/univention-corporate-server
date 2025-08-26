# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Example for a listener module, which logs changes to users."""

import errno
import os
from collections import namedtuple

import univention.debug as ud

from listener import SetUID


description = 'print all names/users/uidNumbers into a file'
filter = ''.join("""\
(&
    (|
        (&
            (objectClass=posixAccount)
            (objectClass=shadowAccount)
        )
        (objectClass=univentionMail)
        (objectClass=sambaSamAccount)
        (objectClass=simpleSecurityObject)
        (objectClass=inetOrgPerson)
    )
    (!(objectClass=univentionHost))
    (!(uidNumber=0))
    (!(uid=*$))
)""".split())  # noqa: SIM905
attributes = ['uid', 'uidNumber', 'cn']
_Rec = namedtuple('_Rec', 'uid uidNumber cn')

USER_LIST = '/root/UserList.txt'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    """
    Write all changes into a text file.
    This function is called on each change.
    """
    if new and old:
        _handle_change(dn, new, old)
    elif new and not old:
        _handle_add(dn, new)
    elif old and not new:
        _handle_remove(dn, old)


def _handle_change(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    """Called when an object is modified."""
    o_rec = _rec(old)
    n_rec = _rec(new)
    ud.debug(ud.LISTENER, ud.INFO, f'Edited user "{o_rec.uid}"')
    _writeit(o_rec, 'edited. Is now:')
    _writeit(n_rec, '')


def _handle_add(dn: str, new: dict[str, list[bytes]]) -> None:
    """Called when an object is newly created."""
    n_rec = _rec(new)
    ud.debug(ud.LISTENER, ud.INFO, f'Added user "{n_rec.uid}"')
    _writeit(n_rec, 'added')


def _handle_remove(dn: str, old: dict[str, list[bytes]]) -> None:
    """Called when an previously existing object is removed."""
    o_rec = _rec(old)
    ud.debug(ud.LISTENER, ud.INFO, f'Removed user "{o_rec.uid}"')
    _writeit(o_rec, 'removed')


def _rec(data: dict[str, list[bytes]]) -> _Rec:
    """Retrieve symbolic, numeric ID and name from user data."""
    return _Rec(*(data.get(attr, (None,))[0] for attr in attributes))


def _writeit(rec: _Rec, comment: str) -> None:
    """Append CommonName, symbolic and numeric User-IDentifier, and comment to file."""
    nuid = '*****' if rec.uid in ('root', 'spam') else rec.uidNumber
    indent = '\t' if comment is None else ''
    try:
        with SetUID(), open(USER_LIST, 'a') as out:
            print(f'{indent}Name: "{rec.cn}"', file=out)
            print(f'{indent}User: "{rec.uid}"', file=out)
            print(f'{indent}UID: "{nuid}"', file=out)
            if comment:
                print(f'{indent}{comment}', file=out)
    except OSError as ex:
        ud.debug(ud.LISTENER, ud.ERROR, f'Failed to write "{USER_LIST}": {ex}')


def initialize() -> None:
    """
    Remove the log file.
    This function is called when the module is forcefully reset.
    """
    try:
        with SetUID():
            os.remove(USER_LIST)
        ud.debug(ud.LISTENER, ud.INFO, f'Successfully deleted "{USER_LIST}"')
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            ud.debug(ud.LISTENER, ud.INFO, f'File "{USER_LIST}" does not exist, will be created')
        else:
            ud.debug(ud.LISTENER, ud.WARN, f'Failed to delete file "{USER_LIST}": {ex}')
