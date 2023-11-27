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

from __future__ import annotations

import logging
import re
import subprocess
import time
import urllib.parse
from enum import Enum
from typing import List

from playwright.sync_api import Page, expect

from univention.config_registry import ucr
from univention.lib.i18n import Translation


logger = logging.getLogger(__name__)

SEC = 1000
MIN = 60 * 1000

translator = Translation("ucs-test-framework")
_ = translator.translate


class UCSLanguage(Enum):
    EN_US = 1
    DE_DE = 2

    def __str__(self) -> str:
        if self == UCSLanguage.EN_US:
            return "en-US"
        elif self == UCSLanguage.DE_DE:
            return "de-DE"

        return ""

    def get_name(self) -> str:
        if self == UCSLanguage.EN_US:
            return "English"
        elif self == UCSLanguage.DE_DE:
            return "Deutsch"

        return ""


class Interactions:
    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page

    def check_second_checkbox_in_grid(self):
        """
        This function checks the second checkbox in a grid

        Note:
            Prefer to use `check_checkbox_in_grid_by_name` when possible
        """
        checkbox = self.page.get_by_role("checkbox")
        expect(checkbox).to_have_count(2)
        checkbox.last.check()

    def check_checkbox_in_grid_by_name(self, name: str, nth: int | None = None):
        """
        This function checks a checkbox in a <tr> where the given `name` appears

        :param name: the name to search for
        :param nth: controls what to do when there are multiple entries with `name` found. If none the function will throw an exception
                                    if `int` the function will act on the nth occurrence of the text
        """
        row = self.page.locator(f"tr:has-text('{name}')")
        if nth is not None:
            row = row.nth(nth)
        expect(row).to_be_visible(timeout=10 * 1000)
        checkbox = row.get_by_role("checkbox")
        expect(checkbox).to_be_visible(timeout=10 * 1000)
        checkbox.click()

    def open_modules(self, modules: List[str], limit: int | None = None, start_at: int | None = None):
        """
        This method will open all modules given by `modules`.
        It does this by searching for the module in the UMC, clicking on it and then clicking the close button

        :param limit: optionally only open the first `limit` modules
        :param start_at: starts opening
        """
        for module in modules[start_at:limit]:
            logger.info("Opening module %s" % module)
            self.open_and_close_module(module)
            logger.info("Closed module %s" % module)
            time.sleep(1)

    def open_all_modules(self, limit: int | None = None, start_at: int | None = None):
        """
        This method opens all modules that can be found in the UMC when searching for '*'

        :param limit: optionally only open the first `limit` modules
        :param start_at: starts opening
        """
        modules = self.get_available_modules()
        logger.info("Found %d modules" % len(modules))
        self.open_modules(modules, limit=limit, start_at=start_at)

    def open_and_close_module(self, module_name: str):
        self.open_module(_(module_name))
        self.page.get_by_role("button", name=_("Close")).click()

    def get_available_modules(self) -> List[str]:
        self.page.locator(".umcModuleSearchToggleButton").click()
        logger.info("Clicked the search button")
        self.page.locator(".umcModuleSearch input.dijitInputInner").type("*")

        modules = self.page.locator(".umcGalleryName").all()
        result = [module.get_attribute("title") or module.inner_text() for module in modules]

        self.page.locator(".umcModuleSearchToggleButton").click()
        return result

    def open_module(self, module_name: str, expect_response: re.Pattern | str | None = None):
        """
        This method opens a module from anywhere where the module search bar in the UCM is visible

        :param module_name: the name of the module to be opened
        """
        self.page.locator(".umcModuleSearchToggleButton").click()
        logger.info("Clicked the search button")
        self.page.locator(".umcModuleSearch input.dijitInputInner").type(module_name)
        module_by_title_attrib_locator = self.page.locator(f".umcGalleryName[title='{module_name}']")
        exact_module_name = re.compile(f"^{re.escape(module_name)}$")
        logger.info("Trying to find button to open module %s" % module_name)
        module_locator = self.page.locator(".umcGalleryName", has_text=exact_module_name)
        expect(module_locator.or_(module_by_title_attrib_locator)).to_be_visible()

        if module_by_title_attrib_locator.is_visible():
            clickable_module_locator = module_by_title_attrib_locator
        else:
            clickable_module_locator = module_locator

        if expect_response is not None:
            with self.page.expect_response(expect_response):
                clickable_module_locator.click()
        else:
            clickable_module_locator.click()
        logger.info("Clicked the module button")
        if module_name == "App Center":
            from univention.testing.browser.appcenter import AppCenter, wait_for_final_query

            app_center = AppCenter(self.tester)
            with self.page.expect_response(lambda request: wait_for_final_query(request), timeout=2 * MIN):
                app_center.handle_first_open_dialog()

    def fill_combobox(self, name: str, option: str):
        # combobox_filter = self.page.locator(f"input[name='{name}'][type='hidden']")
        combobox_filter = self.page.get_by_label(name)
        self.page.get_by_role("combobox").filter(has=combobox_filter).locator(".ucsSimpleIconButton").click()
        self.page.get_by_role("option", name=option).click()


class UMCBrowserTest(Interactions):
    """
    This is the base class for all Playwright browser tests. It defines common operations and methods
    that are useful to all other library modules.

    Note:
        As a general rule of this library, unless otherwise noted, the caller is responsible for the translation of a string

    :param page: The Playwright Page object
    :param lang: The language to use for UCS
    """

    lang: UCSLanguage

    def __init__(self, page: Page, lang: UCSLanguage = UCSLanguage.EN_US):
        self.page: Page = page
        self.set_language(lang)
        Interactions.__init__(self, self)

    def set_language(self, lang: UCSLanguage):
        logger.info("Setting language to %s" % lang)
        self.lang = lang
        self.__set_lang(str(lang))
        translator.set_language(str(lang).replace("-", "_"))

    def __set_lang(self, lang: str):
        self.page.context.clear_cookies()
        cookies = [
            {
                "name": "UMCLang",
                "value": lang,
                "url": f"{self.base_url}/univention",
            },
        ]

        role = ucr.get("server/role")

        # if we are not on the master we also need to set the language cookie for the master
        if role != "domaincontroller_master":
            cookies.append({
                "name": "UMCLang",
                "value": lang,
                "url": f"https://{ucr.get('ldap/master')}/univention",
            })

        self.page.context.add_cookies(cookies)

    @property
    def base_url(self) -> str:
        """:return: the base url in the form of https://{hostname}.{domainname}"""
        return f"https://{ucr.get('hostname')}.{self.domainname}"

    @property
    def ldap_base(self) -> str:
        return ucr["ldap/base"]

    @property
    def domainname(self) -> str:
        return ucr["domainname"]

    def check_for_no_module_available_popup(self):
        popup = self.page.get_by_role("dialog").get_by_text("There is no module available for the authenticated user")
        expect(popup).to_be_visible(timeout=30 * SEC)

        button = self.page.get_by_role("button", name=_("Ok"))
        expect(button).to_be_visible()
        button.click()

    def login(
        self,
        username: str = "Administrator",
        password: str = "univention",
        location: str = "/univention/management",
        check_for_no_module_available_popup: bool = False,
        login_should_fail: bool = False,
        do_navigation: bool = True,
        expect_password_change_prompt: bool = False,
        skip_xhr_check: bool = False,
    ):
        """
        Navigates to {base_url}/univention/login?location={location} and logs in with the given credentials

        :param username: The username of the user to be logged in
        :param password: The password of the user to be logged in
        :param location: the location to navigate to after a successful login. This value is being URL encoded
        :param check_for_no_module_available_popup: If set to true check for a "There is no module available for the..." popup after login
        :param login_should_fail: Returns after failure to log in with wrong credentials
        :param do_navigation: Wether to navigate to the login page
        :param expect_password_change_prompt: Expect a password change prompt to be visible after clicking the Login button
        :param skip_xhr_check: Skip the check for certain requests to be completed
        """
        logger.info("Starting login to '%s' " % location)
        page = self.page

        if do_navigation:
            location = urllib.parse.quote(location)
            query_parameter = f"?location={location}" if location else ""
            page.goto(f"{self.base_url}/univention/login{query_parameter}")

        page.get_by_label(_("Username"), exact=True).fill(username)
        page.get_by_label(_("Password"), exact=True).fill(password)
        login_button = page.get_by_role("button", name=_("Login"))

        if expect_password_change_prompt:
            logger.info("Expecting the password change prompt. Only clicking button")
            login_button.click()
            return

        if login_should_fail:
            login_button.click()
            expect(page.get_by_text(_("The authentication has failed, please login again."))).to_be_visible(timeout=1 * MIN)
            logger.info("Login failed as expected")
            return

        if "/univention/management" in location and not check_for_no_module_available_popup and not skip_xhr_check:
            logger.info("Logging in, waiting for requests to finish")
            join_script_query = re.compile(r"https?://.+/univention/command/join/scripts/query")
            license_query = re.compile(r"https?://.+/univention/command/udm/license")

            if ucr.get("server/role") == "domaincontroller_master":
                with self.page.expect_response(join_script_query), self.page.expect_response(license_query):
                    login_button.click()
            else:
                with self.page.expect_response(join_script_query):
                    login_button.click()
        elif check_for_no_module_available_popup:
            login_button.click()
            logger.info("Checking for the 'No module for user available popup'")
            self.check_for_no_module_available_popup()
        else:
            logger.info("Logging in without waiting for requests to finish")
            login_button.click()

        # TODO: wait_until networkidle is discouraged by Playwright, replace at some point
        self.page.wait_for_url(re.compile(r".*univention/(management|portal).*"), wait_until="networkidle")
        logging.info("Login Done")

    def end_umc_session(self):
        """Logs the current logged in user out by navigating to /univention/login"""
        self.page.goto(f"{self.base_url}/univention/logout")

    def logout(self):
        """
        Logout using the Side Menu

        This method is merely a shortcut for `SideMenu.logout()`
        """
        from univention.testing.browser.sidemenu import SideMenu

        side_menu = SideMenu(self)
        side_menu.navigate(do_login=False)
        side_menu.logout()

    def systemd_restart_service(self, service: str):
        logger.info("restarting service %s" % service)
        subprocess.run(["deb-systemd-invoke", "restart", service], check=True)

    def restart_umc(self):
        self.systemd_restart_service("univention-management-console-server")
        time.sleep(3)
