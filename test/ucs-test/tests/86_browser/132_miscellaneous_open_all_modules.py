#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: |
##  Test if all available modules can be opened and closed without a problem.
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.pytest_univention_playwright import check_for_backtrace, save_trace
from univention.testing.umc import Client


_ = Translation('ucs-test-browser').translate


def get_all_modules():
    client = Client(username='Administrator', password='univention', language='en')
    client.print_response = False
    client.print_request_data = False
    available_modules = client.umc_get('modules').data['modules']
    return [module['name'] for module in available_modules if module['icon'] is not None]


@pytest.fixture(scope='module')
def logged_in_umc_browser_test(umc_browser_test_module: UMCBrowserTest):
    umc_browser_test_module.page.context.tracing.start_chunk()
    umc_browser_test_module.login()
    return umc_browser_test_module


@pytest.fixture(scope='module')
def restart_umc():
    print('Restarting UMC')
    subprocess.run(['deb-systemd-invoke', 'restart', 'univention-management-console-server'], check=True)
    time.sleep(5)


@pytest.mark.parametrize('module_name', get_all_modules())
def test_open_all_modules(restart_umc: None, logged_in_umc_browser_test: UMCBrowserTest, module_name, ucr):
    page: Page = logged_in_umc_browser_test.page
    try:
        expect(page.get_by_role('button', name=_('Favorites'))).to_be_visible(
            timeout=2000,
        )
    except AssertionError:
        logged_in_umc_browser_test.login()

    try:
        logged_in_umc_browser_test.open_and_close_module(module_name, wait_for_network_idle=True)
    except (AssertionError, PlaywrightTimeoutError):
        try:
            save_trace(page, page.context, module_name, Path('browser').resolve(), ucr, tracing_stop_chunk=True)
            check_for_backtrace(page)
        finally:
            logged_in_umc_browser_test.restart_umc()
            logged_in_umc_browser_test.login()
            page.context.tracing.start_chunk()
        raise
