#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import enum
import logging
import re

import apt
from playwright.sync_api import Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import MIN, UMCBrowserTest


logger = logging.getLogger(__name__)

KB = 1000
MB = KB * 1000

_ = Translation('ucs-test-framework').translate


class PackageAction(enum.Enum):
    Install = 1
    Uninstall = 2

    def __str__(self) -> str:
        if self == PackageAction.Install:
            return _('Install')
        elif self == PackageAction.Uninstall:
            return _('Uninstall')

        return ''

    def expected_status(self) -> str:
        if self == PackageAction.Install:
            return _('installed')
        elif self == PackageAction.Uninstall:
            return _('not installed')

        return ''


class PackageManagement:
    """Class for the Package Management UCS Module"""

    def __init__(self, tester: UMCBrowserTest) -> None:
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _('Package Management')
        self.grid_load_url = re.compile('.*univention/command/appcenter/packages/query.*')
        self.initial_grid_load_url = re.compile('.*univention/command/appcenter/packages/sections.*')

    def navigate(self, username='Administrator', password='univention'):
        self.tester.login(username, password)
        self.tester.open_module(self.module_name, self.initial_grid_load_url)

    def find_small_package(self) -> str:
        """
        Finds a small package that is less than 0.5 MB, has no dependencies and recommended packages

        :return: the package name
        """
        logger.info('Trying to find small, uninstalled package with no dependencies and recommends')
        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        for package in cache:
            if (
                package.candidate
                and not package.is_installed
                and package.candidate.installed_size < 0.5 * MB
                and not package.candidate.recommends
                and not package.candidate.dependencies
            ):
                logger.info('Found %s' % package)
                return package.name

        raise Exception('Failed to find a small package')

    def search_for_package(self, name: str):
        search_bar = self.page.locator('[name=pattern]')
        search_bar.fill('')
        search_bar.press_sequentially(name)
        with self.page.expect_response(self.grid_load_url):
            search_bar.press('Enter')

    def do_package_action(self, name: str, action: PackageAction):
        logger.info('Action %s on package %s' % (action, name))
        self.search_for_package(name)
        self.tester.check_checkbox_in_grid_by_name(name, 0)
        self.page.get_by_role('button', name=str(action), exact=True).click()

        self.handle_confirmation_dialog(str(action))
        self.handle_action_dialog()
        logger.info('%s done' % action)
        with self.page.expect_response(self.grid_load_url):
            pass

    def handle_confirmation_dialog(self, action: str):
        dialog = self.page.get_by_role('dialog', name=_('Confirmation'))
        dialog.get_by_role('button', name=action).click()
        expect(dialog).to_have_count(0)

    def handle_action_dialog(self):
        dialog = self.page.get_by_role('dialog')
        expect(dialog).to_have_count(0, timeout=3 * MIN)

        pbar = self.page.get_by_role('progressbar')
        expect(pbar).to_have_count(0, timeout=3 * MIN)

    def install_package(self, name: str):
        """Installs a package that is automatically chosen to be both small in size and has no dependencies and verifies that it is installed"""
        self.do_package_action(name, PackageAction.Install)
        self.verify_package_status(PackageAction.Install)

    def uninstall_package(self, name: str):
        self.do_package_action(name, PackageAction.Uninstall)
        self.verify_package_status(PackageAction.Uninstall)

    def verify_package_status(self, expected: PackageAction):
        """
        Verify that the package actually got (un)installed

        :param expected: If expected is `PackageAction.Install` this function will make sure that the package has been _installed_ and vice versa.
        """
        status_cell = self.page.get_by_role('grid').get_by_role('gridcell').get_by_text(expected.expected_status())
        expect(status_cell).to_have_count(1)
        expect(status_cell).to_be_visible()
