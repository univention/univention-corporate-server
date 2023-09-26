import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Generator, Iterator
from urllib.parse import quote

import pytest
from playwright.sync_api import BrowserContext, Page, expect

from univention.config_registry import handler_set, handler_unset
from univention.testing import ucr as _ucr, udm as _udm
from univention.testing.browser import logger
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.lib import SEC, UMCBrowserTest
from univention.testing.browser.sidemenu import SideMenuLicense, SideMenuUser
from univention.testing.browser.suggestion import AppCenterCacheTest
from univention.testing.browser.univentionconfigurationregistry import UniventionConfigurationRegistry


@pytest.fixture(scope="session", autouse=True)
def suppress_notifications():
    handler_set(["umc/web/hooks/suppress_umc_notifications=suppress_umc_notifications"])
    yield
    handler_unset(["umc/web/hooks/suppress_umc_notifications"])


phase_report_key = pytest.StashKey[Dict[str, pytest.CollectReport]]()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    item.stash.setdefault(phase_report_key, {})[rep.when] = rep


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "executable_path": "/usr/bin/chromium",
    }


@pytest.fixture(scope="module")
def udm_module_scope() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def ucr_module_scope() -> Iterator[_ucr.UCSTestConfigRegistry]:
    """Per `function` auto-reverting UCR instance."""
    with _ucr.UCSTestConfigRegistry() as ucr:
        yield ucr


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


@pytest.fixture(scope="module")
def kill_module_processes():
    logger.info("killing module processes")
    try:
        subprocess.run(["pkill", "-f", "/usr/sbin/univention-management-console-module"], check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:
            logger.exception("failed killing module processes")
            raise


@pytest.fixture()
def umc_browser_test(
    context: BrowserContext,
    request: pytest.FixtureRequest,
    kill_module_processes,
    ucr,
) -> Generator[UMCBrowserTest, None, None]:
    context.set_default_timeout(60 * 1000 * 2)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    expect.set_options(timeout=15_000)
    tester = UMCBrowserTest(page)
    time.sleep(1)
    yield tester

    report = request.node.stash[phase_report_key]
    try:
        if "call" in report and report["call"].failed:
            save_trace(page, context, request, ucr)
            check_for_backtrace(page)
        else:
            context.tracing.stop()
    finally:
        page.close()


def save_trace(page: Page, context: BrowserContext, request: pytest.FixtureRequest, ucr):
    ts = time.time_ns()

    base_path = Path("browser").resolve()
    screenshot_filename = base_path / f"{ts}-{request.node.name}.jpeg"
    trace_filename = base_path / f"{ts}-{request.node.name}_trace.zip"

    page.screenshot(path=screenshot_filename)
    context.tracing.stop(path=trace_filename)

    if os.environ.get("JENKINS_WS"):
        if "master" not in ucr.get("server/role"):
            subfolder = f"{ucr.get('hostname')}/"
        else:
            subfolder = ""

        browser_trace_url = f"{os.environ['JENKINS_WS']}ws/test/{quote(subfolder)}browser/{quote(trace_filename.name)}"
        browser_screenshot_url = f"{os.environ['JENKINS_WS']}ws/test/{quote(subfolder)}browser/{quote(screenshot_filename.name)}"
        logger.info("Browser trace URL: %s" % browser_trace_url)
        logger.info("Browser screenshot URL: %s" % browser_screenshot_url)


def check_for_backtrace(page: Page):
    show_backtrace_button = page.get_by_role("button", name="Show server error message")
    notification_502_error = page.get_by_text("An unknown error with status code 502 occurred").first
    try:
        expect(show_backtrace_button.or_(notification_502_error)).to_be_visible(timeout=5 * SEC)
        if show_backtrace_button.is_visible():
            show_backtrace_button.click()
            backtrace_container = page.get_by_role(
                "region",
                name="Hide server error message",
            )
            logger.info("Recorded backtrace")
            print(backtrace_container.inner_text())
        else:
            raise Exception("An unknown error with status code 502 occurred while connecting to the server.")
    except AssertionError:
        pass


@pytest.fixture()
def app_center_cache():
    app_center_cache = AppCenterCacheTest()
    yield app_center_cache
    app_center_cache.restore()
