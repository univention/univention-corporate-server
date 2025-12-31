#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from typing import TYPE_CHECKING

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


if TYPE_CHECKING:
    from playwright.sync_api import Page


_ = Translation('ucs-test-framework').translate


class Policies:
    """Class for the UMC LDAP Directory module"""

    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self):
        self.page.get_by_role('tab', name=_('Policies')).click()

    def toggle_section(self, name: str, exact: bool = True):
        self.page.get_by_role('button', name=name, exact=exact).click()

    def create_registry_policy(self, name: str, variable_key: str, variable_value: str):
        self.page.get_by_role('button', name=_('Create new policy')).click()
        self.page.get_by_role('textbox', name='Name').fill(name)
        self.page.get_by_label('Variable', exact=True).fill(variable_key)
        self.page.get_by_role('textbox', name='Value').fill(variable_value)
        self.page.get_by_role('button', name='Create policy').click()
