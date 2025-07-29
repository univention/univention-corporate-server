#
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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


def print_path_in_jenkins(name: str, ucr, typ='screenshot'):
    subfolder = ''
    if os.environ.get('JENKINS_WS'):
        if 'master' not in ucr.get('server/role'):
            subfolder = f"{ucr.get('hostname')}/"
        full_url = f"{os.environ['JENKINS_WS']}ws/test/{quote(subfolder)}browser/{quote(name)}"
        logger.info('Browser %s URL: %s' % (typ, full_url))


def save_screenshot(page: Page, node_name, path: Path, ucr, page_index: int = 0, timestamp: int | None = None):
    ts = timestamp or time.time_ns()

    screenshot_filename = path / f'{ts}-{node_name}-page_{page_index}.jpeg'

    page.screenshot(path=screenshot_filename)

    print_path_in_jenkins(screenshot_filename.name, ucr)


def save_trace(
    context: BrowserContext,
    node_name: str,
    path: Path,
    ucr,
    tracing_stop_chunk: bool = False,
    timestamp: int | None = None,
):
    ts = timestamp or time.time_ns()

    trace_filename = path / f'{ts}-{node_name}_trace.zip'

    if tracing_stop_chunk:
        context.tracing.stop_chunk(path=trace_filename)
    else:
        context.tracing.stop(path=trace_filename)

    print_path_in_jenkins(trace_filename.name, ucr, 'trace')
