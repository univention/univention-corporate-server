#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test creating a portal via UMC
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess

import pytest
from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.generic_udm_module import PortalModule
from univention.testing.browser.lib import UMCBrowserTest
from univention.udm import UDM


_ = Translation("ucs-test-browser").translate

udm = UDM.admin().version(2)


class PortalContext:
    def __init__(self) -> None:
        self.dn = ""


@pytest.fixture()
def portal_context(ucr,):
    old_portal_dn = ucr.get("portal/default-dn")
    portal_context = PortalContext()

    yield portal_context
    try:
        udm.obj_by_dn(portal_context.dn).delete()
    except Exception:
        logger.exception("failed to delete created portal with ")
    finally:
        set_portal(old_portal_dn, ucr,)


def test_portal(umc_browser_test: UMCBrowserTest, ucr, portal_context,):
    portal_module = PortalModule(umc_browser_test)
    portal_module.navigate()

    created_item = portal_module.add()
    portal_module.tester.check_checkbox_in_grid_by_name(created_item.identifying_name)

    portal = next(iter(udm.get("portals/portal").search(f"name={created_item.identifying_name}")))
    portal_context.dn = portal.dn
    portal_dname = portal.props.displayName["en_US"]

    set_portal(portal.dn, ucr,)

    umc_browser_test.login(location="/univention/portal")
    portal_name = umc_browser_test.page.get_by_text(portal_dname)
    expect(portal_name, f"expected new portal name '{portal_name}' to be visible",).to_be_visible()


def set_portal(dn: str, ucr,):
    ucr.handler_set([f"portal/default-dn={dn}"])
    subprocess.run(["univention-portal", "update"], check=True,)
