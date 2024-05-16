#!/usr/share/ucs-test/runner pytest-3 -v
## desc: Basic check of univention.lib.atjobs
## bugs: [36809]
## tags: [basic]
## packages:
##   - python3-univention-lib
## exposure: dangerous

from datetime import datetime, timedelta
from typing import Dict, Iterator, Tuple

import pytest

from univention.lib import atjobs
from univention.testing.strings import random_name, random_string


_AtJob = Tuple[atjobs.AtJob, str, Dict[str, str]]


def print_job(job: atjobs.AtJob, msg: str) -> None:
    print(f'{msg}{job!r}\nNumber: {job.nr!r}\nCommand: {job.command!r}\nComments: {job.comments!r}\nExecTime: {job.execTime!r}\nOwner: {job.owner!r}')


def validate(jut: atjobs.AtJob, expected: _AtJob) -> None:
    job, cmd, comments = expected
    assert jut.command.strip() == cmd
    assert jut.comments == comments
    assert jut.execTime == job.execTime
    assert jut.owner == job.owner


@pytest.fixture(scope="module")
def atjob() -> Iterator[_AtJob]:
    cmd = f'echo {random_name()}'
    comments = {
        random_name(): random_string(length=30)
        for _i in range(10)
    }
    job = atjobs.add(cmd, execTime=(datetime.now() + timedelta(days=3)), comments=comments)
    try:
        print_job(job, 'Created job ')
        yield job, cmd, comments
    finally:
        job.rm()
        assert atjobs.load(job.nr) is None


def test_create(atjob: _AtJob) -> None:
    jobs = atjobs.list(extended=True)
    for testjob in jobs:
        if testjob.nr == atjob[0].nr:
            print_job(testjob, 'Found job ')
            break
    else:
        pytest.fail(f'job {atjob[0].nr!r} not found in {jobs}')

    validate(testjob, atjob)


def test_lookup(atjob: _AtJob) -> None:
    testjob2 = atjobs.load(atjob[0].nr, extended=True)
    print_job(testjob2, 'Explicitely loaded job ')
    validate(testjob2, atjob)
