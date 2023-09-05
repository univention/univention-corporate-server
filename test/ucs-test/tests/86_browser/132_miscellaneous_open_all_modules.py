#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
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

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-browser").translate


def test_open_all_modules(umc_browser_test: UMCBrowserTest):
    umc_browser_test.login()
    all_modules = umc_browser_test.get_available_modules()
    limit = 10
    for i in range(0, len(all_modules), limit):
        logger.info("opening all_modules[%d:%d]" % (i, i + limit))
        umc_browser_test.open_modules(all_modules, start_at=i, limit=i + limit)
        try:
            subprocess.run(["pkill", "-f", "/usr/sbin/univention-management-console-module"], check=True)
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            if e.returncode != 1:
                raise
