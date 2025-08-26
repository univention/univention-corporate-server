#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from playwright.sync_api import Locator, Page, expect

from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-framework').translate


class LDAPDirectory:
    """Class for the UMC LDAP Directory module"""

    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _('LDAP directory')

    def navigate(self, username=ucr.get('tests/domainadmin/username', 'Administrator'), password=ucr.get('tests/domainadmin/pwd', 'univention')):
        self.tester.login(username, password)
        self.tester.open_module(self.module_name)

    def _get_directory_locator(self, name: str, exact: bool = False) -> Locator:
        entry = self.page.get_by_role('gridcell', name=name, exact=exact)
        expect(entry, f"LDAP directory entry with name '{name} not visible'").to_be_visible()
        return entry

    def open_directory(self, name: str, exact: bool = True):
        directory = self._get_directory_locator(name, exact)
        directory.click()

    def expand_directory(self, name: str, exact: bool = True):
        directory = self._get_directory_locator(name, exact)
        expand = directory.locator('div').first
        expand.click()

    def open_entry(self, name: str, exact=True):
        entry_grid = self.page.get_by_role('grid').nth(1)
        entry = entry_grid.get_by_role('gridcell', name=name, exact=exact)
        clickable_text = entry.get_by_text(name, exact=exact)
        clickable_text.click()

    def edit_container(self, name: str, exact=True):
        directory = self._get_directory_locator(name, exact=exact)
        directory.click(button='right')
        edit_button = self.page.get_by_role('region').get_by_role('cell', name='Edit')
        expect(edit_button, 'edit button not visible').to_be_visible()
        edit_button.click()
