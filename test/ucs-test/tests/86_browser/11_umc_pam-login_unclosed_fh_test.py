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

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-browser').translate


@pytest.mark.parametrize('try_wrong_pw', [False, True])
def test_open_fd_after_login(umc_browser_test: UMCBrowserTest, udm, try_wrong_pw: bool) -> None:
    umc_browser_test.restart_umc()
    password = 'wrong_password' if try_wrong_pw else 'univention'

    for i in range(4):
        username = udm.create_user()[1]
        logger.info('Created user with username %s' % username)
        umc_browser_test.page.goto(f'{umc_browser_test.base_url}/univention/portal')
        umc_browser_test.page.get_by_role('link', name=_('Login Same tab')).click()
        umc_browser_test.login(username, password, check_for_no_module_available_popup=False, login_should_fail=False, do_navigation=False)
        if not try_wrong_pw:
            umc_browser_test.page.wait_for_url(re.compile('.*/univention/portal/#.*'))
        umc_browser_test.end_umc_session()

    open_sockets, ret = count_fhs()
    logger.info('%d open sockets before sleep:\n%s' % (ret, open_sockets))
    time.sleep(60 * 1)
    umc_browser_test.systemd_restart_service('slapd')

    open_sockets, ret = count_fhs(state='close-wait')
    logger.info('%d sockets in close-wait' % ret)
    assert ret < 3, f'More than 2 sockets in CLOSE_WAIT after UMC login:\n{open_sockets}'


def count_fhs(state: str = 'connected') -> tuple[str, int]:
    pid = subprocess.check_output(['pidof', '-x', 'univention-management-console-server'], text=True).strip()
    cmd = ['ss', '--no-header', '--numeric', '--tcp', '--processes', 'state', state, 'dport', '7389']
    out = subprocess.check_output(cmd, text=True)
    connections = [line for line in out.splitlines() if f'pid={pid}' in line]
    return "\n".join(connections), len(connections)
