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

import subprocess
import time

import pytest

from univention.lib.i18n import Translation
from univention.lib.umc import HTTPError
from univention.testing.browser import logger
from univention.testing.umc import Client


_ = Translation('ucs-test-browser').translate


@pytest.mark.parametrize('try_wrong_pw', [False, True])
def test_open_fd_after_login(udm, try_wrong_pw: bool):
    subprocess.call(['systemctl', 'restart', 'univention-management-console-server.service'])
    password = 'wrong_password' if try_wrong_pw else 'univention'

    for i in range(4):
        username = udm.create_user()[1]
        logger.info('Created user with username %s' % username)
        client = Client(language='en-US')
        try:
            client.authenticate(username, password)
        except HTTPError:
            if not try_wrong_pw:
                raise

    open_sockets, ret = count_fhs()
    logger.info('%d open sockets before sleep:\n%s' % (ret, open_sockets))
    time.sleep(60 * 1)
    subprocess.call(['systemctl', 'restart', 'slapd.service'])

    open_sockets, ret = count_fhs(state='close-wait')
    logger.info('%d sockets in close-wait' % ret)
    assert ret <= 3, f'More than 3 sockets in CLOSE_WAIT after UMC login:\n{open_sockets}'


def count_fhs(state: str | None = None) -> tuple[str, int]:
    state_str = f'state {state}' if state is not None else ''
    ret = subprocess.run(
        f'ss -tp {state_str} dport 7389 | grep pid=$(pidof -x univention-management-console-server)',
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode('utf-8')

    sockets_in_close_wait = ret.count('\n')
    return ret, sockets_in_close_wait
