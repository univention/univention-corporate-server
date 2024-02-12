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

import logging
import os
import re

import pytest

import univention.debug as ud


def test_logging_handler_changed():
    m = logging.getLogger('MAIN')
    f = logging.getLogger('foo')
    assert type(m) is logging.Logger
    import univention.logging

    assert type(m) is univention.logging.Logger
    assert type(f) is logging.Logger
    univention.logging.extendLogger('foo', univention_debug_category='MAIN')
    assert type(f) is univention.logging.Logger


@pytest.fixture()
def tmplog(tmpdir):
    """Setup temporary logging."""
    return tmpdir.ensure('log')


def test_logging_basic_config(tmplog, parse):
    import univention.logging

    pid = os.getpid()
    univention.logging.basicConfig(filename=str(tmplog), level=logging.INFO, log_pid=True, univention_debug_flush=True, univention_debug_function=False, do_exit=True)
    logger = logging.getLogger('LDAP')
    logger.debug('test_debug')
    logger.info('test_info')
    logger.warning('test_warn')
    logger.set_log_pid(True)
    child = logger.getChild('foo')
    child.error('test_error')
    logger.critical('test_critical')
    logger.set_ud_level(ud.ERROR)
    logger.warning('no warning displayed')
    child.warning('no warning displayed')
    logger.set_log_pid(False)
    logger.setLevel(logging.DEBUG)
    logger.reopen()
    logger.debug('test_debug')
    logger.setLevel(logging.NOTSET + 1)
    logger.log(9, 'test ultra debug')
    logger.log(1, 'test ultra debug')

    output = tmplog.read()
    logs = list(parse(output))
    assert logs[0][0] == 'init'
    assert [(y['category'], y['level'], re.sub(r':\d+:', ':', y['msg'])) for x, y in logs[1:]] == [
        ('LDAP', 'PROCESS', '%d: test_info' % pid),
        ('LDAP', 'WARN', '%d: test_warn' % pid),
        ('LDAP', 'ERROR', 'foo: %d: test_error' % pid),
        ('LDAP', 'ERROR', '%d: test_critical' % pid),
        ('LDAP', 'INFO', 'test_debug'),
        ('LDAP', 'ALL', 'test_logging.test_logging_basic_config: test ultra debug'),
        ('LDAP', '99', 'test_logging.test_logging_basic_config: test ultra debug'),
    ]


@pytest.mark.parametrize(
    'ud_level,log_level',
    [
        (ud.ERROR, logging.ERROR),
        (ud.WARN, logging.WARNING),
        (ud.PROCESS, logging.INFO),
        (ud.INFO, logging.DEBUG),
        (ud.ALL, 9),
        (100, logging.NOTSET),
    ],
)
def test_loglevel_mapping_exact(ud_level, log_level):
    from univention.logging import _map_level_to_ud, _map_ud_to_level

    assert _map_ud_to_level(ud_level) == log_level
    assert _map_level_to_ud(log_level) == ud_level


@pytest.mark.parametrize(
    'ud_level,log_level',
    [
        (x, y)
        for z, y in [
            (range(5, 20), 9),
            ([20], 9),
            (range(21, 30), 8),
            ([30], 8),
            (range(31, 40), 7),
            ([40], 7),
            (range(41, 50), 6),
            ([50], 6),
            (range(51, 60), 5),
            ([60], 5),
            (range(61, 70), 4),
            ([70], 4),
            (range(71, 80), 3),
            ([80], 3),
            (range(81, 90), 2),
            ([90], 2),
            (range(91, 100), 1),
            ([100], 0),
        ]
        for x in z
    ],
)
def test_loglevel_mapping_ud(ud_level, log_level):
    from univention.logging import _map_ud_to_level

    assert _map_ud_to_level(ud_level) == log_level


@pytest.mark.parametrize(
    'log_level,ud_level',
    [
        (0, 100),
        (1, 99),
        (2, 89),
        (3, 79),
        (4, 69),
        (5, 59),
        (6, 49),
        (7, 39),
        (8, 29),
        (9, 4),
    ]
    + [
        (x, y)
        for z, y in [
            (range(logging.DEBUG + 1, logging.INFO), ud.INFO),
            (range(logging.INFO + 1, logging.WARNING), ud.PROCESS),
            (range(logging.WARNING + 1, logging.ERROR), ud.WARN),
            ([100], ud.ERROR),
        ]
        for x in z
    ]
    + [
        (x, y)
        for y, z in [
            (ud.ERROR, range(logging.ERROR + 1, 101)),
        ]
        for x in z
    ],
)
def test_loglevel_mapping_logging(log_level, ud_level):
    from univention.logging import _map_level_to_ud

    assert _map_level_to_ud(log_level) == ud_level
