#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test portal entries
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from typing import Dict, List

from playwright.sync_api import Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


translator = Translation("ucs-test-")
_ = translator.translate


tooltip_system_settings = _("Univention Management Console for admin­is­tra­ting the UCS domain and the local system")
tooltip_server_overview = _("Provide an overview of all UCS server in the domain")
row_system_and_domain_settings = [_("Administration"), _("System and domain settings"), tooltip_system_settings]
row_server_overview = [_("Administration"), _("Server overview"), tooltip_server_overview]
row_system_settings = [_("Administration"), _("System settings"), _("Univention Management Console for admin­is­tra­ting the local system")]
row_portal = [_("Administration"), _("Univention Portal"), _("Central portal web page for the UCS domain")]

expected_entries: Dict[str, List[List[str]]] = {
    "domaincontroller_master_single": [
        row_system_and_domain_settings,
    ],
    "domaincontroller_master_multi": [
        row_system_and_domain_settings,
        row_server_overview,
    ],
    "domaincontroller_backup": [
        row_system_and_domain_settings,
        row_server_overview,
    ],
    "domaincontroller_slave": [
        row_system_settings,
        row_portal,
    ],
    "memberserver": [
        row_system_settings,
        row_portal,
    ],
}


def get_entries_for_role(role: str,) -> List[List[str]]:
    return expected_entries[role]


def test_portal_entries_appear_as_expected(umc_browser_test: UMCBrowserTest, ucr,):
    page = umc_browser_test.page
    role = ucr.get("server/role")

    if role == "domaincontroller_master":
        entries = get_entries_for_role("domaincontroller_master_single")
        page.goto(umc_browser_test.base_url)
        check_if_expected_entries_are_shown(page, entries,)
    elif role in ["domaincontroller_backup", "domaincontroller_slave"]:
        # check the master
        entries = get_entries_for_role("domaincontroller_master_multi")
        page.goto(f"https://{ucr.get('ldap/master')}/")
        check_if_expected_entries_are_shown(page, entries,)

        # check member/slave
        entries = get_entries_for_role(role)
        page.goto(umc_browser_test.base_url)
        check_if_expected_entries_are_shown(page, entries,)


def check_if_expected_entries_are_shown(
    page: Page,
    entries: List[List[str]],):
    for entry in entries:
        (header, group, tooltip) = entry
        expect(page.get_by_text(header)).to_be_visible()

        system_and_domain_settings = page.get_by_text(group)
        expect(system_and_domain_settings).to_be_visible()

        system_and_domain_settings.hover()
        tooltip_loc = page.get_by_role("tooltip", name=tooltip,)
        expect(tooltip_loc).to_be_visible()
