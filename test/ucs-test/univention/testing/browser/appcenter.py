#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
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

import json
import logging
import re

from playwright.sync_api import Page, Response, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import MIN, UMCBrowserTest


logger = logging.getLogger(__name__)

_ = Translation("ucs-test-framework").translate


def wait_for_final_query(response: Response):
    if not re.fullmatch(".*/univention/command/appcenter/query.*", response.url):
        return False

    request = response.request
    if request.post_data is None:
        return False
    json_body = json.loads(request.post_data)
    if "options" in json_body and "quick" in json_body["options"] and not json_body["options"]["quick"]:
        logger.debug("URL: %s" % response.url)
        logger.debug("JSON content: %s" % json_body)
        logger.debug("TRUE")
        return True
    return False


class AppCenter:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _("App Center")

    def navigate(self, username="Administrator", password="univention"):
        self.tester.login(username, password)
        self.tester.open_module(self.module_name)
        self.handle_first_open_dialog()

    def handle_first_open_dialog(self):
        first_open_dialog = self.page.get_by_role("dialog", name="Univention App Center")
        only_visible_when_no_dialog = self.page.get_by_role("heading", name=_("Available"))
        expect(first_open_dialog.or_(only_visible_when_no_dialog)).to_be_visible(timeout=5 * MIN)
        if first_open_dialog.is_visible():
            first_open_dialog.get_by_label(_("Do not show this message again")).check()
            first_open_dialog.get_by_role("button", name="Continue").click()

    def open_app(self, app_name: str):
        """Click on an app in the AppCenter overview"""
        self.page.locator(".umcTile").get_by_text(app_name).first.click()

    def return_to_app_module_from_app_view(self):
        """Return to the app center overview from an opened app"""
        back_to_overview = self.page.get_by_role("button", name=_("Back to overview"))
        expect(back_to_overview).to_be_visible()
        back_to_overview.click()

    def install_app(self, app_name: str):
        """Install an app. The AppCenter needs to be on the overview screen"""
        self.open_app(app_name)

        logger.info("Starting installation of %s" % app_name)
        install_button = self.page.get_by_role("button", name=_("Install"), exact=True)
        expect(install_button).to_be_visible()
        install_button.click()

        self.handle_installation_dialog()
        self.return_to_app_module_from_app_view()
        logger.info("App installation done")

    def handle_installation_dialog(self):
        # self.page.get_by_role("button", name=_("Continue"), exact=True).click()
        start_installation = self.page.get_by_role("button", name=_("Start installation"))
        continue_button = self.page.get_by_role("button", name=_("Continue"))
        expect(start_installation.or_(continue_button)).to_be_visible()

        if continue_button.is_visible():
            continue_button.click()

        start_installation.click()
        expect(self.page.get_by_role("progressbar")).to_be_hidden(timeout=10 * MIN)

    def uninstall_app(self, app_name: str):
        """Uninstall an app. The AppCenter needs to be on the overview screen"""
        self.open_app(app_name)
        manage_installations = self.page.get_by_role("button", name=_("Manage installation"))
        expect(manage_installations).to_be_visible(timeout=5 * MIN)
        manage_installations.click()

        uninstall_button = self.page.get_by_role("button", name=_("Uninstall"))
        grid = self.page.get_by_role("grid")

        expect(uninstall_button.or_(grid)).to_be_visible()
        logger.info("Starting uninstall of %s" % app_name)
        if grid.is_visible():
            self.tester.check_checkbox_in_grid_by_name(_("this computer"))
            self.page.get_by_role("button", name=_("More")).click()
            self.page.get_by_role("cell", name=_("Uninstall")).click()
        else:
            uninstall_button.click()

        self.page.get_by_role("button", name=_("Start removal")).click()
        expect(self.page.get_by_role("progressbar")).to_be_hidden(timeout=10 * MIN)
        self.return_to_app_module_from_app_view()
        logger.info("Uninstall done")
