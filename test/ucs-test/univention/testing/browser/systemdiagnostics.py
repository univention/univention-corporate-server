#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from playwright.sync_api import Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import MIN, UMCBrowserTest


_ = Translation('ucs-test-framework').translate


class SystemDiagnostic:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _('System diagnostic')

    def navigate(self, username='Administrator', password='univention'):
        self.tester.login(username, password)
        self.tester.open_module(self.module_name)

        self.wait_for_system_diagnostics_to_finish()

    def run_system_diagnostics(self):
        self.page.get_by_role('button', name=_('Run system diagnosis')).click()
        self.wait_for_system_diagnostics_to_finish()

    def wait_for_system_diagnostics_to_finish(self):
        progress_bar = self.page.get_by_role('progressbar')
        try:
            expect(progress_bar).to_be_visible(timeout=1 * MIN)
            expect(progress_bar).to_be_hidden(timeout=5 * MIN)
        except AssertionError:
            pass
