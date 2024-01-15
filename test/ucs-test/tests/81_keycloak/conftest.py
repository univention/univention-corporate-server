# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Callable, Iterator

import pytest
from keycloak import KeycloakAdmin, KeycloakOpenID
from selenium import webdriver
from selenium.webdriver.common.by import By
from utils import (
    get_portal_tile, keycloak_login, keycloak_password_change, legacy_auth_config_create, legacy_auth_config_remove,
    run_command, wait_for_class, wait_for_id,
)

from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.config_registry import ConfigRegistry
from univention.lib.misc import custom_groupname
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import UCSTestDomainAdminCredentials, get_ldap_connection, wait_for_listener_replication
from univention.udm import UDM
from univention.udm.binary_props import Base64Bzip2BinaryProperty
from univention.udm.modules.settings_data import SettingsDataObject


# don't use the ucs-test ucr fixture (UCSTestConfigRegistry)
# in fixtures, this can lean to problems if system settings
# are reverted after the test, e.g. appcenter/apps/$id/container
# after univention-app reinitialize
@pytest.fixture(scope='session')
def ucr_proper() -> ConfigRegistry:
    ucr = ConfigRegistry()
    return ucr.load()


@pytest.fixture()
def admin_account() -> UCSTestDomainAdminCredentials:
    return UCSTestDomainAdminCredentials()


@pytest.fixture()
def keycloak_secret() -> str | None:
    secret_file = '/etc/keycloak.secret'
    password = None
    if os.path.isfile(secret_file):
        with open(secret_file) as fd:
            password = fd.read().strip()
    return password


@pytest.fixture()
def keycloak_admin() -> str:
    return 'admin'


@pytest.fixture()
def keycloak_settings() -> dict:
    apps_cache = Apps()
    settings = {}
    candidate = apps_cache.find('keycloak', latest=True)
    configure = get_action('configure')
    for setting in configure.list_config(candidate):
        settings[setting['name']] = setting['value']
    return settings


@pytest.fixture()
def keycloak_app_version() -> str:
    apps_cache = Apps()
    version = [app.version for app in apps_cache.get_all_locally_installed_apps() if app.id == 'keycloak']
    return version[0]


@pytest.fixture()
def change_app_setting():
    data = {'app': None, 'configure': None, 'changes': {}}

    def _func(app_id: str, changes: dict, revert: bool = True) -> None:
        apps_cache = Apps()
        app = apps_cache.find(app_id, latest=True)
        data['app'] = app
        configure = get_action('configure')
        data['configure'] = configure
        settings = configure.list_config(app)
        known_settings = {x.get('name'): x.get('value') for x in settings}
        for change in changes:
            if change in known_settings:
                if revert:
                    data['changes'][change] = known_settings[change]
            else:
                raise Exception(f'Unknown setting: {change}')
        configure.call(app=app, set_vars=changes)

    yield _func

    if data['changes']:
        data['configure'].call(app=data['app'], set_vars=data['changes'])


@pytest.fixture()
def upgrade_status_obj(ucr_proper) -> SettingsDataObject:
    udm = UDM.admin().version(2)
    mod = udm.get('settings/data')
    obj = mod.get(f"cn=keycloak,cn=data,cn=univention,{ucr_proper.get('ldap/base')}")
    orig_value = obj.props.data.raw

    yield obj

    obj.props.data = Base64Bzip2BinaryProperty('data', raw_value=orig_value)
    obj.save()


class UnverfiedUser(object):
    def __init__(self, udm: UCSTestUDM, password: str = 'univention'):
        self.ldap = get_ldap_connection(primary=True)
        self.password = password
        self.dn, self.username = udm.create_user(password=password)
        changes = [
            ('objectClass', [b''], self.ldap.get(self.dn).get('objectClass') + [b'univentionPasswordSelfService']),
            ('univentionPasswordSelfServiceEmail', [''], [b'root@localhost']),
            ('univentionPasswordRecoveryEmailVerified', [''], [b'FALSE']),
            ('univentionRegisteredThroughSelfService', [''], [b'TRUE']),
        ]
        self.ldap.modify(self.dn, changes)
        wait_for_listener_replication()

    def verify(self) -> None:
        # verify
        changes = [
            ('univentionPasswordRecoveryEmailVerified', [b''], [b'TRUE']),
        ]
        self.ldap.modify(self.dn, changes)
        wait_for_listener_replication()


@pytest.fixture()
def unverified_user() -> Iterator[UnverfiedUser]:
    with UCSTestUDM() as udm:
        user = UnverfiedUser(udm)
        yield user


@pytest.fixture()
def portal_config(ucr_proper: ConfigRegistry) -> SimpleNamespace:
    portal_fqdn = ucr_proper['umc/saml/sp-server'] if ucr_proper['umc/saml/sp-server'] else f"{ucr_proper['hostname']}.{ucr_proper['domainname']}"
    config = {
        'url': f'https://{portal_fqdn}/univention/portal',
        'fqdn': portal_fqdn,
        'title': 'Univention Portal',
        'sso_login_tile': 'Login (Single sign-on)',
        'sso_login_tile_de': 'Anmelden (Single Sign-on)',
        'tile_name_class': 'portal-tile__name',
        'category_title_class': 'portal-category__title',
        'categories_id': 'portalCategories',
        'tile_class': 'portal-tile',
        'groups_tile': 'School groups',
        'users_tile': 'School users',
        'username': 'admin',
        'password': 'univention',
        'header_menu_id': 'header-button-menu',
        'portal_sidenavigation_username_class': 'portal-sidenavigation--username',
        'logout_msg': 'Logout',
        'logout_msg_de': 'Abmelden',
        'logout_button_id': 'loginButton',
    }

    return SimpleNamespace(**config)


@pytest.fixture()
def umc_config(ucr_proper: ConfigRegistry) -> SimpleNamespace:
    umc_fqdn = ucr_proper['umc/oauth/rp/server'] if ucr_proper['umc/oauth/rp/server'] else f"{ucr_proper['hostname']}.{ucr_proper['domainname']}"
    config = {
        'url': f'https://{umc_fqdn}/univention/oauth/?target_link_uri=/univention/management/',
        'fqdn': umc_fqdn,
        'title': 'Univention Portal',
        'username': 'admin',
        'password': 'univention',
    }

    return SimpleNamespace(**config)


@pytest.fixture()
def keycloak_config(ucr_proper: ConfigRegistry) -> SimpleNamespace:
    server = ucr_proper.get('keycloak/server/sso/fqdn', f"ucs-sso-ng.{ucr_proper['domainname']}")
    path = ucr_proper['keycloak/server/sso/path'] if ucr_proper['keycloak/server/sso/path'] else ''
    url = f'https://{server}{path}'
    config = {
        'server': server,
        'path': path,
        'url': url,
        'admin_url': f'{url}/admin',
        'token_url': f'{url}/realms/ucs/protocol/openid-connect/token',
        'master_token_url': f'{url}/realms/master/protocol/openid-connect/token',
        'users_url': f'{url}/admin/realms/ucs/users',
        'client_session_stats_url': f'{url}/admin/realms/ucs/client-session-stats',
        'logout_all_url': f'{url}/admin/realms/ucs/logout-all',
        'title': 'Welcome to Keycloak',
        'admin_console_class': 'welcome-primary-link',
        'main_content_page_container_id': 'kc-main-content-page-container',
        'login_data': {
            'client_id': 'admin-cli',
            'username': 'Administrator',
            'password': 'univention',
            'grant_type': 'password',
        },
        'logout_all_data': {'realm': 'ucs'},
        'login_id': 'kc-login',
        'username_id': 'username',
        'password_id': 'password',
        'login_error_css_selector': "span[class='pf-c-alert__title kc-feedback-text']",
        'password_update_error_css_selector': "span[class='pf-c-alert__title kc-feedback-text']",
        'wrong_password_msg': 'Invalid username or password.',
        'wrong_password_msg_de': 'Ungültiger Benutzername oder Passwort.',
        'kc_passwd_update_form_id': 'kc-passwd-update-form',
        'password_confirm_id': 'password-confirm',
        'password_new_id': 'password-new',
        'password_change_button_id': 'kc-form-buttons',
        'password_update_failed_msg': 'Update password failed',
        'kc_page_title_id': 'kc-page-title',
        'account_expired_msg': 'The account has expired.',
        'account_disabled_msg': 'The account is disabled.',
    }
    return SimpleNamespace(**config)


@pytest.fixture()
def selenium() -> webdriver.Chrome:
    """Browser based testing for using Selenium."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')  # chrome complains about being executed as root
    # do not use these two options, selenium will get stuck with
    # >      raise exception_class(message, screen, stacktrace)
    # E       selenium.common.exceptions.SessionNotCreatedException: Message: session not created
    # E       from timeout: Timed out receiving message from renderer: 600.000
    # E         (Session info: headless chrome=90.0.4430.212)
    # on UCS
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('ignore-certificate-errors')
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
        fails_with: str | None = None,
        new_password: str | None = None,
        new_password_confirm: str | None = None,
        verify_login: bool | None = True,
        url: str | None = portal_config.url,
        no_login: bool = False,
    ) -> webdriver.Chrome:
        selenium.get(url)
        wait_for_id(selenium, portal_config.categories_id)
        assert selenium.title == portal_config.title
        lang = selenium.execute_script('return window.navigator.userLanguage || window.navigator.language')
        sso_login_tile = portal_config.sso_login_tile if lang == 'en-US' else portal_config.sso_login_tile_de
        get_portal_tile(selenium, sso_login_tile, portal_config).click()
        # login
        keycloak_login(selenium, keycloak_config, username, password, fails_with=fails_with if not new_password else None, no_login=no_login)
        # check password change
        if new_password:
            new_password_confirm = new_password_confirm if new_password_confirm else new_password
            keycloak_password_change(selenium, keycloak_config, password, new_password, new_password_confirm, fails_with=fails_with)
        if fails_with or no_login:
            return selenium
        # check that we are logged in
        if verify_login:
            wait_for_id(selenium, portal_config.header_menu_id)
        return selenium

    return _func


@pytest.fixture()
def umc_login_via_keycloak(selenium: webdriver.Chrome, umc_config: SimpleNamespace, keycloak_config: SimpleNamespace):
    def _func(
        username: str,
        password: str,
        fails_with: str | None = None,
        new_password: str | None = None,
        new_password_confirm: str | None = None,
        verify_login: bool | None = True,
        url: str | None = umc_config.url,
        no_login: bool = False,
    ) -> webdriver.Chrome:
        selenium.get(url)
        keycloak_login(selenium, keycloak_config, username, password, fails_with=fails_with if not new_password else None, no_login=no_login)
        # check password change
        if new_password:
            new_password_confirm = new_password_confirm if new_password_confirm else new_password
            keycloak_password_change(selenium, keycloak_config, password, new_password, new_password_confirm, fails_with=fails_with)
        if fails_with or no_login:
            return selenium
        # check that we are logged in
        if verify_login:
            wait_for_id(selenium, 'umcTopContainer')  # TODO: it doesn't verfiy logged in status
        return selenium

    return _func


@pytest.fixture()
def keycloak_adm_login(selenium: webdriver.Chrome, keycloak_config: SimpleNamespace):
    def _func(
        username: str,
        password: str,
        fails_with: str | None = None,
        url: str | None = keycloak_config.url,
        no_login: bool = False,
    ) -> webdriver.Chrome:
        selenium.get(url)
        wait_for_class(selenium, keycloak_config.admin_console_class)
        assert selenium.title == keycloak_config.title
        admin_console = wait_for_class(selenium, keycloak_config.admin_console_class)[0]
        admin_console.find_element(By.TAG_NAME, 'a').click()
        keycloak_login(selenium, keycloak_config, username, password, fails_with=fails_with, no_login=no_login)
        if fails_with or no_login:
            return selenium
        # check that we are logged in
        wait_for_id(selenium, keycloak_config.main_content_page_container_id)
        return selenium

    return _func


@pytest.fixture()
def domain_admins_dn(ucr_proper: ConfigRegistry) -> str:
    return f"cn={custom_groupname('Domain Admins')},cn=groups,{ucr_proper['ldap/base']}"


@pytest.fixture()
def keycloak_session(keycloak_config: SimpleNamespace) -> Callable[[str, str], KeycloakAdmin]:
    def _session(username: str, password: str) -> KeycloakAdmin:
        session = KeycloakAdmin(
            server_url=keycloak_config.url,
            username=username,
            password=password,
            realm_name='ucs',
            user_realm_name='master',
            verify=True,
        )
        session.path = keycloak_config.path
        return session
    return _session


@pytest.fixture()
def keycloak_administrator_connection(keycloak_session: Callable, admin_account: UCSTestDomainAdminCredentials) -> KeycloakAdmin:
    return keycloak_session(admin_account.username, admin_account.bindpw)


@pytest.fixture()
def keycloak_admin_connection(
    keycloak_session: Callable,
    keycloak_admin: str,
    keycloak_secret: str,
) -> KeycloakAdmin:
    if keycloak_secret:
        return keycloak_session(keycloak_admin, keycloak_secret)


@pytest.fixture()
def keycloak_openid(keycloak_secret: str, keycloak_config: SimpleNamespace) -> KeycloakOpenID:
    def _session(client_id: str, realm_name: str = 'ucs', client_secret_key: str | None = None) -> KeycloakAdmin:
        return KeycloakOpenID(
            server_url=keycloak_config.url,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key or keycloak_secret,
        )
    return _session


@pytest.fixture()
def keycloak_openid_connection(keycloak_openid: Callable) -> KeycloakOpenID:
    return keycloak_openid('admin-cli')


@pytest.fixture()
def legacy_authorization_setup_saml(
    udm: UCSTestUDM,
    ucr: ConfigRegistry,
    keycloak_administrator_connection: KeycloakAdmin,
    admin_account: UCSTestDomainAdminCredentials,
    portal_config: SimpleNamespace,
) -> Iterator[SimpleNamespace]:
    group_dn, group_name = udm.create_group()
    user_dn, user_name = udm.create_user(password='univention')
    saml_client = f'https://{portal_config.fqdn}/univention/saml/metadata'
    groups = {group_name: saml_client}

    try:
        # create flow
        run_command(['univention-keycloak', 'legacy-authentication-flow', 'create'])
        # create config
        legacy_auth_config_create(keycloak_administrator_connection, ucr['ldap/base'], groups)
        # add flow to client
        run_command(['univention-keycloak', 'client-auth-flow', '--clientid', saml_client, '--auth-flow', 'browser flow with legacy app authorization'])
        yield SimpleNamespace(
            client=saml_client,
            group=group_name,
            group_dn=group_dn,
            user=user_name,
            user_dn=user_dn,
            password='univention',
        )
    finally:
        # cleanup
        run_command(['univention-keycloak', 'legacy-authentication-flow', 'delete'])
        legacy_auth_config_remove(keycloak_administrator_connection, groups)


@pytest.fixture()
def legacy_authorization_setup_oidc(
    udm: UCSTestUDM,
    ucr: ConfigRegistry,
    keycloak_administrator_connection: KeycloakAdmin,
    admin_account: UCSTestDomainAdminCredentials,
) -> Iterator[SimpleNamespace]:
    group_dn, group_name = udm.create_group()
    user_dn, user_name = udm.create_user(password='univention')
    client = f'testclient-{user_name}'
    client_secret = 'abc'
    groups = {group_name: client}

    try:
        # create flow
        run_command(['univention-keycloak', 'legacy-authentication-flow', 'create', '--flow', 'direct grant'])
        # create client and add custom direct grant flow
        run_command(['univention-keycloak', 'oidc/rp', 'create', client, '--client-secret', client_secret, '--app-url', 'https://*', '--direct-access-grants'])
        client_id = keycloak_administrator_connection.get_client_id(client)
        flow_id = next(
            flow['id'] for flow in keycloak_administrator_connection.get_authentication_flows() if flow.get('alias') == 'direct grant flow with legacy app authorization'
        )
        client_data = keycloak_administrator_connection.get_client(client_id)
        client_data['authenticationFlowBindingOverrides']['direct grant'] = flow_id
        client_data['authenticationFlowBindingOverrides']['direct_grant'] = flow_id
        keycloak_administrator_connection.update_client(client_id, client_data)
        # create config
        legacy_auth_config_create(keycloak_administrator_connection, ucr['ldap/base'], groups)
        yield SimpleNamespace(
            client=client,
            client_secret=client_secret,
            group=group_name,
            group_dn=group_dn,
            user=user_name,
            user_dn=user_dn,
            password='univention',
        )
    finally:
        # cleanup
        run_command(['univention-keycloak', 'legacy-authentication-flow', 'delete', '--flow', 'direct grant'])
        legacy_auth_config_remove(keycloak_administrator_connection, groups)
        keycloak_administrator_connection.delete_client(client_id)
