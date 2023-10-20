#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test adding, changing and removing a photo for a user
## packages:
##  - univention-management-console-module-udm
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.udm_users import create_test_user
from univention.testing.utils import get_ldap_connection


_ = Translation("ucs-test-browser").translate


def test_add_user_photo(umc_browser_test: UMCBrowserTest, udm,):
    page = umc_browser_test.page
    lo = get_ldap_connection()
    user = create_test_user(udm, lo,)

    user_module = UserModule(umc_browser_test)
    user_module.navigate()
    detail_view = user_module.open_details(user.username)

    inital = detail_view.upload_picture("/tmp/inital.png")
    inital_src_attribute = inital.get_attribute("src")

    # if we don't sleep here the second image will be took before the first image is displayed on the user details page
    # this will lead to the assertion failing since the image is the same
    time.sleep(1)

    changed = detail_view.upload_picture("/tmp/changed.png")
    changed_src_attribute = changed.get_attribute("src")

    assert inital_src_attribute != changed_src_attribute, "The src attribute didn't change after uploading a new image"

    detail_view.remove_picture()
    detail_view.save()

    detail_view = user_module.open_details(user.username)

    image_locator = page.locator(".umcUDMUsersModule__jpegPhoto .umcImage__img")
    expect(image_locator).to_be_hidden()
