#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keycloak ad hoc federation
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

from __future__ import annotations

import base64
import os
import time
import uuid
from typing import TYPE_CHECKING

import pytest
from ad_hoc import AdHocProvisioning
from playwright.sync_api import Page, expect
from utils import get_portal_tile

from univention.udm import UDM


if TYPE_CHECKING:
    from types import SimpleNamespace

    from keycloak import KeycloakAdmin

    from univention.config_registry.backend import ConfigRegistry
    from univention.udm.modules.users_user import UsersUserObject


def _test_sso_login(page, portal_config: SimpleNamespace, keycloak_config: SimpleNamespace) -> None:
    page.goto(portal_config.url)
    expect(page).to_have_title(portal_config.title)

    get_portal_tile(page, portal_config.sso_oidc_login_tile, portal_config).click()
    page.click("[id='social-oidc-test']")
    _keycloak_login_dummy_realm(page, keycloak_config, 'test_user1', 'univention')
    page.click(f"[id='{portal_config.header_menu_id}']")
    page.click("[id='loginButton']")
    assert get_portal_tile(page, portal_config.sso_login_tile_de, portal_config)


def get_udm_user_obj(username: str) -> UsersUserObject | None:
    udm_users = UDM.admin().version(2).get('users/user')
    user = list(udm_users.search(f'uid={username}'))
    if len(user) == 1:
        return user[0]
    else:
        return None


def _test_federated_user(keycloak_admin_connection: KeycloakAdmin, remote_uuid: uuid) -> None:
    udm_user = get_udm_user_obj('external-oidc-test-test_user1')
    assert udm_user
    assert udm_user.props.username == 'external-oidc-test-test_user1'
    assert udm_user.props.lastname == 'User'
    assert udm_user.props.firstname == 'Test'
    assert udm_user.props.description == 'Shadow copy of user'
    assert udm_user.props.univentionObjectIdentifier == str(remote_uuid)
    assert udm_user.props.univentionSourceIAM == 'Federation from test'
    kc_user_id = keycloak_admin_connection.get_user_id(username='external-oidc-test-test_user1')
    kc_user = keycloak_admin_connection.get_user(user_id=kc_user_id)
    assert kc_user['username'] == 'external-oidc-test-test_user1'
    assert kc_user['email'] == 'test_user1@adhoc.test'
    assert kc_user['firstName'] == 'Test'
    assert kc_user['lastName'] == 'User'


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_adhoc_federation(keycloak_admin_connection: KeycloakAdmin, keycloak_admin: str, keycloak_secret: str, ucr: ConfigRegistry, tracing_page: Page, keycloak_config: SimpleNamespace, portal_config: SimpleNamespace):

    ad_hoc_provisioning = AdHocProvisioning(
        keycloak_url=keycloak_config.url,
        admin_username=keycloak_admin,
        admin_password=keycloak_secret,
        udm_url=keycloak_config.udm_endpoint,
        udm_username="Administrator",
        udm_password="univention",
        existing_realm="ucs",
        dummy_realm="test",
        path=keycloak_config.path,
    )
    try:
        ad_hoc_provisioning.setup()
        # create dummy users
        user_uuid = uuid.uuid4()
        uuid_remote = base64.b64encode(user_uuid.bytes_le).decode("utf-8")
        ad_hoc_provisioning.kc_dummy.create_user(ad_hoc_provisioning._get_test_user_payload('test_user1', 'univention', uuid_remote=uuid_remote))
        # do some tests
        keycloak_admin_connection.realm_name = 'ucs'
        _test_sso_login(tracing_page, portal_config, keycloak_config)
        _test_federated_user(keycloak_admin_connection, user_uuid)
    finally:
        udm_user = get_udm_user_obj('external-oidc-test-test_user1')
        if udm_user:
            udm_user.delete()
        keycloak_admin_connection.realm_name = 'ucs'
        time.sleep(10)
        kc_user_id = keycloak_admin_connection.get_user_id(username='external-oidc-test-test_user1')
        if kc_user_id:
            keycloak_admin_connection.delete_user(kc_user_id)
        ad_hoc_provisioning.cleanup()


# This is a copy of keycloak_login from utils.py
# The dummy realm is configured to be in English, so it cause problems with the utils functions
def _keycloak_login_dummy_realm(
    page: Page,
    keycloak_config: SimpleNamespace,
    username: str,
    password: str,
    fails_with: str | None = None,
    no_login: bool = False,
) -> None:
    try:
        name = page.get_by_label("Username or email")
        expect(name, "login form username input not visible").to_be_visible()
        pw = page.get_by_label("Password", exact=True)
        expect(pw, "password form input not visible").to_be_visible()
        if no_login:
            return
        name.fill(username)
        pw.fill(password)
        page.get_by_role("button", name="Sign In").click()
        if fails_with:
            error = page.locator(keycloak_config.login_error_css_selector)
            assert fails_with == error.inner_text(), f'{fails_with} == {error.inner_text()}'
            assert error.is_visible()

    except Exception:
        print(page.content())
        raise
