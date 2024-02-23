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


from playwright.sync_api import Page

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


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
