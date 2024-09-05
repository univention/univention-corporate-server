#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright -p repeat
## desc: Test logout refresh
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import json
import time
from typing import List
from urllib.parse import urlparse

import pytest
from playwright.sync_api import BrowserContext, expect
from utils import run_command

from univention.config_registry.frontend import ucr_update
from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.portal import UCSPortal, UCSSideMenu


_ = Translation('ucs-test-browser').translate

num_tabs = 4


@pytest.fixture(autouse=True, scope='module')
def enable_logout_refresh(ucr_proper):
    print('enabling logout refresh')
    original = ucr_proper['portal/reload-tabs-on-logout']
    ucr_update(ucr_proper, {
        'portal/reload-tabs-on-logout': 'true'
    })

    yield

    ucr_update(ucr_proper, {
        'portal/reload-tabs-on-logout': original
    })


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


def login_tabs(tabs: List[UCSPortal], protocol: str, login_func):
    login_func(tabs[0].page, 'Administrator', 'univention', protocol=protocol)

    expect(tabs[0].page.get_by_role('link', name=_('Software update')), message='Initial login not successful').to_be_visible()
    portal_url = urlparse(tabs[0].page.url)
    for i, tab in enumerate(tabs[1:]):
        tab.navigate(do_login=False, portal_url=f'{portal_url.scheme}://{portal_url.netloc}')
        expect(tab.page.get_by_role('link', name=_('Software update')), message=f'Tab {i + 1} not logged in').to_be_visible()


@pytest.mark.repeat(5)
@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_logout_refresh_sso(multi_tab_context: BrowserContext, portal_login_via_keycloak_custom_page, protocol: str):
    tabs = [UCSPortal(UMCBrowserTest(multi_tab_context.new_page())) for _ in range(num_tabs)]

    login_tabs(tabs, protocol, portal_login_via_keycloak_custom_page)

    page1_side_menu = UCSSideMenu(tabs[0].tester)
    page1_side_menu.navigate()
    page1_side_menu.logout()
    login_locator = tabs[0].page.get_by_role('link', name=_('Login Same tab'), exact=True)
    logout_locator = tabs[0].page.get_by_role("button", name="Logout")
    expect(login_locator.or_(logout_locator), 'neither the keycloak logout locator nor the portal login locator is visible').to_be_visible()
    if logout_locator.is_visible():
        logout_locator.click()

    for i, tab in enumerate(tabs):
        expect(tab.page.get_by_role('link', name=_('Login Same tab'), exact=True), message=f'Tab {i} not logged out').to_be_visible()


def umc_db_is_postgres():
    umc_settings = json.loads(run_command(['univention-management-console-settings', '-j', 'get']))
    return 'sqlURI' in umc_settings and umc_settings['sqlURI'] is not None and 'postgresql+psycopg2' in umc_settings['sqlURI']


def do_login_logout(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context, needs_manual_refresh):
    username = udm.create_user()[1]

    portal_hostname = portal_config.fqdn
    multi_tab_context.add_cookies([{
        "name": "UMCWEB_ROUTEID",
        "value": ".2",
        "domain": portal_hostname,
        "path": "/",
    }])
    login_page, logout_page = multi_tab_context.new_page(), multi_tab_context.new_page()
    portal_login_via_keycloak_custom_page(login_page, username, "univention", protocol="oidc")
    time.sleep(3)
    logout_page.goto(keycloak_config.logout_url)
    logout_page.get_by_role('button', name='Logout').click()

    time.sleep(3)
    if needs_manual_refresh:
        login_page.reload()
    expect(login_page.get_by_role('link', name=_('Login Same tab'), exact=True), message='Tab not logged out').to_be_visible()


@pytest.mark.repeat(5)
@pytest.mark.parametrize('oidc_client_logout_meachanism', ['backchannel', 'frontchannel'], indirect=True)
def test_oidc_backchannel_login_logout_with_automatic_refresh(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context, oidc_client_logout_meachanism, ucr_proper):
    if not umc_db_is_postgres() and oidc_client_logout_meachanism == 'backchannel' and int(ucr_proper.get('umc/http/processes')) != 1:
        pytest.skip('Automatic logout refresh does not work if logout mechanism is backchannel AND the database is not postgres AND umc multiprocessing is enabled')
    do_login_logout(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context, False)


@pytest.mark.skipif(umc_db_is_postgres(), reason='Configured database for UMC is postgres')
@pytest.mark.repeat(5)
@pytest.mark.usefixtures('oidc_client_logout_meachanism')
@pytest.mark.parametrize('oidc_client_logout_meachanism', ['backchannel', 'frontchannel'], indirect=True)
def test_oidc_backchannel_login_logout_with_manual_refresh(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context, ucr_proper):
    if int(ucr_proper.get('umc/http/processes')) == 1:
        pytest.skip('No need to test manual refresh when multiprocessing disabled.')
    do_login_logout(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context, True)
