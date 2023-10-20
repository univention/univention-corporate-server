#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2023 Univention GmbH
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


@pytest.mark.skip()
def test_running(atjobs):
    j = atjobs.add('sleep 10')
    j = atjobs.load(j.nr, extended=True)
    assert str(j) == f'Job #{j.nr} (running)'
