#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Reboot the server! Must be skipped!
## roles-not:
##  - basesystem
## tags:
##  - SKIP
##  - skip_admember
## exposure: dangerous

from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.sidemenu import SideMenuServer


def test_reboot_server(umc_browser_test: UMCBrowserTest):
    side_menu_server = SideMenuServer(umc_browser_test)
    side_menu_server.navigate()
    side_menu_server.reboot_server()
