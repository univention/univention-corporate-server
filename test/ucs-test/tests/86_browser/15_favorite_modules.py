#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: |
##  Test favorite modules
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import re
import time
from typing import List

from playwright.sync_api import Locator, Page, expect

from univention.lib.i18n import Translation
from univention.testing import utils
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.utils import get_ldap_connection


_ = Translation("ucs-test-browser").translate


def test_adding_removing_favorites(umc_browser_test: UMCBrowserTest, ucr):
    page = umc_browser_test.page
    umc_browser_test.login()

    check_default_favorites(page, ucr)
    check_removing_default_favorites(page)
    check_add_to_favorites(page)
    re_add_default_favorites(page, ucr)


def check_default_favorites(page: Page, ucr):
    default_favorites = get_default_favorites(ucr)

    for favorite in default_favorites:
        locator = get_locator_for_module_by_moduleid(page, favorite)
        expect(locator).to_be_visible()


def number_of_visible_locators(locators: Locator) -> int:
    n = 0
    for locator in locators.all():
        if locator.is_visible():
            n += 1
    print(f"{n} visible locators found")
    return n


def check_removing_default_favorites(page: Page):
    page.get_by_role("button", name="Favorites").click()
    # simply looping over all the locators sadly doesn't work here
    locators = page.locator(".umcGalleryWrapperItem")
    while number_of_visible_locators(locators) != 0:
        locator = locators.first

        if locator.is_hidden():
            continue

        locator.locator(".umcGalleryContextIcon").click()
        time.sleep(0.5)
        page.get_by_role("cell", name=_("Remove from favorites")).click()
        time.sleep(0.5)
        locators = page.locator(".umcGalleryWrapperItem")

    # after removing all favorites, the button should not be visible
    expect(page.get_by_role("button", name="Favorites")).to_be_hidden()


def check_add_to_favorites(page: Page):
    page.get_by_role("button", name=_("Users")).click()
    module = page.locator(".umcGalleryWrapperItem[moduleid]").first
    moduleid = module.get_attribute("moduleid")
    assert moduleid is not None, "moduleid attribute of .umcGalleryWrapperItem element doesn't exist"

    moduleid = normalize_moduleid(moduleid)

    module.click(button="right")
    page.get_by_role("cell", name=_("Add to favorites")).click()

    page.get_by_role("button", name=_("Favorites")).click()
    check_module_is_visible(page, moduleid)


def check_module_is_visible(page: Page, moduleid: str):
    locator = page.locator(f".umcGalleryWrapperItem[moduleid^='{moduleid}']")
    expect(locator).to_be_visible()


def get_default_favorites(ucr) -> List[str]:
    default_favorites_string = ucr.get("umc/web/favorites/default")

    if not utils.package_installed("univention-management-console-module-welcome"):
        default_favorites_string = re.sub(r"welcome(,|$)", "", default_favorites_string).rstrip(",")

    if not utils.package_installed("univention-management-console-module-udm"):
        default_favorites_string = re.sub(r"udm.*?(,|$)", "", default_favorites_string).rstrip(",")

    return default_favorites_string.split(",")


def normalize_moduleid(moduleid: str) -> str:
    moduleid_split = moduleid.split("#")
    assert len(moduleid_split) == 2
    return moduleid_split[0]


def get_locator_for_module_by_moduleid(page: Page, moduleid: str) -> Locator:
    return page.locator(f".umcGalleryWrapperItem[moduleid^='{moduleid}']")


def re_add_default_favorites(page: Page, ucr):
    check_removing_default_favorites(page)

    page.locator(".umcModuleSearchToggleButton").click()
    page.locator(".umcModuleSearch input.dijitInputInner").type("*")
    for favorite in get_default_favorites(ucr):
        locator = get_locator_for_module_by_moduleid(page, favorite)
        locator.click(button="right")
        page.get_by_role("cell", name=_("Add to favorites")).click()

    verify_default_favorites_are_restored(ucr)


def verify_default_favorites_are_restored(ucr):
    lo = get_ldap_connection()
    umc_property = lo.getAttr(f"uid=Administrator,cn=users,{ucr.get('ldap/base')}", "univentionUMCProperty")
    favorites = next((property.decode("utf-8")[len("favorites="):] for property in umc_property if property.startswith(b"favorites=")), None)
    assert favorites is not None

    assert set(get_default_favorites(ucr)) == set(favorites.split(","))
