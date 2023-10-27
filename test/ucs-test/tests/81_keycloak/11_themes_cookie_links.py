#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
# desc: Test univention-keycloak
# tags: [keycloak]
# roles: [domaincontroller_master, domaincontroller_backup]
# exposure: dangerous

import os
import shutil
import socket
import tempfile
from itertools import product
from subprocess import CalledProcessError
from typing import Tuple

import pytest
import requests
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from utils import run_command, wait_for_class, wait_for_id


LINK_COUNT = 12


@pytest.fixture(autouse=True)
def check_i_am_keycloak(request, keycloak_config, ucr):
    if request.node.get_closest_marker("check_i_am_keycloak"):
        keycloak_ip = socket.gethostbyname(keycloak_config.server)
        my_ip = socket.gethostbyname(ucr["hostname"])
        if keycloak_ip != my_ip:
            pytest.skip(
                "this system is not the keycloak server, test makes no sense here")


@pytest.fixture()
def login_links(lang: str, link_count: int) -> Tuple[str, int]:
    try:
        for i in range(1, link_count + 1):
            run_command(["univention-keycloak", "login-links",
                        "set", lang, str(i), f"href{i}", f"desc{i}"])
        yield lang, link_count
    finally:
        for i in range(1, link_count + 1):
            try:
                run_command(["univention-keycloak", "login-links",
                            "delete", lang, str(i)])
            except CalledProcessError:
                pass


def test_get_webresources(keycloak_config):
    resources = [
        "/univention/theme.css",
        "/univention/login/css/custom.css",
        "/favicon.ico",
        "/univention/meta.json",
        "/univention/js/dijit/themes/umc/images/login_logo.svg",
    ]
    for resource in resources:
        url = f"https://{keycloak_config.server}/{resource}"
        resp = requests.get(url)
        assert resp.status_code == 200, f"{resp.status_code} {url}"


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
@pytest.mark.parametrize("settings", [
    ["dark", "rgba(255, 255, 255, 1)"],
    ["light", "rgba(30, 30, 29, 1)"]],
    ids=["dark", "light"],
)
def test_theme_switch(ucr, keycloak_adm_login, admin_account, settings):
    theme = settings[0]
    color = settings[1]
    ucr.handler_set([f"ucs/web/theme={theme}"])
    driver = keycloak_adm_login(
        admin_account.username, admin_account.bindpw, no_login=True)
    element = wait_for_class(driver, "login-pf-header")
    assert element[0].value_of_css_property("color") == color


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
def test_custom_theme(keycloak_adm_login, admin_account):
    custom_css = "/var/www/univention/login/css/custom.css"
    color_css = "rgba(131, 20, 20, 1)"
    with tempfile.NamedTemporaryFile(dir='/tmp', delete=False) as tmpfile:
        temp_file = tmpfile.name
    shutil.move(custom_css, temp_file)
    try:
        with open(custom_css, "w") as fh:
            fh.write(":root { --bgc-content-body: #831414; }")
        driver = keycloak_adm_login(
            admin_account.username, admin_account.bindpw, no_login=True)
        element = wait_for_id(driver, "username")
        assert element.value_of_css_property("background-color") == color_css
    finally:
        shutil.move(temp_file, custom_css)


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
def test_cookie_banner(keycloak_adm_login, admin_account, ucr, keycloak_config):
    ucr.handler_set([
        "umc/cookie-banner/cookie=TESTCOOKIE",
        "umc/cookie-banner/show=true",
        "umc/cookie-banner/text/de=de-DE text",
        "umc/cookie-banner/title/de=de-DE title",
        "umc/cookie-banner/text/en=en-US text",
        "umc/cookie-banner/title/en=en-US title",
    ])
    # check that the login does not work
    with pytest.raises(ElementClickInterceptedException):
        keycloak_adm_login(admin_account.username, admin_account.bindpw)
    # check the popup
    driver = keycloak_adm_login(
        admin_account.username, admin_account.bindpw, no_login=True)
    lang = driver.execute_script(
        "return window.navigator.userLanguage || window.navigator.language")
    assert wait_for_id(driver, "cookie-text").text == f"{lang} text"
    assert wait_for_id(driver, "cookie-title").text == f"{lang} title"
    button = wait_for_class(driver, "cookie-banner-button")
    # accept the popup and check the cookie
    assert button[0].text == "ACCEPT" if lang == 'en-US' else "AKZEPTIEREN"
    button[0].click()
    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie["name"] == "TESTCOOKIE":
            assert cookie["value"] == "do-not-change-me"
            assert cookie["domain"] == keycloak_config.server.lower()
            break
    else:
        raise Exception(f"cookie TESTCOOKIE not found: {cookies}")
    # just to test if this is interactable")
    driver.find_element(By.ID, keycloak_config.login_id).click()


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
def test_cookie_banner_no_banner_with_cookie_domains(keycloak_adm_login, admin_account, ucr):
    # no banner if umc/cookie-banner/domains does not match
    # the current domain
    ucr.handler_set([
        "umc/cookie-banner/cookie=TESTCOOKIE",
        "umc/cookie-banner/show=true",
        "umc/cookie-banner/text/de=de-DE text",
        "umc/cookie-banner/title/de=de-DE title",
        "umc/cookie-banner/text/en=en-US text",
        "umc/cookie-banner/title/en=en-US title",
        "umc/cookie-banner/domains=does.not.exists",
    ])
    keycloak_adm_login(admin_account.username, admin_account.bindpw)


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
def test_cookie_banner_domains(keycloak_adm_login, admin_account, ucr, keycloak_config):
    # check if cookie domain is set to umc/cookie-banner/domains
    domain = keycloak_config.server.split(".", 1)[1]
    ucr.handler_set([
        "umc/cookie-banner/cookie=TESTCOOKIE",
        "umc/cookie-banner/show=true",
        "umc/cookie-banner/text/de=de-DE text",
        "umc/cookie-banner/title/de=de-DE title",
        "umc/cookie-banner/text/en=en-US text",
        "umc/cookie-banner/title/en=en-US title",
        f"umc/cookie-banner/domains=does.not.exist,{domain.lower()}",
    ])
    driver = keycloak_adm_login(
        admin_account.username, admin_account.bindpw, no_login=True)
    button = wait_for_class(driver, "cookie-banner-button")
    button[0].click()
    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie["name"] == "TESTCOOKIE":
            assert cookie["domain"] == f".{domain.lower()}"
            break
    else:
        raise Exception(f"cookie TESTCOOKIE not found: {cookies}")


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.check_i_am_keycloak()
def test_login_page_with_cookie_banner_no_element_is_tabbable(keycloak_adm_login, admin_account, ucr):
    # only the accept button is tabbable
    ucr.handler_set([
        "umc/cookie-banner/cookie=TESTCOOKIE",
        "umc/cookie-banner/show=true",
        "umc/cookie-banner/text/de=de-DE text",
        "umc/cookie-banner/title/de=de-DE title",
        "umc/cookie-banner/text/en=en-US text",
        "umc/cookie-banner/title/en=en-US title",
    ])
    driver = keycloak_adm_login(
        admin_account.username, admin_account.bindpw, no_login=True)
    lang = driver.execute_script(
        "return window.navigator.userLanguage || window.navigator.language")
    button = wait_for_class(driver, "cookie-banner-button")
    assert button[0].text == "ACCEPT" if lang == 'en-US' else "ANNEHMEN"
    assert driver.switch_to.active_element.is_displayed
    # some browser fields
    ActionChains(driver).send_keys(Keys.TAB).perform()
    ActionChains(driver).send_keys(Keys.TAB).perform()
    ActionChains(driver).send_keys(Keys.TAB).perform()
    ActionChains(driver).send_keys(Keys.TAB).perform()
    # and back to the beginning
    button = wait_for_class(driver, "cookie-banner-button")
    assert button[0].text == "ACCEPT" if lang == 'en-US' else "ANNEHMEN"


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
def test_login_page_all_elements_are_tabbable(portal_login_via_keycloak, keycloak_adm_login, admin_account):
    driver = portal_login_via_keycloak(
        admin_account.username, admin_account.bindpw, no_login=True)
    assert driver.switch_to.active_element.get_attribute("name") == "username"
    assert driver.switch_to.active_element.is_displayed
    ActionChains(driver).send_keys(Keys.TAB).perform()
    assert driver.switch_to.active_element.get_attribute("name") == "password"
    assert driver.switch_to.active_element.is_displayed
    ActionChains(driver).send_keys(Keys.TAB).perform()
    assert driver.switch_to.active_element.get_attribute("name") == "login"
    assert driver.switch_to.active_element.is_displayed
    # some browser fields
    ActionChains(driver).send_keys(Keys.TAB).perform()
    ActionChains(driver).send_keys(Keys.TAB).perform()
    lang = driver.execute_script(
        "return window.navigator.userLanguage || window.navigator.language")
    assert driver.switch_to.active_element.text == "English" if lang == 'en-US' else "Deutsch"
    assert driver.switch_to.active_element.is_displayed
    ActionChains(driver).send_keys(Keys.TAB).perform()
    assert driver.switch_to.active_element.text == "Deutsch" if lang == 'en-US' else "English"
    assert driver.switch_to.active_element.is_displayed
    # and back to the beginning
    ActionChains(driver).send_keys(Keys.TAB).perform()
    ActionChains(driver).send_keys(Keys.TAB).perform()
    assert driver.switch_to.active_element.get_attribute("name") == "username"


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.parametrize("lang, link_count", list(product(["en"], [0, LINK_COUNT + 1])))
def test_invalid_link_count(lang: str, link_count: int):
    with pytest.raises(CalledProcessError):
        run_command(["univention-keycloak", "login-links", "set",
                    lang, str(link_count), "href", "desc"])


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.parametrize("lang, link_count", list(product(["en"], [1, 5, 12])))
def test_login_links(lang, link_count, login_links, portal_login_via_keycloak, admin_account):
    driver = portal_login_via_keycloak(
        admin_account.username, admin_account.bindpw, no_login=True)
    login_links_parent = wait_for_id(driver, "umcLoginLinks")
    links_found = login_links_parent.find_elements(By.TAG_NAME, "a")
    assert link_count == len(links_found)
    for link in links_found:
        assert link.text.startswith("href")
        assert link.is_displayed()
