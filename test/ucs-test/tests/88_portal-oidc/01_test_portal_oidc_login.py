#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test login to portal via OIDC
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous
import json
import time

import pytest
from playwright.sync_api import Page, expect

from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.portal import KeycloakLoginPage, UCSPortal, UCSPortalEditMode


PORTAL_JSON = '/usr/share/univention-portal/portals.json'


def is_oidc_authenticator():
    with open(PORTAL_JSON) as f:
        portals = json.loads(f.read())
    try:
        authenticator = portals['default']['kwargs']['authenticator']['class']
        return authenticator == 'OIDCAuthenticator'
    except KeyError:
        return False


oidc_authenticator = pytest.mark.skipif(not is_oidc_authenticator(), reason='Configured default portal authenticator is not OIDCAuthenticator')


def login_with_side_menu(umc_browser_test):
    portal = UCSPortal(umc_browser_test)
    portal.navigate(do_login=False)
    side_menu = portal.side_menu()
    side_menu.navigate()
    side_menu.login()

    keycloak_login_page = KeycloakLoginPage(umc_browser_test)
    keycloak_login_page.login()

    side_menu.navigate()


@oidc_authenticator
def test_login(umc_browser_test: UMCBrowserTest):
    login_with_side_menu(umc_browser_test)
    expect(umc_browser_test.page.get_by_role('button', name="Logout")).to_be_visible()


# move this to lib
def wait_for_dialog_to_disappear(page: Page):
    expect(page.get_by_role('dialog')).to_be_hidden()


# move this to lib
def search_for_udm_object(module: str, name: str, udm, timeout: int = 10):
    udm_module = udm.get(module)

    end = time.monotonic() + timeout
    while time.monotonic() < end:
        entries = list(udm_module.search(f'name={name}'))
        if len(entries) != 0:
            return entries[0]

        time.sleep(0.2)

    pytest.fail(f'Failed to find {name} in {module} after {timeout} seconds')


@oidc_authenticator
def test_edit_mode(umc_browser_test: UMCBrowserTest):
    login_with_side_menu(umc_browser_test)
    edit_mode = UCSPortalEditMode(umc_browser_test)

    category_name = 'internal-name-for-category'
    category_display_name = 'Category Name'
    edit_mode.add_category(category_name, category_display_name)
