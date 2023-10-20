#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: test language switch, logout, module visibility, process timeout
## packages:
##  - univention-management-console-module-ucr
##  - univention-management-console-module-top
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous
from __future__ import annotations

import re
import time
from typing import Set

import psutil
import pytest
from playwright.sync_api import BrowserContext, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UCSLanguage, UMCBrowserTest
from univention.testing.browser.process_overview import ProcessOverview
from univention.testing.browser.sidemenu import SideMenu


translator = Translation("ucs-test-browser")
_ = translator.translate


def test_switch_language(umc_browser_test: UMCBrowserTest):
    original_language = umc_browser_test.lang
    target_language = UCSLanguage.DE_DE if umc_browser_test.lang == UCSLanguage.EN_US else UCSLanguage.EN_US
    side_menu = SideMenu(umc_browser_test)
    side_menu.navigate()
    side_menu.switch_to_language(target_language)

    translator.set_language(str(target_language).replace("-", "_"))

    umc_browser_test.end_umc_session()
    umc_browser_test.login()
    expect(side_menu.page.get_by_role("button", name=_("Favorites"))).to_be_visible()

    translator.set_language(str(original_language).replace("-", "_"))


def test_logout_with_side_menu(umc_browser_test: UMCBrowserTest):
    umc_browser_test.login()
    favorites_button = umc_browser_test.page.get_by_role("button", name=_("Favorites"))
    expect(favorites_button).to_be_visible()

    context = umc_browser_test.page.context

    assert search_for_session_id_cookie(context), "No UMCSessionid cookie found after login"

    umc_browser_test.logout()

    exp = re.compile(".*/univention/portal.*")
    umc_browser_test.page.wait_for_url(exp)

    assert not search_for_session_id_cookie(context), "UMCSessionid cookie found after logout"


def search_for_session_id_cookie(context: BrowserContext) -> bool:
    return any("name" in cookie and cookie["name"] == "UMCSessionId" for cookie in context.cookies())


@pytest.fixture()
def module_process_timeout(umc_browser_test: UMCBrowserTest, ucr):
    umc_browser_test.restart_umc()
    timeout = 30
    ucr.handler_set([f"umc/module/timeout={timeout}"])
    yield timeout
    ucr.revert_to_original_registry()
    umc_browser_test.restart_umc()


def test_module_process_timeout(umc_browser_test: UMCBrowserTest, module_process_timeout: int):
    umc_browser_test.login()
    umc_browser_test.open_module("Univention Configuration Registry")
    expect(umc_browser_test.page.get_by_role("grid")).to_be_visible()
    time.sleep(5)
    process_overview = ProcessOverview(umc_browser_test)
    umc_browser_test.open_module("Process overview")

    timeout_end = time.time() + module_process_timeout + 10

    while time.time() < timeout_end:
        search_bar = umc_browser_test.page.get_by_text("Search...").last
        search_bar.click(force=True)
        with umc_browser_test.page.expect_response(process_overview.grid_load_url):
            search_bar.press("Enter")

        time.sleep(10)

    assert not module_process_alive("ucr"), "A module's process still exists after its timeout"
    assert module_process_alive("top"), "A module's process dies before its timeout"


def module_process_alive(module) -> bool:
    return any({"/usr/sbin/univention-management-console-module", "-m", module}.issubset(set(process.cmdline())) for process in psutil.process_iter())


def test_module_visibility_for_regular_user(umc_browser_test: UMCBrowserTest, udm):
    username = udm.create_user()[1]
    umc_browser_test.login(username, check_for_no_module_available_popup=True)

    add_user_policy(udm, umc_browser_test, username)
    add_group_policy(udm, umc_browser_test, username)

    umc_browser_test.login(username, skip_xhr_check=True)

    allowed_modules: Set[str] = {
        _("Univention Configuration Registry"),
        _("Process overview"),
    }

    assert (
        set(umc_browser_test.get_available_modules()) & allowed_modules == allowed_modules
    ), "Modules 'Process overview' and 'Univention Configuration Registry'  should be visible"


def add_user_policy(udm, umc_browser_test: UMCBrowserTest, username: str):
    udm.create_object(
        "policies/umc",
        name="username_policy",
        allow=f"cn=top-all,cn=operations,cn=UMC,cn=univention,{umc_browser_test.ldap_base}",
        position=f"cn=policies,{umc_browser_test.ldap_base}",
    )
    udm.modify_object(
        "users/user",
        dn=f"uid={username},cn=users,{umc_browser_test.ldap_base}",
        policy_reference=f"cn=username_policy,cn=policies,{umc_browser_test.ldap_base}",
    )


def add_group_policy(udm, umc_browser_test: UMCBrowserTest, username: str):
    udm.create_object(
        "groups/group",
        name="umc_test_group",
        position=f"cn=groups,{umc_browser_test.ldap_base}",
    )
    udm.modify_object(
        "users/user",
        dn=f"uid={username},cn=users,{umc_browser_test.ldap_base}",
        append={"groups": [f"cn=umc_test_group,cn=groups,{umc_browser_test.ldap_base}"]},
    )
    udm.create_object(
        "policies/umc",
        name="umc_test_group_policy",
        allow=f"cn=ucr-all,cn=operations,cn=UMC,cn=univention,{umc_browser_test.ldap_base}",
        position=f"cn=policies,{umc_browser_test.ldap_base}",
    )
    udm.modify_object(
        "groups/group",
        dn=f"cn=umc_test_group,cn=groups,{umc_browser_test.ldap_base}",
        policy_reference=f"cn=umc_test_group_policy,cn=policies,{umc_browser_test.ldap_base}",
    )
