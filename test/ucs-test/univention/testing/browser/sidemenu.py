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

import time
from pathlib import Path

from playwright.sync_api import Locator, Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UCSLanguage, UMCBrowserTest


_ = Translation("ucs-test-framework").translate


class SideMenuUser:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = self.tester.page

    def navigate(self, username: str = "Administrator", password: str = "univention", do_login: bool = True, **kwargs):
        SideMenu(self.tester).navigate(username=username, password=password, do_login=do_login, **kwargs)
        self.page.locator("#umcMenuUserSettings").click()

    def change_password(self, old_password: str, new_password: str):
        self.page.locator("#umcMenuChangePassword").click()

        self.page.get_by_role("dialog").get_by_label("Old Password").type(old_password)
        time.sleep(0.5)
        self.page.get_by_role("dialog").get_by_label("New password", exact=True).type(new_password)
        time.sleep(0.5)
        self.page.get_by_role("dialog").get_by_label("New password (retype)").type(new_password)
        time.sleep(0.5)
        self.page.get_by_role("button", name=_("Change password")).click()


class SideMenuServer:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = self.tester.page

    def navigate(self):
        SideMenu(self.tester).navigate()
        self.page.locator("#umcMenuServer").click()

    def reboot_server(self, do_reboot: bool = False):
        self.page.get_by_text("Reboot Server").click()
        reboot_button = self.page.get_by_role("button", name="Reboot")

        expect(reboot_button).to_be_visible()

        if do_reboot:
            reboot_button.click()


class SideMenuLicense:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self, do_login: bool = True):
        SideMenu(self.tester).navigate(do_login=do_login)
        self.page.locator("#umcMenuLicense").click()

    def import_license(self, license_file_path: Path, as_text: bool):
        self.page.get_by_text(_("Import new license")).click()

        if as_text:
            with open(license_file_path) as license_file:
                license_text = license_file.read()
                self.page.get_by_role("dialog").get_by_role("textbox").last.fill(license_text)
                self.page.get_by_role("button", name=_("Import from text field")).click()

        else:
            with self.page.expect_file_chooser() as fc_info:
                self.page.get_by_role("button", name=_("Import from file...")).click(force=True)

            file_chooser = fc_info.value
            file_chooser.set_files(license_file_path)

        success_text = self.page.get_by_text(_("The license has been imported successfully."))
        expect(success_text).to_be_visible()
        self.page.get_by_role("dialog").get_by_role("button", name="Ok").click()

    def open_license_information(self):
        self.page.get_by_text(_("License information")).click()


class SideMenu:
    side_menu_button: Locator

    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def find_side_menu_button(self):
        side_menu_button_umc = self.page.locator(".umcMenuButton")
        side_menu_button_portal = self.page.get_by_role("button", name="Menu")
        expect(side_menu_button_umc.or_(side_menu_button_portal), "Neither the UMC nor the Portal side menu button is visible").to_be_visible()

        if side_menu_button_portal.is_visible():
            self.side_menu_button = side_menu_button_portal
        else:
            self.side_menu_button = side_menu_button_umc

    def navigate(self, username="Administrator", password="univention", do_login=True, **kwargs):
        if do_login:
            self.tester.login(username, password, **kwargs)

        self.find_side_menu_button()

        self.toggle_menu()

        return self

    def toggle_menu(self):
        # sometimes when opening the side menu immediately after logging in
        # playwright thinks that the button is visible and clickable and clicks it, but it actually isn't
        # the test would continue, thinking the side menu is open when
        # here we check if the "Logout" button is visible on the page
        # this button should only be visible when the side menu is open

        expect(self.side_menu_button, "side menu button should be visible").to_be_visible()
        retry = 2
        for i in range(retry):
            self.side_menu_button.click()
            logout_button = self.page.get_by_role("button", name=_("Logout"))
            login_button = self.page.get_by_role("button", name=_("Login"))
            try:
                expect(logout_button.or_(login_button), "side menu logout or login button not visible after clicking sidemenu").to_be_visible()
                break
            except AssertionError:
                if i == retry:
                    raise

    def switch_to_language(self, target_language: UCSLanguage):
        """
        Switches the language to the language given by target_language.

        This method changes the language using the SideMnu "Switch Language" button.
        It also updates the tester this Class was initialized with to the new language.

        :param target_language: the language to switch to
        """
        self.page.locator("#umcMenuLanguage").click()

        lang_button = self.page.get_by_text(target_language.get_name())
        lang_button.click()

        self.page.get_by_role("button", name="Switch language").click()
        # not sure if this is the right place to do this
        self.tester.set_language(target_language)

    def logout(self):
        """Logout using the Side Menu"""
        self.page.get_by_role("button", name=_("Logout")).click()
        self.page.get_by_role("dialog", name=_("Confirmation")).get_by_role("button", name=_("Logout")).click()

    def back(self):
        # TODO: find a better locator for this
        self.page.locator(".menuSlideHeader").locator("visible=true").click()

    def open_user_settings(self):
        self.page.locator("#umcMenuUserSettings").click()
