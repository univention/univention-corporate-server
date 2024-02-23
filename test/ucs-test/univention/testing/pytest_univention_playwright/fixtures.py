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

import subprocess
from pathlib import Path
from typing import Dict, Generator, Iterator

import pytest
from playwright.sync_api import BrowserContext, BrowserType, Page, expect

from univention.config_registry import handler_set, handler_unset
from univention.testing import udm as _udm
from univention.testing.browser import logger
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.ldap_directory import LDAPDirectory
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.selfservice import SelfService
from univention.testing.browser.sidemenu import SideMenuLicense, SideMenuUser
from univention.testing.browser.suggestion import AppCenterCacheTest
from univention.testing.browser.univentionconfigurationregistry import UniventionConfigurationRegistry

from . import check_for_backtrace, save_trace


@pytest.fixture(scope='session', autouse=True)
def suppress_notifications():
    handler_set(['umc/web/hooks/suppress_umc_notifications=suppress_umc_notifications'])
    yield
    handler_unset(['umc/web/hooks/suppress_umc_notifications'])


phase_report_key = pytest.StashKey[Dict[str, pytest.CollectReport]]()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    item.stash.setdefault(phase_report_key, {})[rep.when] = rep


@pytest.fixture(scope='session')
def ucs_browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        'ignore_https_errors': True,
    }


@pytest.fixture(scope='session')
def ucs_browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        'executable_path': '/usr/bin/chromium',
        'args': [
            '--disable-gpu',
        ],
    }


@pytest.fixture(scope='module')
def udm_module_scope() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def ucr_module(umc_browser_test: UMCBrowserTest):
    return UniventionConfigurationRegistry(umc_browser_test)


@pytest.fixture()
def user_module(umc_browser_test: UMCBrowserTest):
    return UserModule(umc_browser_test)


@pytest.fixture()
def side_menu_license(umc_browser_test: UMCBrowserTest):
    return SideMenuLicense(umc_browser_test)


@pytest.fixture()
def side_menu_user(umc_browser_test: UMCBrowserTest):
    return SideMenuUser(umc_browser_test)


@pytest.fixture()
def self_service(umc_browser_test: UMCBrowserTest) -> SelfService:
    return SelfService(umc_browser_test)


@pytest.fixture()
def ldap_directory(umc_browser_test: UMCBrowserTest) -> LDAPDirectory:
    return LDAPDirectory(umc_browser_test)


@pytest.fixture(scope='module')
def kill_module_processes():
    logger.info('killing module processes')
    try:
        subprocess.run(
            ['pkill', '-f', '/usr/sbin/univention-management-console-module'],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:
            logger.exception('failed killing module processes')
            raise


def setup_browser_context(context, start_tracing=True):
    context.set_default_timeout(30 * 1000)
    expect.set_options(timeout=30 * 1000)
    if start_tracing:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    return page


@pytest.fixture(scope='module')
def context_module_scope(
    browser_type: BrowserType,
    ucs_browser_type_launch_args: Dict,
    ucs_browser_context_args: Dict,
):
    browser = browser_type.launch(**ucs_browser_type_launch_args)
    return browser.new_context(**ucs_browser_context_args)


@pytest.fixture(scope='module')
def umc_browser_test_module(
    context_module_scope: BrowserContext,
    kill_module_processes,
) -> UMCBrowserTest:
    page = setup_browser_context(context_module_scope)
    tester = UMCBrowserTest(page)

    return tester


@pytest.fixture()
def umc_browser_test(
    browser_type: BrowserType,
    ucs_browser_type_launch_args: Dict,
    ucs_browser_context_args: Dict,
    request: pytest.FixtureRequest,
    kill_module_processes,
    ucr,
) -> Generator[UMCBrowserTest, None, None]:
    browser = browser_type.launch(**ucs_browser_type_launch_args)
    context = browser.new_context(**ucs_browser_context_args)
    page = setup_browser_context(context)
    tester = UMCBrowserTest(page)

    yield tester

    teardown_umc_browser_test(request, ucr, page, context)


def teardown_umc_browser_test(
    request: pytest.FixtureRequest,
    ucr,
    page: Page,
    context: BrowserContext,
):
    try:
        report = request.node.stash[phase_report_key]
    except KeyError:
        logger.warning(
            'phase_report_key has not been found in node stash. Skipping trace saving and backtrace checking.',
        )
        return

    try:
        if 'call' in report and report['call'].failed:
            save_trace(page, context, request.node.name, Path('browser').resolve(), ucr)
            check_for_backtrace(page)
        else:
            context.tracing.stop()
    finally:
        page.close()


@pytest.fixture()
def app_center_cache():
    app_center_cache = AppCenterCacheTest()
    yield app_center_cache
    app_center_cache.restore()
