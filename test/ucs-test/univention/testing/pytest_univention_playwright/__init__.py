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

import os
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import BrowserContext, Page, expect

from univention.testing.browser import logger
from univention.testing.browser.lib import SEC


def check_for_backtrace(page: Page, page_index: int = 0):
    show_backtrace_button = page.get_by_role('button', name='Show server error message')
    notification_502_error = page.get_by_text('An unknown error with status code 502 occurred').first
    try:
        expect(show_backtrace_button.or_(notification_502_error)).to_be_visible(timeout=5 * SEC)
        if show_backtrace_button.is_visible():
            show_backtrace_button.click()
            backtrace_container = page.get_by_role(
                'region',
                name='Hide server error message',
            )
            logger.info(f'Recorded backtrace on page {page_index}')
            print(backtrace_container.inner_text())
        else:
            logger.info('An unknown error with status code 502 occurred while connecting to the server.')
    except AssertionError:
        pass


def print_path_in_jenkins(name: str, ucr):
    subfolder = ''
    if os.environ.get('JENKINS_WS'):
        if 'master' not in ucr.get('server/role'):
            subfolder = f"{ucr.get('hostname')}/"
        full_url = f"{os.environ['JENKINS_WS']}ws/test/{quote(subfolder)}browser/{quote(name)}"
        logger.info('Browser screenshot URL: %s' % full_url)


def save_screenshot(page: Page, node_name, path: Path, ucr, page_index: int = 0):
    ts = time.time_ns()

    screenshot_filename = path / f'{ts}-{node_name}-page_{page_index}.jpeg'

    page.screenshot(path=screenshot_filename)

    print_path_in_jenkins(screenshot_filename.name, ucr)


def save_trace(
    context: BrowserContext,
    node_name: str,
    path: Path,
    ucr,
    tracing_stop_chunk: bool = False,
):
    ts = time.time_ns()

    trace_filename = path / f'{ts}-{node_name}_trace.zip'

    if tracing_stop_chunk:
        context.tracing.stop_chunk(path=trace_filename)
    else:
        context.tracing.stop(path=trace_filename)

    print_path_in_jenkins(trace_filename.name, ucr)
