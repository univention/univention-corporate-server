#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import re
import time

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


logger = logging.getLogger(__name__)

_ = Translation('ucs-test-framework').translate


class UniventionConfigurationRegistry:
    def __init__(self, tester: UMCBrowserTest):
        self.tester = tester
        self.page = tester.page
        self.grid_load_url = re.compile('.*univention/command/ucr/query.*')

    def navigate(self, username='Administrator', password='univention'):
        self.tester.login(username, password)
        self.tester.open_module('Univention Configuration Registry', self.grid_load_url)

    def search(self, text: str):
        search_box = self.page.locator('[name=pattern]')

        search_box.fill(text)
        with self.page.expect_response(self.grid_load_url):
            search_box.press('Enter')

    def get_ucr_module_search_results(self, query: str) -> dict[str, str]:
        """
        Perform a search in the UCR Module and return the key + value for each row

        :param query: The query to search for

        :returns: A dict with the key and value of the variable
        """
        self.search(query)
        # the number of rows - 1 since the header row also gets counted here
        rows = self.page.locator('.dgrid-row').get_by_role('row')
        logger.info("query '%s' returned %d results", query, rows.count())
        keys = rows.locator('.field-key').all()
        values = rows.locator('.field-value').all()

        result = {key.inner_text(): value.inner_text() for (key, value) in zip(keys, values)}
        # ucr_module.page.pause()
        return result

    def set_variable(self, key: str, value: str):
        self.page.get_by_text(key).click()
        time.sleep(1)
        # wait for the loading animation to disappear before filling the textbox
        # TODO: is there a better way?
        for standby in self.page.locator('.umcStandbySvg').all():
            standby.wait_for(state='hidden')
        value_textbox = self.page.get_by_role('textbox', name=_('Value'), exact=True)
        value_textbox.clear()
        value_textbox.fill(value)
        #        self.page.get_by_role("textbox", name=_("Value"), exact=True).fill(value)
        with self.page.expect_response(self.grid_load_url):
            self.page.get_by_role('button', name=_('Save'), exact=True).click()
