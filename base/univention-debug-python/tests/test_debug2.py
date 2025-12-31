#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
from logging import DEBUG, getLogger

import pytest
from conftest import CATEGORY, LEVEL

import univention.debug2 as ud


TRACE = DEBUG - 5


@pytest.fixture
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


def test_flush(parse, tmpdir):
    ud.exit()
    tmp = tmpdir.ensure('log')
    fd = ud.init(str(tmp), ud.FLUSH, ud.FUNCTION)
    assert hasattr(fd, 'write')

    ud.debug(ud.MAIN, ud.ERROR, "flush")
    ud.exit()

    output = tmp.read()
    assert [typ for typ, groups in parse(output)] == ['init', 'msg', 'exit']


@pytest.mark.parametrize('function,expected', [(ud.FUNCTION, ['init', 'begin', 'end', 'exit']), (ud.NO_FUNCTION, ['init', 'exit'])])
def test_function(function, expected, parse, tmplog):
    def f():
        _d = ud.function('f')
        _d  # noqa: B018

    ud.set_function(function)
    with pytest.warns(PendingDeprecationWarning):
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
def test_level(name, parse, tmplog, caplog):
    caplog.set_level(TRACE)
    level = getattr(ud, 'WARN' if name == 'WARNING' else name)
    ud.set_level(ud.MAIN, level)
    assert level == ud.get_level(ud.MAIN)

    ud.debug(ud.MAIN, ud.ERROR, "Error in main: %%%")
    ud.debug(ud.MAIN, ud.WARN, "Warning in main: %%%")
    ud.debug(ud.MAIN, ud.PROCESS, "Process in main: %%%")
    ud.debug(ud.MAIN, ud.INFO, "Information in main: %%%")
    ud.debug(ud.MAIN, ud.ALL, "Debug in main: %%%")
    ud.debug(ud.MAIN, ud.TRACE, "Trace in main: %%%")
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
    ud.debug(category, ud.TRACE, "Trace in main: %%%")
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
    ud.debug(ud.MAIN, ud.ERROR, '\u2603')
    ud.exit()

    output = tmplog.read()
    for ((c_type, c_groups), (e_type, e_groups)) in zip(parse(output), [
            ('init', {}),
            ('msg', {'msg': '\u2603'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for key, val in e_groups.items():
            assert c_groups[key] == val


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
            ('begin', {'begin': 'test_debug2.f(...): ...'}),
            ('end', {'end': 'test_debug2.f(...): ...'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for val in e_groups.values():
            assert c_groups['msg'] == val


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
            ('begin', {'begin': "test_debug2.f('in'): ..."}),
            ('end', {'end': 'test_debug2.f(...): 42'}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for val in e_groups.values():
            assert c_groups['msg'] == val


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
            ('begin', {'begin': 'test_debug2.f(...): ...'}),
            ('end', {'end': "test_debug2.f(...): %r(42)" % ValueError}),
            ('exit', {}),
    ]):
        assert c_type == e_type
        for val in e_groups.values():
            assert c_groups['msg'] == val


def test_error_handling():
    # the error handling is bad!
    ud.exit()
    filename = '/tmp/test-not-existing/foo.log'
    ud.init(filename, ud.FLUSH, ud.NO_FUNCTION)
    ud.debug(ud.MAIN, ud.ERROR, 'test')
    ud.exit()
    assert not os.path.exists(filename)


# Important! Must be the last test, and must cleanup for test_logging
def test_unstructured(tmpdir):
    ud.exit()
    ud.set_structured(False)
    tmp = tmpdir.ensure('log')
    fd = ud.init(str(tmp), ud.FLUSH, ud.FUNCTION)
    assert hasattr(fd, 'write')

    ud.debug(ud.MAIN, ud.ERROR, "test")
    ud.exit()

    for cat in CATEGORY:
        if hasattr(getLogger(cat), 'destroy'):
            getLogger(cat).destroy()

    sys.modules.pop('univention.logging')
    output = [line[24:].split('|', 1)[0] for line in tmp.read().splitlines()]
    assert output == ['MAIN        (INIT   ): ', 'MAIN        (ERROR  ): test', 'MAIN        (EXIT   ): EXIT']
