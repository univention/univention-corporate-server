#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass

from playwright.sync_api import Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-browser').translate


@dataclass
class UserCreationAttribute:
    label: str
    value: str


class SelfService:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self, hash: str = '', username: str | None = None, password: str | None = None):
        if username and password:
            self.tester.login(username, password, f'/univention/portal/#/selfservice/{hash}')
            return
        self.page.goto(f'{self.tester.base_url}/univention/portal/#/selfservice/{hash}')

    def navigate_create_account(self):
        self.navigate('createaccount')
        expect(self.page.get_by_role('heading', name=_('Create an account'))).to_be_visible()

    def fill_create_account(self, attributes: dict[str, UserCreationAttribute], button: str | None = 'Create an account'):
        for k, v in attributes.items():
            if k == 'password':
                self.page.get_by_role('textbox', name=_('Password'), exact=True).fill(v.value)
                self.page.get_by_role('textbox', name=_('Password (retype)'), exact=True).fill(v.value)
            else:
                self.page.get_by_role('textbox', name=v.label).fill(v.value)

        if button is not None:
            self.page.get_by_role('button', name=button).click()
