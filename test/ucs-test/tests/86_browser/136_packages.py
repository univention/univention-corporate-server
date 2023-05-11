#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test the package management module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.packagemanagement import PackageManagement


def test_package_management_install_uninstall_package(umc_browser_test: UMCBrowserTest) -> None:
    pm = PackageManagement(umc_browser_test)
    pm.navigate()

    small_package = pm.find_small_package()
    pm.install_package(small_package)
    pm.uninstall_package(small_package)
