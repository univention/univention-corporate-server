#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2024 Univention GmbH
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


from playwright.sync_api import Locator, Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-framework').translate


class LDAPDirectory:
    """Class for the UMC LDAP Directory module"""

    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _('LDAP directory')

    def navigate(self, username='Administrator', password='univention'):
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
