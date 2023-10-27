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

from __future__ import annotations

import subprocess
import time
from types import SimpleNamespace

import requests
from keycloak import KeycloakAdmin
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def host_is_alive(host: str) -> bool:
    command = ['ping', '-c', '2', host]
    return subprocess.call(command) == 0


def wait_for(driver: WebDriver, by: By, element: str, timeout: int = 30) -> None:
    element_present = EC.presence_of_element_located((by, element))
    WebDriverWait(driver, timeout).until(element_present)
    WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, element)))
    time.sleep(1)


def wait_for_id(driver: WebDriver, element_id: str, timeout: int = 30) -> WebElement:
    wait_for(driver, By.ID, element_id, timeout)
    return driver.find_element(By.ID, element_id)


def wait_for_class(driver: WebDriver, element_class: str, timeout: int = 30) -> WebElement:
    wait_for(driver, By.CLASS_NAME, element_class, timeout)
    return driver.find_elements(By.CLASS_NAME, element_class)


def get_portal_tile(driver: WebDriver, text: str, portal_config: SimpleNamespace) -> WebElement:
    lang = get_language(driver)
    text = text[lang]
    for tile in driver.find_elements(By.CLASS_NAME, portal_config.tile_name_class):
        if tile.text == text:
            return tile


def get_language(driver: WebDriver, german: bool = False) -> str:
    if german:
        # TODO since chromium 119 l10n stuff does no longer work, all
        # keycloak site are german, no matter what locale settings
        # check at some point if we can revert this workaround
        return 'de-DE'
    lang = driver.execute_script('return window.navigator.userLanguage || window.navigator.language')
    return lang


def keycloak_password_change(
    driver: WebDriver,
    keycloak_config: SimpleNamespace,
    password: str,
    new_password: str,
    new_password_confirm: str,
    fails_with: dict | None = None,
) -> None:
    wait_for_id(driver, keycloak_config.kc_passwd_update_form_id)
    driver.find_element(By.ID, keycloak_config.password_id).send_keys(password)
    driver.find_element(By.ID, keycloak_config.password_new_id).send_keys(new_password)
    driver.find_element(By.ID, keycloak_config.password_confirm_id).send_keys(new_password_confirm)
    driver.find_element(By.ID, keycloak_config.password_change_button_id).click()
    if fails_with:
        lang = get_language(driver, german=True)
        fails_with = fails_with[lang]
        error = driver.find_element(By.CSS_SELECTOR, keycloak_config.password_update_error_css_selector)
        assert fails_with in error.text, f'{fails_with} != {error.text}'
        assert error.is_displayed()


def keycloak_auth_header(config: SimpleNamespace) -> dict:
    response = requests.post(config.master_token_url, data=config.login_data)
    assert response.status_code == 200, response.text
    return {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {response.json()['access_token']}",
    }


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


def keycloak_login(
    driver: WebDriver,
    keycloak_config: SimpleNamespace,
    username: str,
    password: str,
    fails_with: dict | None = None,
    no_login: bool = False,
) -> None:
    wait_for_id(driver, keycloak_config.username_id)
    wait_for_id(driver, keycloak_config.password_id)
    wait_for_id(driver, keycloak_config.login_id)
    if no_login:
        return
    driver.find_element(By.ID, keycloak_config.username_id).send_keys(username)
    driver.find_element(By.ID, keycloak_config.password_id).send_keys(password)
    driver.find_element(By.ID, keycloak_config.login_id).click()
    lang = get_language(driver, german=True)
    if fails_with:
        fails_with = fails_with[lang]
        error = driver.find_element(By.CSS_SELECTOR, keycloak_config.login_error_css_selector)
        assert fails_with == error.text, f'{fails_with} != {error.text}'
        assert error.is_displayed()


def run_command(cmd: list) -> str:
    return subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')


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
