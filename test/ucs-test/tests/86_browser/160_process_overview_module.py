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

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.process_overview import ProcessOverview


_ = Translation("ucs-test-browser").translate


def test_process_overview_module(umc_browser_test: UMCBrowserTest,):
    page = umc_browser_test.page
    process_overview = ProcessOverview(umc_browser_test)
    process_overview.navigate()
    process_overview.search("All", "",)

    cells = page.get_by_role("gridcell").all()
    assert all(len(cell.inner_html()) != 0 for cell in cells)

    process_overview.search("User", "root",)

    cells = page.locator(".field-user[role=gridcell]").all()
    assert all(cell.inner_text() == "root" for cell in cells)


@pytest.mark.parametrize("force", [False, True],)
def test_kill_process(force: bool, umc_browser_test: UMCBrowserTest,):
    process_overview = ProcessOverview(umc_browser_test)
    process_overview.navigate()

    p = subprocess.Popen(["sleep", "5000"])
    process_overview.ensure_process(p, "PID",)
    process_overview.ensure_process(p, "Command",)
    process_overview.kill_process(p, force,)
    assert p.wait() == -9 if force else -15
