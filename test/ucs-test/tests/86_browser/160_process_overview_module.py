#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test the 'Process overview' module
## packages:
##  - univention-management-console-module-top
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
from typing import Generator

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.process_overview import ProcessOverview


_ = Translation("ucs-test-browser").translate


def test_process_overview_module(umc_browser_test: UMCBrowserTest):
    page = umc_browser_test.page
    process_overview = ProcessOverview(umc_browser_test)
    process_overview.navigate()
    process_overview.search("All", "")

    cells = page.get_by_role("gridcell").all()
    assert all(len(cell.inner_html()) != 0 for cell in cells)

    process_overview.search("User", "root")

    cells = page.locator(".field-user[role=gridcell]").all()
    assert all(cell.inner_text() == "root" for cell in cells)


@pytest.fixture()
def sleep_process() -> Generator[subprocess.Popen, None, None]:
    p = subprocess.Popen(["sleep", "900"])
    yield p
    if p.poll() is None:
        p.kill()


@pytest.mark.parametrize("force", [False, True])
def test_kill_process(force: bool, umc_browser_test: UMCBrowserTest, sleep_process: subprocess.Popen):
    process_overview = ProcessOverview(umc_browser_test)
    process_overview.navigate()

    process_overview.ensure_process(sleep_process, "PID")
    process_overview.ensure_process(sleep_process, "Command")
    process_overview.kill_process(sleep_process, force)
    assert sleep_process.wait() == -9 if force else -15
