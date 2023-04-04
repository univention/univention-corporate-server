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

import subprocess
import time
from types import SimpleNamespace
from typing import Optional

import requests
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def host_is_alive(host: str) -> bool:
    command = ["ping", "-c", "2", host]
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
    for tile in driver.find_elements(By.CLASS_NAME, portal_config.tile_name_class):
        if tile.text == text:
            return tile


def keycloak_password_change(
    driver: WebDriver,
    keycloak_config: SimpleNamespace,
    password: str,
    new_password: str,
    new_password_confirm: str,
    fails_with: Optional[str] = None,
) -> None:
    wait_for_id(driver, keycloak_config.kc_passwd_update_form_id)
    driver.find_element(By.ID, keycloak_config.password_id).send_keys(password)
    driver.find_element(By.ID, keycloak_config.password_new_id).send_keys(new_password)
    driver.find_element(By.ID, keycloak_config.password_confirm_id).send_keys(new_password_confirm)
    driver.find_element(By.ID, keycloak_config.password_change_button_id).click()
    if fails_with:
        error = driver.find_element(By.CSS_SELECTOR, keycloak_config.password_update_error_css_selector)
        assert fails_with == error.text, f"{fails_with} != {error.text}"
        assert error.is_displayed()


def keycloak_auth_header(config: SimpleNamespace) -> dict:
    response = requests.post(config.token_url, data=config.login_data)
    assert response.status_code == 200, response.text
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


def keycloak_get_request(config: SimpleNamespace, path: str, params: dict = None) -> dict:
    response = requests.get(f"{config.admin_url}/{path}", headers=keycloak_auth_header(config), params=params)
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_sessions(config: SimpleNamespace) -> dict:
    response = requests.get(config.client_session_stats_url, headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_sessions_by_user(config: SimpleNamespace, username: str) -> dict:
    params = {"search": username}
    response = requests.get(config.users_url, params=params, headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    user_object = {}
    for user in response.json():
        if user["attributes"]["uid"][0] == username:
            user_object = user
    assert user_object, f"user {username} not found in keycloak"
    response = requests.get(f"{config.users_url}/{user_object['id']}/sessions", headers=keycloak_auth_header(config))
    assert response.status_code == 200, response.text
    return response.json()


def keycloak_login(
    driver: WebDriver,
    keycloak_config: SimpleNamespace,
    username: str,
    password: str,
    fails_with: Optional[str] = None,
) -> None:
    wait_for_id(driver, keycloak_config.username_id)
    wait_for_id(driver, keycloak_config.password_id)
    wait_for_id(driver, keycloak_config.login_id)
    driver.find_element(By.ID, keycloak_config.username_id).send_keys(username)
    driver.find_element(By.ID, keycloak_config.password_id).send_keys(password)
    driver.find_element(By.ID, keycloak_config.login_id).click()
    if fails_with:
        error = driver.find_element(By.CSS_SELECTOR, keycloak_config.login_error_css_selector)
        assert fails_with == error.text, f"{fails_with} != {error.text}"
        assert error.is_displayed()


def run_command(cmd: list) -> str:
    return subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
