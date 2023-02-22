# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2023 Univention GmbH
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

from types import SimpleNamespace

import pytest
from selenium import webdriver
from utils import get_portal_tile, wait_for_class, wait_for_id

from univention.config_registry import ConfigRegistry
from univention.lib.misc import custom_groupname


@pytest.fixture()
def portal_config(ucr: ConfigRegistry) -> SimpleNamespace:
    config = {
        "url": f"https://{ucr['hostname']}.{ucr['domainname']}/univention/portal",
        "title": "Univention Portal",
        "sso_login_tile": "Login (Single sign-on)",
        "sso_login_tile_de": "Anmelden (Single Sign-on)",
        "tile_name_class": "portal-tile__name",
        "category_title_class": "portal-category__title",
        "categories_id": "portalCategories",
        "tile_class": "portal-tile",
        "groups_tile": "School groups",
        "users_tile": "School users",
        "username": "admin",
        "password": "univention",
        "header_menu_id": "header-button-menu",
    }

    return SimpleNamespace(**config)


@pytest.fixture()
def keycloak_config(ucr: ConfigRegistry) -> SimpleNamespace:
    url = f"https://ucs-sso-ng.{ucr['domainname']}"
    config = {
        "url": url,
        "token_url": f"{url}/realms/master/protocol/openid-connect/token",
        "client_session_stats_url": f"{url}/admin/realms/ucs/client-session-stats",
        "logout_all_url": f"{url}/admin/realms/ucs/logout-all",
        "title": "Welcome to Keycloak",
        "admin_console_class": "welcome-primary-link",
        "realm_selector_class": "realm-selector",
        "login_data": {
            "client_id": "admin-cli",
            "username": "Administrator",
            "password": "univention",
            "grant_type": "password",
        },
        "logout_all_data": {"realm": "ucs"},
        "login_id": "kc-login",
        "username_id": "username",
        "password_id": "password",
        "input_error_id": "input-error",
        "wrong_password_msg": "Invalid username or password.",
        "kc_passwd_update_form_id": "kc-passwd-update-form",
        "password_confirm_id": "password-confirm",
        "password_new_id": "password-new",
        "password_update_feedback_class": "pf-c-alert__title kc-feedback-text",
        "password_change_button_id": "kc-form-buttons",
    }
    return SimpleNamespace(**config)


@pytest.fixture()
def ucr() -> ConfigRegistry:
    ucr = ConfigRegistry()
    return ucr.load()


@pytest.fixture()
def selenium() -> webdriver.Chrome:
    """Browser based testing for using Selenium."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")  # chrome complains about being executed as root
    chrome_options.add_argument("ignore-certificate-errors")
    # seems not to work for keycloak
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'de_DE'})
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


@pytest.fixture()
def portal_login_via_keycloak(selenium: webdriver.Chrome, portal_config: SimpleNamespace, keycloak_config: SimpleNamespace):
    selenium.get(portal_config.url)
    wait_for_id(selenium, portal_config.categories_id)
    assert selenium.title == portal_config.title
    portal = selenium

    def _func(
        username: str,
        password: str,
        fails_with: str = "",
        new_password: str = "",
        new_password_confirm: str = "",
    ) -> bool:
        get_portal_tile(portal, portal_config.sso_login_tile_de, portal_config).click()
        # login
        _keycloak_login(portal, keycloak_config, username, password)
        # check password change
        if new_password:
            new_password_confirm = new_password_confirm if new_password_confirm else new_password
            _keycloak_password_change(portal, keycloak_config, password, new_password, new_password_confirm)
            if fails_with:
                error = portal.find_element_by_css_selector(f"span[class='{keycloak_config.password_update_feedback_class}']")
                assert fails_with == error.text
                assert error.is_displayed()
                return True
        # login succeeded?
        else:
            if fails_with:
                error = portal.find_element_by_id(keycloak_config.input_error_id)
                assert fails_with == error.text
                assert error.is_displayed()
                return True
        # check that we are logged in
        wait_for_id(portal, portal_config.header_menu_id)
        return True
    return _func


def _keycloak_password_change(
    keycloak: webdriver.Chrome,
    keycloak_config: SimpleNamespace,
    password: str,
    new_password: str,
    new_password_confirm: str,
) -> None:
    # TODO verify password change error message
    wait_for_id(keycloak, keycloak_config.kc_passwd_update_form_id)
    keycloak.find_element_by_id(keycloak_config.password_id).send_keys(password)
    keycloak.find_element_by_id(keycloak_config.password_new_id).send_keys(new_password)
    keycloak.find_element_by_id(keycloak_config.password_confirm_id).send_keys(new_password_confirm)
    keycloak.find_element_by_id(keycloak_config.password_change_button_id).click()


def _keycloak_login(keycloak: webdriver.Chrome, keycloak_config: SimpleNamespace, username: str, password: str) -> None:
    wait_for_id(keycloak, keycloak_config.username_id)
    wait_for_id(keycloak, keycloak_config.password_id)
    wait_for_id(keycloak, keycloak_config.login_id)
    keycloak.find_element_by_id(keycloak_config.username_id).send_keys(username)
    keycloak.find_element_by_id(keycloak_config.password_id).send_keys(password)
    keycloak.find_element_by_id(keycloak_config.login_id).click()


@pytest.fixture()
def keycloak_adm_login(selenium: webdriver.Chrome, keycloak_config: SimpleNamespace):
    selenium.get(keycloak_config.url)
    wait_for_class(selenium, keycloak_config.admin_console_class)
    assert selenium.title == keycloak_config.title
    keycloak = selenium

    def _func(
        username: str,
        password: str,
        fails_with: str = "",
        new_password: str = "",
        new_password_confirm: str = "",
    ) -> bool:
        admin_console = wait_for_class(keycloak, keycloak_config.admin_console_class)[0]
        admin_console.find_element_by_tag_name("a").click()
        _keycloak_login(keycloak, keycloak_config, username, password)
        # check password change
        if new_password:
            new_password_confirm = new_password_confirm if new_password_confirm else new_password
            _keycloak_password_change(keycloak, keycloak_config, password, new_password, new_password_confirm)
            if fails_with:
                error = keycloak.find_element_by_css_selector(f"span[class='{keycloak_config.password_update_feedback_class}']")
                assert fails_with == error.text
                assert error.is_displayed()
                return True
        # login succeeded
        else:
            if fails_with:
                error = keycloak.find_element_by_id(keycloak_config.input_error_id)
                assert fails_with == error.text
                assert error.is_displayed()
                return True
        # check that we are logged in
        wait_for_class(keycloak, keycloak_config.realm_selector_class)
        return True

    return _func


@pytest.fixture()
def domain_admins_dn(ucr: ConfigRegistry) -> str:
    return f"cn={custom_groupname('Domain Admins')},cn=groups,{ucr['ldap/base']}"
