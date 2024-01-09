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

import re
import subprocess
import time

from playwright.sync_api import Page, expect
from typing_extensions import Literal

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-framework').translate

available_categories = Literal['All', 'User', 'PID', 'Command']


class ProcessOverview:
    def __init__(self, tester: UMCBrowserTest):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name = _('Process overview')
        self.grid_load_url = re.compile('.*univention/command/top/query.*')

    def navigate(self, username='Administrator', password='univention'):
        self.tester.login(username, password)
        self.tester.open_module(self.module_name, self.grid_load_url)

    def search(self, category: available_categories, text: str):
        """
        Run a search

        :param category: the category to search for. NOTICE: this argument gets translated in the function
        :param text: the text to search for
        """
        # usually caller is responsible for translating but here it makes more sense to translate here
        # so we can have nice typing
        category = _(category)
        text_boxes = self.page.get_by_role('textbox')

        category_textbox = self.page.get_by_label('Category')
        search_textbox = text_boxes.nth(2)
        category_textbox.click()
        expect(category_textbox).to_be_enabled()
        category_textbox.clear()
        category_textbox.fill(category)

        search_textbox.fill(text)
        with self.page.expect_response(self.grid_load_url):
            search_textbox.press('Enter')

    def ensure_process(self, process: subprocess.Popen, category: available_categories):
        """
        Ensures that a process is running, either by PID or Command

        :param process: the process to search for. If searching by name the process args are joined together
                         if searching by pid, process.pid is used
        :param category: the category to search for the process by. Currently only PID and Command are supported
        """
        process_name = ' '.join(process.args)
        if category == 'PID':
            self.search('PID', str(process.pid))
        else:
            self.search('Command', process_name)

    def kill_process(self, process: subprocess.Popen, force: bool):
        """
        Kills the process given by process and ensures that is was actually killed

        :param process: the process to kill
        :param force: if false sends SIGTERM to the process by pressing the Terminate button
                          if true sends SIGKILL to the process by pressing the 'Force termination' button

        """
        process_pid = str(process.pid)
        self.search('PID', process_pid)
        self.page.get_by_role('gridcell', name=str(process_pid), exact=True).click()

        button = self.page.get_by_role('button', name=f"{_('Force termination') if force else _('Terminate')}")
        button.click()

        # without this sleep the button sometimes doesn't get clicked correctly
        time.sleep(1)
        confirmation_dialog = self.page.get_by_role('dialog')
        confirmation_dialog.get_by_role('button', name='Ok').click()
        expect(confirmation_dialog).to_be_hidden()

        with self.page.expect_response(self.grid_load_url):
            pass

        expected_return_code = -9 if force else -15
        return_code = process.poll()
        assert expected_return_code == return_code, f'Expected return code to be {expected_return_code} but got {return_code}'

        self.search('PID', process_pid)
        cell = self.page.get_by_role('gridcell', name=process_pid)
        expect(cell).to_be_hidden()
