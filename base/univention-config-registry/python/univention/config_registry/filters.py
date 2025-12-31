"""Univention Configuration Registry output filters."""
#  main configuration registry classes
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.config_registry.misc import escape_value, key_shell_escape


try:
    from collections.abc import Iterable
    from typing import Any
except ImportError:  # pragma: no cover
    pass

__all__ = ['filter_keys_only', 'filter_shell', 'filter_sort']


def filter_shell(args: Any, text: Iterable[str]) -> Iterable[str]:  # pylint: disable-msg=W0613
    """
    Filter output for shell: escape keys.

    :param args: UNUSED.
    :param text: Text as list of lines.
    :returns: Filteres list of lines.
    """
    out = []
    for line in text:
        try:
            var, value = line.split(': ', 1)
        except ValueError:
            var = line
            value = ''
        out.append('%s=%s' % (key_shell_escape(var), escape_value(value)))
    return out


def filter_keys_only(args: Any, text: Iterable[str]) -> Iterable[str]:  # pylint: disable-msg=W0613
    """
    Filter output: strip values.

    :param args: UNUSED.
    :param text: Text as list of lines.
    :returns: Filteres list of lines.
    """
    out = []
    for line in text:
        out.append(line.split(': ', 1)[0])
    return out


def filter_sort(args: Any, text: Iterable[str]) -> Iterable[str]:  # pylint: disable-msg=W0613
    """
    Filter output: sort by key.

    :param args: UNUSED.
    :param text: Text as list of lines.
    :returns: Filteres list of lines.
    """
    return sorted(text)
