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
from typing import Tuple

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-browser').translate


@pytest.mark.parametrize('try_wrong_pw', [False, True])
def test_open_fd_after_login(umc_browser_test: UMCBrowserTest, udm, try_wrong_pw: bool):
    umc_browser_test.restart_umc()
    password = 'wrong_password' if try_wrong_pw else 'univention'

    for i in range(4):
        username = udm.create_user()[1]
        logger.info('Created user with username %s' % username)
        umc_browser_test.page.goto(f'{umc_browser_test.base_url}/univention/portal')
        umc_browser_test.page.get_by_role('link', name=_('Login')).click()
        umc_browser_test.login(username, password, check_for_no_module_available_popup=False, login_should_fail=False, do_navigation=False, skip_xhr_check=True)
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


def count_fhs(state: str | None = None) -> Tuple[str, int]:
    state_str = f'state {state}' if state is not None else ''
    ret = subprocess.run(
        f'ss -tp {state_str} dport 7389 | grep pid=$(pidof -x univention-management-console-server)',
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode('utf-8')

    sockets_in_close_wait = ret.count('\n')
    return ret, sockets_in_close_wait
