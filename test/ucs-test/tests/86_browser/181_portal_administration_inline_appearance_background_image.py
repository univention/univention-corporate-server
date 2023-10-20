#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal_administration_inline_appearance_background_image
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import re
import time

from playwright.sync_api import Page, expect

from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.portal import UCSPortalEditMode


def ensure_background(page: Page, exists: bool,):
    background = page.locator(".portal__background")
    if exists:
        css = re.compile("url\\(.*\\)")
    else:
        css = "none"

    expect(background).to_have_css("background-image", css,)


def test_portal_change_background_picture(umc_browser_test: UMCBrowserTest,):
    page = umc_browser_test.page
    edit_mode = UCSPortalEditMode(umc_browser_test)

    edit_mode.navigate()

    # make sure we start out with no background set
    ensure_background(page, False,)

    # set the background
    edit_mode.open_edit_side_bar()
    edit_mode.upload_background_picture()
    ensure_background(page, True,)

    # very random sleep but test sometimes fails without this sleep
    time.sleep(5)

    # remove the background
    edit_mode.navigate()
    edit_mode.open_edit_side_bar()
    edit_mode.remove_background_picture()
    ensure_background(page, False,)
