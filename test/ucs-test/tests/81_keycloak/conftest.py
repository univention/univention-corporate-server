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

import os
from types import SimpleNamespace
from typing import Optional

import pytest
from selenium import webdriver
from utils import get_portal_tile, keycloak_login, keycloak_password_change, wait_for_class, wait_for_id

import univention.testing.udm as udm_test
from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.config_registry import ConfigRegistry
from univention.lib.misc import custom_groupname
from univention.testing.utils import get_ldap_connection, wait_for_listener_replication


@pytest.fixture()
def keycloak_secret() -> Optional[str]:
    secret_file = "/etc/keycloak.secret"
    password = None
    if os.path.isfile(secret_file):
        with open(secret_file) as fd:
            password = fd.read().strip()
    return password


@pytest.fixture()
def keycloak_admin() -> str:
    return "admin"


@pytest.fixture()
def keycloak_settings() -> dict:
    apps_cache = Apps()
    settings = {}
    candidate = apps_cache.find("keycloak", latest=True)
    configure = get_action('configure')
    for setting in configure.list_config(candidate):
        settings[setting["name"]] = setting["value"]
    return settings


@pytest.fixture()
def change_app_setting():
    apps_cache = Apps()
    app = apps_cache.find("keycloak", latest=True)
    configure = get_action('configure')
    settings = configure.list_config(app)
    revert_changes = {}

    def _func(app_id: str, changes: dict, revert: bool = True) -> None:
        known_settings = {x.get("name"): x.get("value") for x in settings}
        for change in changes:
            if change in known_settings:
                if revert:
                    revert_changes[change] = known_settings[change]
            else:
                raise Exception(f"Unknown setting: {change}")
        configure.call(app=app, set_vars=changes)

    yield _func

    if revert_changes:
        configure.call(app=app, set_vars=revert_changes)


@pytest.fixture()
def unverified_user() -> dict:
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user()
        ldap = get_ldap_connection(primary=True)
        changes = [
            ("objectClass", [""], ldap.get(dn).get("objectClass") + [b"univentionPasswordSelfService"]),
            ("univentionPasswordSelfServiceEmail", [""], [b"root@localhost"]),
            ("univentionPasswordRecoveryEmailVerified", [""], [b"FALSE"]),
            ("univentionRegisteredThroughSelfService", [""], [b"TRUE"]),
        ]
        ldap.modify(dn, changes)
        wait_for_listener_replication()
        yield SimpleNamespace(**{"username": username, "dn": dn, "password": "univention"})


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
        "portal_sidenavigation_username_class": "portal-sidenavigation--username",
        "logout_msg_de": "Abmelden",
        "logout_button_id": "loginButton",
    }

    return SimpleNamespace(**config)


@pytest.fixture()
def keycloak_config(ucr: ConfigRegistry) -> SimpleNamespace:
    url = f"https://ucs-sso-ng.{ucr['domainname']}"
    config = {
        "url": url,
        "token_url": f"{url}/realms/master/protocol/openid-connect/token",
        "users_url": f"{url}/admin/realms/ucs/users",
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
        "password_update_failed_msg": "Update password failed",
        "password_already_used_msg": "Changing password failed. The password was already used.",
        "password_too_short_msg": "Changing password failed. The password is too short.",
        "password_confirm_error_msg": "Passwords don't match.",
        "password_confirm_error_id": "input-error-password-confirm",
        "password_input_error_id": "input-error-password",
        "password_input_error_msg": "Please specify password.",
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
    print(driver.page_source)
    driver.quit()


@pytest.fixture()
def portal_login_via_keycloak(selenium: webdriver.Chrome, portal_config: SimpleNamespace, keycloak_config: SimpleNamespace):

    def _func(
        username: str,
        password: str,
        fails_with: Optional[str] = None,
        new_password: Optional[str] = None,
        new_password_confirm: Optional[str] = None,
        verify_login: Optional[bool] = True,
        url: Optional[str] = portal_config.url,
    ) -> webdriver.Chrome:
        selenium.get(url)
        wait_for_id(selenium, portal_config.categories_id)
        assert selenium.title == portal_config.title
        get_portal_tile(selenium, portal_config.sso_login_tile_de, portal_config).click()
        # login
        keycloak_login(selenium, keycloak_config, username, password, fails_with=fails_with if not new_password else None)
        # check password change
        if new_password:
            new_password_confirm = new_password_confirm if new_password_confirm else new_password
            keycloak_password_change(selenium, keycloak_config, password, new_password, new_password_confirm, fails_with=fails_with)
        if fails_with:
            return selenium
        # check that we are logged in
        if verify_login:
            wait_for_id(selenium, portal_config.header_menu_id)
        return selenium

    return _func


@pytest.fixture()
def keycloak_adm_login(selenium: webdriver.Chrome, keycloak_config: SimpleNamespace):

    def _func(
        username: str,
        password: str,
        fails_with: Optional[str] = None,
        url: Optional[str] = keycloak_config.url,
    ) -> webdriver.Chrome:
        selenium.get(url)
        wait_for_class(selenium, keycloak_config.admin_console_class)
        assert selenium.title == keycloak_config.title
        admin_console = wait_for_class(selenium, keycloak_config.admin_console_class)[0]
        admin_console.find_element_by_tag_name("a").click()
        keycloak_login(selenium, keycloak_config, username, password, fails_with=fails_with)
        if fails_with:
            return selenium
        # check that we are logged in
        wait_for_class(selenium, keycloak_config.realm_selector_class)
        return selenium

    return _func


@pytest.fixture()
def domain_admins_dn(ucr: ConfigRegistry) -> str:
    return f"cn={custom_groupname('Domain Admins')},cn=groups,{ucr['ldap/base']}"
