# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def handler(
    dn: str,
    new: dict[str, list[bytes]],
    old: dict[str, list[bytes]],
) -> None:
    if new and not old:
        handler_add(dn, new)
    elif new and old:
        handler_modify(dn, old, new)
    elif not new and old:
        handler_remove(dn, old)
    else:
        pass  # ignore


def handler_add(dn: str, new: dict[str, list[bytes]]) -> None:
    """Handle addition of object."""
    # replace this


def handler_modify(
    dn: str,
    old: dict[str, list[bytes]],
    new: dict[str, list[bytes]],
) -> None:
    """Handle modification of object."""
    # replace this


def handler_remove(dn: str, old: dict[str, list[bytes]]) -> None:
    """Handle removal of object."""
    # replace this
