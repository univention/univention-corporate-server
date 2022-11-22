#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2024 Univention GmbH
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import re
from datetime import datetime

import pytest


try:
    from typing import Callable, Dict, Iterator, Tuple  # noqa: F401
except ImportError:
    pass


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


@pytest.fixture()
def parse():
    # type: () -> Iterator[Callable[[str], Iterator[Tuple[str, Dict[str, str]]]]]
    """Setup parser."""
    now = datetime.now()
    start = now.replace(microsecond=now.microsecond - now.microsecond % 1000)

    def f(text):
        # type: (str) -> Iterator[Tuple[str, Dict[str, str]]]
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
