# SPDX-FileCopyrightText: 2021-2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Dict, List


modrdn = "1"

_delay = None


def handler(
        dn: str,
        new: Dict[str, List[bytes]],
        old: Dict[str, List[bytes]],
        command: str = "",
) -> None:
    global _delay
    if _delay:
        old_dn, old = _delay
        _delay = None
        if command == "a" and old['entryUUID'] == new['entryUUID']:
            handler_move(old_dn, old, dn, new)
            return
        handler_remove(old_dn, old)

    if command == "n" and dn == "cn=Subschema":
        handler_schema(old, new)
    elif new and not old:
        handler_add(dn, new)
    elif new and old:
        handler_modify(dn, old, new)
    elif not new and old:
        if command == "r":
            _delay = (dn, old)
        else:
            handler_remove(dn, old)
    else:
        pass  # ignore, reserved for future use


def handler_add(dn: str, new: Dict[str, List[bytes]]) -> None:
    """Handle creation of object."""
    # replace this


def handler_modify(
        dn: str,
        old: Dict[str, List[bytes]],
        new: Dict[str, List[bytes]],
) -> None:
    """Handle modification of object."""
    # replace this


def handler_remove(dn: str, old: Dict[str, List[bytes]]) -> None:
    """Handle removal of object."""
    # replace this


def handler_move(
        old_dn: str,
        old: Dict[str, List[bytes]],
        new_dn: str,
        new: Dict[str, List[bytes]],
) -> None:
    """Handle rename or move of object."""
    # replace this


def handler_schema(
        old: Dict[str, List[bytes]],
        new: Dict[str, List[bytes]],
) -> None:
    """Handle change in LDAP schema."""
    # replace this
