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

from __future__ import annotations

from playwright.sync_api import Locator, Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-framework").translate


class UCSPortalEditMode:
    """This Class is used to interact with the edit mode of the UCS Portal."""

    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self):
        UCSPortal(self.tester).navigate()
        UCSSideMenu(self.tester).navigate()
        self.page.locator('[data-test="openEditmodeButton"]').click()

    def open_edit_side_bar(self):
        """Open the side bar in the edit mode"""
        self.page.get_by_role("button", name=_("Open edit sidebar")).click()

    def upload_background_picture(self, path=""):
        """
        Takes a screenshot of the current page and sets it as the background image.
        The side bar needs to be opened with `open_edit_side_bar` before calling this function
        """
        if not path:
            path = "screenshot.png"
            self.page.screenshot(path="screenshot.png")

        with self.page.expect_file_chooser() as fc_info:
            self.page.locator('[data-test="imageUploadButton--Background"]').click()
        file_chooser = fc_info.value
        file_chooser.set_files("screenshot.png")

        remove_button = self.page.locator('[data-test="imageRemoveButton--Background"]')
        expect(remove_button, "expect the remove button to be enabled after uploading an image").to_be_enabled()

        save_button = self.page.locator('[data-test="editModeSideNavigation--Save"]')
        save_button.click()
        expect(save_button).to_be_hidden()

    def remove_background_picture(self):
        """
        Remove the background picture. A background picture needs to have been set.
        The side bar needs to be opened with `open_edit_side_bar` before calling this function
        """
        remove_button = self.page.locator('[data-test="imageRemoveButton--Background"]')
        remove_button.click()
        expect(remove_button).to_be_disabled()

        save_button = self.page.locator('[data-test="editModeSideNavigation--Save"]')
        save_button.click()
        expect(save_button).to_be_hidden()

    def add_category(self, internal_name: str, name: str):
        """Add a category to the UCS Portal"""
        self.page.get_by_role("button", name=_("Add category")).click()
        self.page.get_by_role("button", name=_("Add new category")).click()
        self.page.get_by_label(_("Internal name *")).fill(internal_name)

        self.fill_localization_dialog(name, "Name")
        self.page.get_by_role("button", name=_("Save")).click()

        expect(self.page.get_by_text(_("Category successfully added"))).to_be_visible()

    def add_entry(self, internal_name: str, name: str, description: str, keyword: str, link: str, category: str):
        """Add a entry to the UCS Portal. The entry will be created in the last category"""
        self.page.locator(".portal-category", has_text=category).get_by_role("button", name=_("Add new tile")).click()

        self.page.get_by_role("button", name=_("Create a new Entry")).click()
        self.page.get_by_label(_("Internal name *")).fill(internal_name)

        self.fill_localization_dialog(name, "Name")
        self.fill_localization_dialog(description, "Description")
        self.fill_localization_dialog(keyword, "Keywords")

        self.page.locator('[data-test="localeInput--Links"]').fill(link)

        self.page.get_by_role("button", name=_("Save")).click()

        expect(self.page.get_by_text(_("Entry successfully added"))).to_be_visible()

    def add_folder(self, internal_name: str, name: str, category: str):
        """Add a folder to the UCS Portal. The folder will be created in the last category"""
        self.page.locator(".portal-category", has_text=category).get_by_role("button", name=_("Add new tile")).click()

        self.page.get_by_role("button", name=_("Create a new folder")).click()
        self.page.get_by_label(_("Internal name *")).fill(internal_name)

        self.fill_localization_dialog(name, "Name")
        self.page.get_by_role("button", name=_("Save")).click()

        expect(self.page.get_by_text("Folder successfully added")).to_be_visible()

    def fill_localization_dialog(
        self,
        text: str,
        data_test_suffix: str = "",
        locator: Locator | None = None,
    ):
        """
        Fill a localization dialog
        The dialog MUST NOT be open when this method is called
        When this method returns the dialog will be closed

        :param text: the text to fill the boxes with. Suffixed with " US" for en_US and " DE" for de_DE
        :param data_test_suffix: this can be used if the button to open to box has an id of the form
                    "[data-test="iconButton--{data_test_suffix}]"
        :param locator: if the data-test attribute does not exist on the button the locator can be passed here
        """
        if locator is not None:
            locator.click()
        else:
            self.page.locator(f'[data-test="iconButton--{data_test_suffix}"]').click()

        self.page.get_by_role("textbox", name="en_US").fill(text + " US")
        self.page.get_by_role("textbox", name="de_DE").fill(text + " DE")
        self.page.get_by_role("dialog", name="Translation: ").get_by_role("button", name="Save").click()


class UCSSideMenu:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self):
        self.page.get_by_role("button", name="Menu").click()

    def open_edit_mode(self) -> UCSPortalEditMode:
        self.page.locator('[data-test="openEditmodeButton"]').click()
        return UCSPortalEditMode(self.tester)


class UCSPortal:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def navigate(self, username="Administrator", password="univention"):
        self.tester.login(username, password, location="/univention/portal")

    def side_menu(self) -> UCSSideMenu:
        return UCSSideMenu(self.tester)
