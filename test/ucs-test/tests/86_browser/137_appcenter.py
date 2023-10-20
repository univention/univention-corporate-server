#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test Dudle installation via the 'Appcenter' module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from univention.testing.browser.appcenter import AppCenter
from univention.testing.browser.lib import UMCBrowserTest


APP_NAME = "Admin Diary Backend"


def test_appcenter_install_uninstall_admin_diary_backend(umc_browser_test: UMCBrowserTest,):
    app_center = AppCenter(umc_browser_test)

    app_center.navigate()
    app_center.install_app(APP_NAME)
    app_center.uninstall_app(APP_NAME)
