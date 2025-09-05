#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import re
from collections.abc import Callable, Iterator
from datetime import datetime

import pytest


RE = re.compile(
    r'''
    (?P<datetime>[0-3]\d\.[01]\d\.\d{2}\s[0-2]\d:[0-5]\d:[0-5]\d)\.(?P<msec>\d{3})\s{2}(?P<text>
      (?:DEBUG_INIT
        |DEBUG_EXIT
        |(?P<category>\S+)\s+\(\s(?P<level>\S+)\s+\)\s:\s(?P<msg>.*)
    ))$
    |UNIVENTION_DEBUG_BEGIN\s{2}:\s(?P<begin>.*)$
    |UNIVENTION_DEBUG_END\s{4}:\s(?P<end>.*)$
    ''', re.VERBOSE)
LEVEL = ['ERROR', 'WARN', 'PROCESS', 'INFO', 'ALL']
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
def parse() -> Iterator[Callable[[str], Iterator[tuple[str, dict[str, str]]]]]:
    """Setup parser."""
    now = datetime.now()
    start = now.replace(microsecond=now.microsecond - now.microsecond % 1000)

    def f(text: str) -> Iterator[tuple[str, dict[str, str]]]:
        """
        Parse line into componets.

        :param text: Multi-line text.
        :returns: 2-tuple (typ, data) where `data` is a mapping from regular-expression-group-name to value.
        """
        end = datetime.now()

        for line in text.splitlines():
            print(repr(line))
            match = RE.match(line)
            assert match, line
            groups = match.groupdict()

            stamp = groups.get('datetime')
            if stamp is not None:
                assert start <= datetime.strptime(stamp, '%d.%m.%y %H:%M:%S').replace(microsecond=int(groups['msec']) * 1000) <= end

            if groups.get('begin') is not None:
                yield ('begin', groups)
            elif groups.get('end') is not None:
                yield ('end', groups)
            elif groups.get('text') == 'DEBUG_INIT':
                yield ('init', groups)
            elif groups.get('text') == 'DEBUG_EXIT':
                yield ('exit', groups)
            elif groups.get('text') is not None:
                yield ('msg', groups)
            else:
                raise AssertionError(groups)

    return f


@pytest.fixture
def parse_structured_line() -> Callable[[str], tuple[str, dict[str, str]]]:
    def f(line: str) -> tuple[str, dict[str, str]]:
        message, _, logfmter_data = line[30:].partition('\t| ')
        logfmter_data_dict = {}
        for elem in logfmter_data.split(' '):
            key, value = elem.split('=', 1)
            logfmter_data_dict[key] = value
        return (message, logfmter_data_dict)

    return f
