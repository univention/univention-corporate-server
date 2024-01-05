#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from typing import Dict, Union

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

    def navigate(self, hash: str = '', username: Union[str, None] = None, password: Union[str, None] = None):
        if username and password:
            self.tester.login(username, password, f'/univention/portal/#/selfservice/{hash}', skip_xhr_check=True)
            return
        self.page.goto(f'{self.tester.base_url}/univention/portal/#/selfservice/{hash}')

    def navigate_create_account(self):
        self.navigate('createaccount')
        expect(self.page.get_by_role('heading', name=_('Create an account'))).to_be_visible()

    def fill_create_account(self, attributes: Dict[str, UserCreationAttribute], button: Union[str, None] = 'Create an account'):
        for k, v in attributes.items():
            if k == 'password':
                self.page.get_by_role('textbox', name=_('Password'), exact=True).fill(v.value)
                self.page.get_by_role('textbox', name=_('Password (retype)'), exact=True).fill(v.value)
            else:
                self.page.get_by_role('textbox', name=v.label).fill(v.value)

        if button is not None:
            self.page.get_by_role('button', name=button).click()
