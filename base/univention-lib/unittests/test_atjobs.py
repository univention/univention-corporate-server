#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import time

import pytest


def test_add_simple(atjobs):
    atjobs.add('ls')


def test_add_later(atjobs):
    j = atjobs.add('ls', time.time() + 120)
    assert atjobs.load(j.nr) is not None


def test_comments(atjobs):
    comments = {'my': 'comment', 'another': 'comment #2'}
    j = atjobs.add('ls', time.time() + 120, comments)
    j = atjobs.load(j.nr, extended=True)
    assert j.command == 'ls\n'
    assert j.comments == comments


@pytest.mark.skip(reason='Why do I need comments to get command?')
def test_command(atjobs):
    j = atjobs.add('ls', time.time() + 120)
    j = atjobs.load(j.nr, extended=True)
    assert j.command == 'ls\n'


@pytest.mark.xfail(reason='This is bad: No comment -> Broken new job')
def test_reschedule(atjobs):
    exec_time = time.time() + 120
    exec_time_datetime = datetime.datetime.fromtimestamp(exec_time)
    exec_time_datetime = exec_time_datetime.replace(second=0, microsecond=0)
    j1 = atjobs.add('ls', exec_time)
    assert j1.execTime == exec_time_datetime
    j2 = atjobs.reschedule(j1.nr, exec_time + 120)
    assert j1.nr != j2.nr
    j2 = atjobs.load(j2.nr, extended=True)
    assert j2.execTime == exec_time_datetime + datetime.timedelta(minutes=2)
    assert j2.command == 'ls\n'


def test_reschedule_unknown(atjobs):
    with pytest.raises(AttributeError):
        atjobs.reschedule(-1)


def test_remove(atjobs):
    j = atjobs.add('ls', time.time() + 120)
    j = atjobs.load(j.nr, extended=True)
    assert j is not None
    atjobs.remove(j.nr)
    j = atjobs.load(j.nr, extended=True)
    assert j is None


@pytest.mark.skip
def test_running(atjobs):
    j = atjobs.add('sleep 10')
    j = atjobs.load(j.nr, extended=True)
    assert str(j) == f'Job #{j.nr} (running)'
