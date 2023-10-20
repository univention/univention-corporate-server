#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: test adding, modifying, removal of UDM objects
## packages:
##  - univention-management-console-module-udm
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

import pytest
from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser.generic_udm_module import ComputerModule, GroupModule, PoliciesModule, UserModule
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-browser").translate


@pytest.mark.parametrize("module", [GroupModule, UserModule, PoliciesModule, ComputerModule])
def test_udm_create_modify_delete_objects(umc_browser_test: UMCBrowserTest, module):
    udm_module = module(umc_browser_test)

    udm_module.navigate()
    created_item = udm_module.create_object()

    created_object_locator = umc_browser_test.page.get_by_role("grid").get_by_role("gridcell").get_by_text(created_item.identifying_name, exact=True)
    expect(created_object_locator, "Expect the name of the created item to be visible in the grid").to_be_visible()

    udm_module.modify_text_field(created_item)
    udm_module.delete(created_item)
