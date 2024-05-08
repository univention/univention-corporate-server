#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Check for unclosed file handles after log ins and password resets
## packages:
##  - univention-management-console-module-udm
##  - univention-management-console-module-passwordchange
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from __future__ import annotations

import re
import subprocess
import time
from typing import Iterator

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.udm import UCSTestUDM


_ = Translation('ucs-test-browser').translate


@pytest.fixture(scope="module")
def users() -> Iterator[list[str]]:
    """Create multiple users once and wait for replication only once."""
    users: list[str] = []
    with UCSTestUDM() as udm:
        for i in range(4):
            dn, username = udm.create_user(wait_for_replication=False, check_for_drs_replication=False, wait_for=False)
            logger.info('Created user with username %s' % username)
            users.append(username)

        udm.wait_for("users/user", dn, wait_for_replication=True, everything=True)
        yield users


@pytest.mark.parametrize('try_wrong_pw', [False, True])
def test_open_fd_after_login(umc_browser_test: UMCBrowserTest, users, try_wrong_pw: bool) -> None:
    umc_browser_test.restart_umc()
    password = 'wrong_password' if try_wrong_pw else 'univention'

    for username in users:
        umc_browser_test.page.goto(f'{umc_browser_test.base_url}/univention/portal')
        umc_browser_test.page.get_by_role('link', name=_('Login Same tab')).click()
        umc_browser_test.login(username, password, check_for_no_module_available_popup=False, login_should_fail=False, do_navigation=False)
        if not try_wrong_pw:
            umc_browser_test.page.wait_for_url(re.compile('.*/univention/portal/#.*'))
        umc_browser_test.end_umc_session()

    open_sockets, ret = count_fhs()
    logger.info(f'{ret} open sockets before sleep:\n{open_sockets}')
    time.sleep(60)
    umc_browser_test.systemd_restart_service('slapd')

    open_sockets, ret = count_fhs(state='close-wait')
    logger.info(f'{ret} sockets in close-wait')
    assert ret < 3, f'More than 2 sockets in CLOSE_WAIT after UMC login:\n{open_sockets}'


def count_fhs(state: str = 'connected') -> tuple[str, int]:
    pid = subprocess.check_output(['pidof', '-x', 'univention-management-console-server'], text=True).strip()
    cmd = ['ss', '--no-header', '--numeric', '--tcp', '--processes', 'state', state, 'dport', '7389']
    out = subprocess.check_output(cmd, text=True)
    connections = [line for line in out.splitlines() if f'pid={pid}' in line]
    return "\n".join(connections), len(connections)
