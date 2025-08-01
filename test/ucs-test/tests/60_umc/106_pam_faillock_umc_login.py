#!/usr/share/ucs-test/runner pytest-3 -s -vvv --tb=native
# desc: Test auth/faillog for the univention-management-console pam stack
# exposure: dangerous
# bugs: [57968]
# packages: [univention-management-console-server]
# roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]

import subprocess

import pytest
from retrying import retry

from univention.config_registry import ucr as _ucr
from univention.lib.umc import HTTPError
from univention.testing.umc import Client


@pytest.fixture
def enable_faillog(ucr):
    ucr.handler_set(['auth/faillog=true'])


@pytest.fixture
def enable_faillog_global(ucr):
    ucr.handler_set(['auth/faillog=true', 'auth/faillog/lock_global=true'])


@pytest.fixture
def faillog_attempts(ucr):
    return ucr.get_int('auth/faillog/limit')


run_on_primary_and_backup = pytest.mark.skipif(_ucr.get('server/role') not in ['domaincontroller_master', 'domaincontroller_backup'], reason='Test can only run primary and backup')


def assert_successful_authentication(username, password, client):
    resp = client.authenticate(username, password)
    assert resp.status == 200


@pytest.mark.usefixtures('enable_faillog')
def test_faillog_umc_login(udm, faillog_attempts):
    username = udm.create_user()[1]
    client = Client(language='en-US')

    assert_successful_authentication(username, 'univention', client)

    for _ in range(faillog_attempts):
        with pytest.raises(HTTPError) as e:
            client.authenticate(username, 'fake_password')

    with pytest.raises(HTTPError) as e:
        client.authenticate(username, 'univention')

    assert e.value.code == 401
    print(e)
    assert count_faillock(username) == faillog_attempts


@pytest.mark.usefixtures('enable_faillog')
def test_successful_login_resets_faillock(udm, faillog_attempts):
    assert faillog_attempts > 1
    username = udm.create_user()[1]
    client = Client(language='en-US')
    for _ in range(1):
        with pytest.raises(HTTPError):
            client.authenticate(username, 'fake_password')

    assert_successful_authentication(username, 'univention', client)
    assert count_faillock(username) == 0


@pytest.mark.usefixtures('enable_faillog_global')
@run_on_primary_and_backup
def test_faillog_global_umc_login(udm, faillog_attempts):
    username = udm.create_user()[1]
    client = Client(language='en-US')

    assert_successful_authentication(username, 'univention', client)

    for _ in range(faillog_attempts):
        with pytest.raises(HTTPError):
            client.authenticate(username, 'fake_password')

    with pytest.raises(HTTPError) as e:
        client.authenticate(username, 'univention')

    assert e.value.code == 401

    assert_account_is_disabled(udm, username)


@retry(retry_on_exception=lambda e: isinstance(e, AssertionError), stop_max_attempt_number=5, wait_fixed=3000)
def assert_account_is_disabled(udm, username):
    is_disabled = udm.list_objects('users/user', filter=f'uid={username}')[0][1]['disabled'][0]

    assert is_disabled == '1'


def count_faillock(username: str) -> int:
    process = subprocess.run(['faillock', '--user', username], check=True, capture_output=True)

    # first two lines of output is the heading, last line is a newline
    faillog_entries = process.stdout.decode('utf-8').split('\n')[2:-1]

    return len(faillog_entries)
