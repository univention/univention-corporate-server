# SPDX-FileCopyrightText: 2021-2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Dict, List


def handler(
        dn: str,
        new: Dict[str, List[bytes]],
        old: Dict[str, List[bytes]],
) -> None:
    if new and not old:
        handler_add(dn, new)
    elif new and old:
        handler_modify(dn, old, new)
    elif not new and old:
        handler_remove(dn, old)
    else:
        pass  # ignore


def handler_add(dn: str, new: Dict[str, List[bytes]]) -> None:
    """Handle addition of object."""
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
