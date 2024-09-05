#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test logout refresh
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

from types import SimpleNamespace
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.portal import UCSPortal, UCSSideMenu
from univention.testing.pytest_univention_playwright import fixtures


_ = Translation('ucs-test-browser').translate

num_tabs = 4


@pytest.fixture()
def multi_tab_context(browser: Browser, request: pytest.FixtureRequest, ucr) -> Generator[BrowserContext, None, None]:
    context = browser.new_context(ignore_https_errors=True)
    context.set_default_timeout(30 * 1000)
    expect.set_options(timeout=30 * 1000)

    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    fixtures.teardown_umc_browser_test(request, ucr, context.pages, context, browser)


def test_logout_refresh_plain(multi_tab_context: BrowserContext):
    tabs = [UCSPortal(UMCBrowserTest(multi_tab_context.new_page())) for _ in range(num_tabs)]
    tabs[0].navigate()
    expect(tabs[0].page.get_by_role('link', name=_('Users'))).to_be_visible()
    for tab in tabs[1:]:
        tab.navigate(do_login=False)
        expect(tab.page.get_by_role('link', name=_('Users'))).to_be_visible()

    page1_side_menu = UCSSideMenu(tabs[0].tester)
    page1_side_menu.navigate()
    page1_side_menu.logout()

    for tab in tabs:
        expect(tab.page.get_by_role('link', name=_('Login Same tab'), exact=True)).to_be_visible()


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_logout_refresh_sso(multi_tab_context: BrowserContext, portal_login_via_keycloak_custom_page, protocol: str):
    tabs = [UCSPortal(UMCBrowserTest(multi_tab_context.new_page())) for _ in range(num_tabs)]

    portal_login_via_keycloak_custom_page(tabs[0].page, 'Administrator', 'univention', protocol=protocol)
    expect(tabs[0].page.get_by_role('link', name=_('Users')), message='Initial login not successful').to_be_visible()
    for i, tab in enumerate(tabs[1:]):
        tab.navigate(do_login=False)
        expect(tab.page.get_by_role('link', name=_('Users')), message=f'Tab {i} not logged in').to_be_visible()

    page1_side_menu = UCSSideMenu(tabs[0].tester)
    page1_side_menu.navigate()
    page1_side_menu.logout()

    for i, tab in enumerate(tabs):
        expect(tab.page.get_by_role('link', name=_('Login Same tab'), exact=True), message=f'Tab {i} not logged out').to_be_visible()


def test_logout_refresh_oidc_backchannel(multi_tab_context: BrowserContext, portal_login_via_keycloak_custom_page, keycloak_config: SimpleNamespace):
    tabs = [UCSPortal(UMCBrowserTest(multi_tab_context.new_page())) for _ in range(num_tabs)]

    portal_login_via_keycloak_custom_page(tabs[0].page, 'Administrator', 'univention', protocol='oidc')
    expect(tabs[0].page.get_by_role('link', name=_('Users')), message='Initial login not successful').to_be_visible()
    for i, tab in enumerate(tabs[1:]):
        tab.navigate(do_login=False)
        expect(tab.page.get_by_role('link', name=_('Users')), message=f'Tab {i} not logged in').to_be_visible()

    backchannel_logout_tab = multi_tab_context.new_page()
    backchannel_logout_url = f'{keycloak_config.url}/realms/ucs/protocol/openid-connect/logout'
    backchannel_logout_tab.goto(backchannel_logout_url)
    backchannel_logout_tab.get_by_role('button', name='Logout').click()

    for i, tab in enumerate(tabs):
        expect(tab.page.get_by_role('link', name=_('Login Same tab'), exact=True), message=f'Tab {i} not logged out').to_be_visible()
