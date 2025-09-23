#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import re
import shlex
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import pytest


ADR0010_REGEX = re.compile(
    r"^(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.(?P<msec>\d{3,6})\+\d{2}:?\d{2}) +"
    r"(?P<level>\w+?) +(?:\[(?P<request_id>.*?)\] )?(?P<msg>.*?)(?:\t\| (?P<data>.*?))?$",
)
RE_BEGIN = r'UNIVENTION_DEBUG_BEGIN\s{2}:\s(?P<begin>.*)$'
RE_END = r'UNIVENTION_DEBUG_END\s{4}:\s(?P<end>.*)$'
RE = re.compile(f'{ADR0010_REGEX.pattern}$|{RE_BEGIN}|{RE_END}')

LEVEL = ['ERROR', 'WARNING', 'PROCESS', 'INFO', 'DEBUG', 'TRACE']
CATEGORY = [
    'MAIN',
    'LDAP',
    'USERS',
    'NETWORK',
    'SSL',
    'SLAPD',
    'SEARCH',
    'TRANSFILE',
    'LISTENER',
    'POLICY',
    'ADMIN',
    'CONFIG',
    'LICENSE',
    'KERBEROS',
    'DHCP',
    'PROTOCOL',
    'MODULE',
    'ACL',
    'RESOURCES',
    'PARSER',
    'LOCALE',
    'AUTH',
]


@pytest.fixture
def parse() -> Callable[[str], Iterator[tuple[str, dict[str, str]]]]:
    """Setup parser."""
    start = datetime.now(UTC)

    def f(text: str) -> Iterator[tuple[str, dict[str, str]]]:
        """
        Parse line into components.

        :param text: Multi-line text.
        :returns: 2-tuple (typ, data) where `data` is a mapping from regular-expression-group-name to value.
        """
        end = datetime.now(UTC)

        for line in text.splitlines():
            print(repr(line))
            match = RE.match(line)
            assert match, line
            groups = match.groupdict()

            stamp = groups.get('datetime')
            if stamp is not None:
                assert start <= datetime.fromisoformat(stamp) <= end

            groups['category'] = ''
            if groups.get('data'):
                groups['data'] = parse_logfmt(groups['data'])
                groups['category'] = groups['data'].get('logname', '').split('.', 1)[0]

            if groups.get('begin') is not None or groups.get('level') == 'BEGIN':
                yield ('begin', groups)
            elif groups.get('end') is not None or groups.get('level') == 'END':
                yield ('end', groups)
            elif groups.get('level') == 'INIT':
                yield ('init', groups)
            elif groups.get('level') == 'REINIT':
                yield ('reinit', groups)
            elif groups.get('level') == 'EXIT':
                yield ('exit', groups)
            elif groups.get('msg') is not None:
                yield ('msg', groups)
            else:
                raise AssertionError(groups)

    return f


def parse_logfmt(line: str) -> dict[str, str]:
    fields = {}
    aliases = {'exc_info': 'exc', 'stack_info': 'stack'}
    for token in shlex.split(line):
        if '=' in token:
            k, v = token.split('=', 1)
            k = aliases.get(k, k)
            fields[k] = v.replace('\\n', '\n')
        else:
            token = aliases.get(token, token)
            fields[token] = ''
    return fields
