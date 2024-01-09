#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test the Side menu
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.sidemenu import SideMenu


_ = Translation('ucs-test-browser').translate


def test_side_menu_navigation(umc_browser_test: UMCBrowserTest):
    side_menu = SideMenu(umc_browser_test)
    side_menu.navigate()
    side_menu.open_user_settings()

    change_password_locator = side_menu.page.get_by_text(_('Change password'))
    expect(change_password_locator, "Expect 'Change password' to be visible when on the side menu user settings").to_be_visible()

    side_menu.back()

    user_settings_locator = side_menu.page.locator('#umcMenuUserSettings')
    expect(user_settings_locator, "Expect 'User settings' to be visible after clicking back from User settings").to_be_visible()

    side_menu.toggle_menu()
    # sleep to allow animation
    time.sleep(2)
    side_menu.toggle_menu()
    user_settings_locator = side_menu.page.locator('#umcMenuUserSettings')
    expect(user_settings_locator, "Expect 'User settings' to be visible after closing and opening the side menu").to_be_visible()
