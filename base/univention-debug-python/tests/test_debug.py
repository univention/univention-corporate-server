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


import os
import sys

import pytest
from conftest import CATEGORY, LEVEL

import univention.debug as ud


@pytest.fixture()
def tmplog(tmpdir):
    """Setup temporary logging."""
    tmp = tmpdir.ensure('log')
    fd = ud.init(str(tmp), ud.NO_FLUSH, ud.FUNCTION)
    assert hasattr(fd, 'write')

    return tmp


@pytest.mark.parametrize('stream,idx', [('stdout', 0), ('stderr', 1)])
def test_stdio(stream, idx, capfd, parse):
    fd = ud.init(stream, ud.NO_FLUSH, ud.FUNCTION)
    assert hasattr(fd, 'write')
    ud.exit()

    output = capfd.readouterr()
    assert [typ for typ, groups in parse(output[idx])] == ['init', 'exit']


def test_file(parse, tmplog):
    ud.exit()

    output = tmplog.read()
    assert [typ for typ, groups in parse(output)] == ['init', 'exit']


@pytest.mark.parametrize('function,expected', [(ud.FUNCTION, ['init', 'begin', 'end', 'exit']), (ud.NO_FUNCTION, ['init', 'exit'])])
def test_function(function, expected, parse, tmplog):
    def f():
        _d = ud.function('f')  # noqa: F841
        _d  # noqa: B018

    ud.set_function(function)
    f()
    ud.exit()

    output = tmplog.read()
    assert [typ for typ, groups in parse(output)] == expected


def test_level_set(tmplog):
    ud.set_level(ud.MAIN, ud.PROCESS)
    level = ud.get_level(ud.MAIN)
    assert level == ud.PROCESS

    ud.exit()


def test_debug_closed():
    ud.debug(ud.MAIN, ud.ALL, "No crash")
    assert True


@pytest.mark.parametrize('name', LEVEL)
def test_level(name, parse, tmplog):
    level = getattr(ud, name)
    ud.set_level(ud.MAIN, level)
    assert level == ud.get_level(ud.MAIN)

    ud.debug(ud.MAIN, ud.ERROR, "Error in main: %%%")
    ud.debug(ud.MAIN, ud.WARN, "Warning in main: %%%")
    ud.debug(ud.MAIN, ud.PROCESS, "Process in main: %%%")
    ud.debug(ud.MAIN, ud.INFO, "Information in main: %%%")
    ud.debug(ud.MAIN, ud.ALL, "All in main: %%%")
    ud.exit()

    output = tmplog.read()
    assert [groups['level'] for typ, groups in parse(output) if typ == 'msg'] == LEVEL[:1 + LEVEL.index(name)]


@pytest.mark.parametrize('name', CATEGORY)
def test_category(name, parse, tmplog):
    category = getattr(ud, name)
    ud.debug(category, ud.ERROR, "Error in main: %%%")
    ud.debug(category, ud.WARN, "Warning in main: %%%")
    ud.debug(category, ud.PROCESS, "Process in main: %%%")
    ud.debug(category, ud.INFO, "Information in main: %%%")
    ud.debug(category, ud.ALL, "All in main: %%%")
    ud.exit()

    output = tmplog.read()
    assert {groups['category'] for typ, groups in parse(output) if typ == 'msg'} == {name}


def test_reopen(parse, tmplog):
    ud.debug(ud.MAIN, ud.ERROR, '1st')
    tmpbak = tmplog.dirpath('bak')
    tmplog.rename(tmpbak)
    ud.reopen()
    ud.debug(ud.MAIN, ud.ERROR, '2nd')
    ud.exit()

    output = tmpbak.read()
    assert [groups['msg'] for typ, groups in parse(output) if typ == 'msg'] == ['1st']

    output = tmplog.read()
    assert [groups['msg'] for typ, groups in parse(output) if typ == 'msg'] == ['2nd']


def test_unicode(parse, tmplog):
    ud.debug(ud.MAIN, ud.ERROR, u'\u2603' if sys.getdefaultencoding() != 'ascii' else u'\u2603'.encode())
    ud.exit()

    output = tmplog.read()
    for ((c_type, c_groups), (e_type, e_groups)) in zip(parse(output), [
            ('init', {}),
            ('msg', {'msg': '\xe2\x98\x83' if sys.version_info.major < 3 else u'\u2603'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for key, val in e_groups.items():
            assert c_groups[key] == val


def test_close(parse, tmpdir):
    """Closing the Python wrapped file should not close the underlying file descriptor."""
    tmp = tmpdir.ensure('log')
    fd = ud.init(str(tmp), ud.NO_FLUSH, ud.FUNCTION)
    fd.close()
    ud.debug(ud.MAIN, ud.ERROR, 'open')
    ud.exit()

    output = tmp.read()
    assert [typ for typ, groups in parse(output)] == ['init', 'msg', 'exit']


def test_fifo(parse, tmpdir):
    """Using a non-seekable file should not crash Python."""
    tmp = tmpdir.join('log')
    os.mkfifo(str(tmp))

    fd = os.open(str(tmp), os.O_RDONLY | os.O_NONBLOCK)
    try:
        ud.init(str(tmp), ud.NO_FLUSH, ud.FUNCTION)
        ud.exit()
        output = os.read(fd, 4096).decode('ascii')
    finally:
        os.close(fd)

    assert [typ for typ, groups in parse(output)] == ['init', 'exit']


def test_trace_plain(parse, tmplog):
    @ud.trace(with_args=False)
    def f():
        pass

    ud.set_function(ud.FUNCTION)
    assert f() is None
    ud.exit()

    output = tmplog.read()
    for ((c_type, c_groups), (e_type, e_groups)) in zip(parse(output), [
            ('init', {}),
            ('begin', {'begin': 'test_debug.f(...): ...'}),
            ('end', {'end': 'test_debug.f(...): ...'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for key, val in e_groups.items():
            assert c_groups[key] == val


def test_trace_detail(parse, tmplog):
    @ud.trace(with_args=True, with_return=True, repr=repr)
    def f(args):
        return 42

    ud.set_function(ud.FUNCTION)
    assert f('in') == 42
    ud.exit()

    output = tmplog.read()
    for ((c_type, c_groups), (e_type, e_groups)) in zip(parse(output), [
            ('init', {}),
            ('begin', {'begin': "test_debug.f('in'): ..."}),
            ('end', {'end': 'test_debug.f(...): 42'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for key, val in e_groups.items():
            assert c_groups[key] == val


def test_trace_exception(parse, tmplog):
    @ud.trace(with_args=False)
    def f():
        raise ValueError(42)

    ud.set_function(ud.FUNCTION)
    with pytest.raises(ValueError):
        f()
    ud.exit()

    output = tmplog.read()
    for ((c_type, c_groups), (e_type, e_groups)) in zip(parse(output), [
            ('init', {}),
            ('begin', {'begin': 'test_debug.f(...): ...'}),
            ('end', {'end': "test_debug.f(...): %r(42)" % ValueError}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for key, val in e_groups.items():
            assert c_groups[key] == val
