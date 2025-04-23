# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2025 Univention GmbH
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

import locale
import subprocess
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Page, expect
from requests_kerberos import OPTIONAL, HTTPKerberosAuth

from univention.testing.utils import wait_for_listener_replication_and_postrun


if TYPE_CHECKING:
    from types import SimpleNamespace

    from keycloak import KeycloakAdmin


TRANSLATIONS = {
    'de-DE': {
        'Username': 'Benutzername',
        'Password': 'Passwort',
        'Username or email': 'Benutzername oder E-Mail',
        'password': 'Passwort',
        'Sign In': 'Anmelden',
        'The authentication has failed, please login again.': 'Authentisierung ist fehlgeschlagen. Bitte melden Sie sich erneut an.',
        'Login (Single sign-on)': 'Anmelden (Single Sign-on)',
        'Changing password failed. The password was already used.': 'Passwort ändern fehlgeschlagen. Das Passwort wurde bereits genutzt.',
        'Changing password failed. The password is too short.': 'Passwort ändern fehlgeschlagen. Das Passwort ist zu kurz.',
        'Changing password failed. The password is too short. The password must consist of at least 8 characters.': 'Passwort ändern fehlgeschlagen. Das Passwort ist zu kurz. Das Passwort muss mindestens 8 Zeichen lang sein.',
        'Changing password failed. The password was already used. Choose a password which does not match any of your last 3 passwords.': 'Passwort ändern fehlgeschlagen. Das Passwort wurde bereits genutzt. Wählen Sie ein Passwort, dass nicht den letzten 3 Passwörtern entspricht.',
        "Passwords don't match.": 'Passwörter sind nicht identisch.',
        'Please specify password.': 'Bitte geben Sie ein Passwort ein.',
        'LOGOUT': 'ABMELDEN',
        'Unexpected error when handling authentication request to identity provider.': 'Unerwarteter Fehler während der Bearbeitung der Anfrage an den Identity Provider.',
        'The account has expired.': 'Das Benutzerkonto ist abgelaufen.',
        'The account is disabled.': 'Das Benutzerkonto ist deaktiviert.',
        'en-US text': 'de-DE text',
        'en-US title': 'de-DE title',
        'ACCEPT': 'ANNEHMEN',
        'Accept': 'Annehmen',
        'en yada yada yada': 'de yada yada yada',
        'Your account is not verified.': 'Konto nicht verifiziert.',
        'Access forbidden.': 'Zugriff verboten.',
        'Menu': 'Menü',
        'Login': 'Anmelden',
    },
}


def host_is_alive(host: str) -> bool:
    command = ['ping', '-c', '2', host]
    return subprocess.call(command) == 0


def get_portal_tile(page: Page, text: str, portal_config: SimpleNamespace):
    return page.get_by_label(_(text))


def get_language_code() -> str:
    return locale.getlocale()[0].replace('_', '-')


def keycloak_password_change(
    page: Page,
    keycloak_config: SimpleNamespace,
    username: str,
    password: str,
    new_password: str,
    new_password_confirm: str,
    fails_with: str | None = None,
) -> None:
    page.locator(f"#{keycloak_config.password_id}").fill(password)
    page.locator(f"#{keycloak_config.password_new_id}").fill(new_password)
    page.locator(f"#{keycloak_config.password_confirm_id}").fill(new_password_confirm)
    page.locator(f"#{keycloak_config.password_change_button_id}").click()

    if fails_with:
        error = page.locator(keycloak_config.password_update_error_css_selector.replace("[class='", ".").replace("']", "").replace(" ", "."))
        assert _(fails_with) == error.inner_text(), f'{fails_with} != {error.inner_text()}'
        return

    wait_for_listener_replication_and_postrun()
    if (page.get_by_label(_("Username or email")).is_visible()):
        keycloak_login(page=page, username=username, password=new_password, keycloak_config=keycloak_config)


def keycloak_auth_header(config: SimpleNamespace) -> dict:
    response = requests.post(config.master_token_url, data=config.login_data)
    assert response.status_code == 200, response.text
    return {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {response.json()['access_token']}",
    }


def keycloak_post_request(config: SimpleNamespace, path: str, params: dict | None = None) -> dict:
    response = requests.post(f'{config.admin_url}/{path}', headers=keycloak_auth_header(config), params=params)
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_get_request(config: SimpleNamespace, path: str, params: dict | None = None) -> dict:
    response = requests.get(f'{config.admin_url}/{path}', headers=keycloak_auth_header(config), params=params)
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_sessions(config: SimpleNamespace) -> dict:
    response = requests.get(config.client_session_stats_url, headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_sessions_by_user(config: SimpleNamespace, username: str) -> dict:
    params = {'search': username}
    response = requests.get(config.users_url, params=params, headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    user_object = {}
    for user in response.json():
        if user['attributes']['uid'][0] == username:
            user_object = user
    assert user_object, f'user {username} not found in keycloak'
    response = requests.get(f"{config.users_url}/{user_object['id']}/sessions", headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    return response.json()


def _(string: str) -> str:
    lc = get_language_code()
    if lc in TRANSLATIONS:
        return TRANSLATIONS[lc].get(string, string)
    else:
        return string


def keycloak_delete_session(config: SimpleNamespace, session_id: str) -> None:
    url = f'{config.sessions_url}/{session_id}'
    response = requests.delete(url, headers=keycloak_auth_header(config))
    assert response.status_code == 204, response.text


def grant_oidc_privileges(page: Page) -> None:
    if "oidc" in page.url:
        try:
            accept = page.get_by_role("button", name="Yes")
            expect(accept, "button accept to grant privileges not visible").to_be_visible()
            accept.click()
        except AssertionError:
            pass


def portal_logout(page: Page, portal_config: SimpleNamespace) -> None:
    page.click(f"[id={portal_config.header_menu_id}]")
    page.click(f"[id={portal_config.logout_button_id}]")


def keycloak_login(
    page: Page,
    keycloak_config: SimpleNamespace,
    username: str,
    password: str,
    fails_with: str | None = None,
    no_login: bool = False,
) -> None:
    try:
        name = page.get_by_label(_("Username or email"))
        expect(name, "login form username input not visible").to_be_visible()
        pw = page.get_by_label(_("Password"), exact=True)
        expect(pw, "password form input not visible").to_be_visible()
        if no_login:
            return
        name.fill(username)
        pw.fill(password)
        page.get_by_role("button", name=_("Sign In")).click()
        if fails_with:
            error = page.locator(keycloak_config.login_error_css_selector)
            assert _(fails_with) == error.inner_text(), f'{_(fails_with)} == {error.inner_text()}'
            assert error.is_visible()

    except Exception:
        print(page.content())
        raise


def run_command(cmd: list) -> str:
    print(f'execute {cmd}')
    return subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')


def kerberos_auth(portal_login_via_keycloak, ucr, protocol, portal_config):
    if protocol == 'oidc':
        # login with playwright to get rid of the oidc grant
        # privileges dialog, i don't get it to work with requests
        #   soup = BeautifulSoup(page.content, features='lxml')
        #   uri = soup.find('form', {'class': 'form-actions'}).attrs['action']
        #   code = soup.find('input', {'name': 'code'}).attrs['value']
        #   data = {'code': code, 'accept': 'Yes'}
        #   page = session.post(f'https://ucs-sso-ng.ucs.test/{uri}', data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
        page = portal_login_via_keycloak('Administrator', 'univention', protocol='oidc')
        portal_logout(page, portal_config)
        page.close()

    ucr.handler_set(['kerberos/defaults/rdns=false'])
    subprocess.call(['kdestroy'])
    subprocess.check_call(['kinit', '--password-file=/var/lib/ucs-test/pwdfile', 'Administrator'])
    session = requests.Session()
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

    headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
    url = f'https://{portal_config.fqdn}/univention/saml/' if protocol == 'saml' else f'https://{portal_config.fqdn}/univention/oidc/'
    page = session.get(url, data=None, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
    assert page.status_code == 200

    if protocol == 'saml':
        soup = BeautifulSoup(page.content, features='lxml')
        saml_resp = soup.find('input', {'name': 'SAMLResponse'}).attrs['value']
        relay_state = soup.find('input', {'name': 'RelayState'}).attrs['value']
        uri = soup.find('form', {'name': 'saml-post-binding'}).attrs['action']
        print(f'Got URI: {uri}')
        print(f'Got SAMLResponse: {saml_resp}')
        print(f'Got RelayState: {relay_state}')
        assert saml_resp
        data = {'SAMLResponse': saml_resp, 'RelayState': relay_state}
        page = session.post(uri, data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
        assert page.status_code == 200

    cookies = session.cookies.get_dict()
    assert cookies['UMCUsername'] == 'Administrator'
    assert 'UMCSessionId' in cookies
    assert 'AUTH_SESSION_ID' in cookies
    assert 'KEYCLOAK_IDENTITY' in cookies


def legacy_auth_config_remove(session: KeycloakAdmin, groups: dict) -> None:
    """
    groups = {
        "umcaccess": "https://master.ucs.test/univention/saml/metadata",
        "testclientaccess": "testclient",
    }
    """
    auth_role_name = 'univentionClientAccess'
    ldap_provider_name = 'ldap-provider'
    group_mapper_name = 'group-mapper'

    # remove role from clients
    for client in session.get_clients():
        for role in session.get_client_roles(client['id']):
            if role['name'] == auth_role_name:
                session.delete_client_role(client['id'], role['name'])

    # remove groups
    for group in session.get_groups():
        if group['name'] in groups.keys():
            session.delete_group(group['id'])

    # remove group-mapper
    ldap_provider_id = session.get_components(query={'name': ldap_provider_name, 'type': 'org.keycloak.storage.UserStorageProvider'})[0]['id']
    mapper = session.get_components(query={'parent': ldap_provider_id, 'name': group_mapper_name, 'type': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper'})
    if mapper:
        session.delete_component(mapper[0]['id'])


def legacy_auth_config_create(session: KeycloakAdmin, ldap_base: str, groups: dict) -> None:
    """
    groups = {
        "umcaccess": "https://master.ucs.test/univention/saml/metadata",
        "testclientaccess": "testclient",
    }
    """
    auth_role_name = 'univentionClientAccess'
    ldap_provider_name = 'ldap-provider'
    group_mapper_name = 'group-mapper'

    # get/check clients
    clients = {x['clientId']: x['id'] for x in session.get_clients()}
    for client in groups.values():
        if client not in clients:
            raise Exception(f'client {client} not found')

    # create group mapper
    ldap_provider_id = session.get_components(query={'name': ldap_provider_name, 'type': 'org.keycloak.storage.UserStorageProvider'})[0]['id']
    mapper = session.get_components(query={'parent': ldap_provider_id, 'name': group_mapper_name, 'type': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper'})
    if mapper:
        raise Exception(f'group mapper {group_mapper_name} already exists')
    else:
        group_names = list(groups.keys())
        ldap_filter = f'(cn={group_names[0]})' if len(group_names) == 1 else f"(|(cn={')(cn='.join(group_names)}))"
        payload = {
            'name': group_mapper_name,
            'providerId': 'group-ldap-mapper',
            'providerType': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
            'parentId': ldap_provider_id,
            'config': {
                'membership.attribute.type': ['UID'],
                'group.name.ldap.attribute': ['cn'],
                'preserve.group.inheritance': ['false'],
                'membership.user.ldap.attribute': ['uid'],
                'groups.dn': [ldap_base],
                'mode': ['READ_ONLY'],
                'user.roles.retrieve.strategy': ['LOAD_GROUPS_BY_MEMBER_ATTRIBUTE'],
                'groups.ldap.filter': [ldap_filter],
                'membership.ldap.attribute': ['memberUid'],
                'ignore.missing.groups': ['true'],
                'memberof.ldap.attribute': ['memberOf'],
                'group.object.classes': ['univentionGroup'],
                'groups.path': ['/'],
                'drop.non.existing.groups.during.sync': ['true'],
            },
        }
        session.create_component(payload)

    # update groups
    mapper_id = session.get_components(
        query={
            'parent': ldap_provider_id,
            'name': group_mapper_name,
            'type': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper',
        },
    )[0]['id']
    # python-keycloak uses urljoin to join the base url and the path for raw requests
    # but urljoin eats up the path portions of the first argument and we lose the keycloak path
    #   urljoin("https://srv/auth1", "/auth2") -> 'https://srv/auth2'
    # so we have to carry the keycloak path over and add it to raw requests ourself
    url = f'/admin/realms/ucs/user-storage/{ldap_provider_id}/mappers/{mapper_id}/sync?direction=fedToKeycloak'
    if session.path:
        url = f'{session.path}/{url}'
    res = session.raw_post(url, data={})
    if res.status_code != 200:
        raise Exception(f'raw POST to {url} failed: {res}')

    # add client role to each client
    roles = {}
    for client in groups.values():
        client_id = clients[client]
        session.create_client_role(client_id, {'name': auth_role_name}, skip_exists=True)
        role = next(x for x in session.get_client_roles(client_id) if x['name'] == auth_role_name)
        roles[client_id] = role['id']

    # add group role mapping
    keycloak_groups = {x['name']: x['id'] for x in session.get_groups()}
    for group in groups.keys():
        if group not in keycloak_groups:
            raise Exception(f'group {group} not found in keycloak')
        group_id = keycloak_groups[group]
        client_id = clients[groups[group]]
        role_id = roles[client_id]
        payload = {
            'id': role_id,
            'name': auth_role_name,
        }
        session.assign_group_client_roles(group_id, client_id, payload)
