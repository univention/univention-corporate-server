#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os
import shutil
import tempfile
from itertools import product
from subprocess import CalledProcessError

import pytest
import requests
from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.by import By
from utils import run_command, wait_for_class, wait_for_id


LINK_COUNT = 12


def test_get_webresources(keycloak_config):
    resources = [
        "/univention/theme.css",
        "/univention/login/css/custom.css",
        "/favicon.ico",
        "/univention/meta.json",
        "/univention/js/dijit/themes/umc/images/login_logo.svg",
    ]
    for resource in resources:
        resp = requests.get(f"{keycloak_config.url}/{resource}")
        assert resp.status_code == 200


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.parametrize("settings", [
    ["dark", "rgba(255, 255, 255, 1)"],
    ["light", "rgba(30, 30, 29, 1)"]],
    ids=["dark", "light"],
)
def test_theme_switch(ucr, keycloak_adm_login, admin_account, settings):
    theme = settings[0]
    color = settings[1]
    ucr.handler_set([f"ucs/web/theme={theme}"])
    driver = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    element = wait_for_class(driver, "login-pf-header")
    assert element[0].value_of_css_property("color") == color


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
def test_custom_theme(keycloak_adm_login, admin_account):
    custom_css = "/var/www/univention/login/css/custom.css"
    driver = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    element = wait_for_class(driver, "card-pf")
    assert element[0].value_of_css_property("background-color") == "rgba(30, 30, 29, 1)"
    with tempfile.NamedTemporaryFile(dir='/tmp', delete=False) as tmpfile:
        temp_file = tmpfile.name
    shutil.move(custom_css, temp_file)
    try:
        with open(custom_css, "w") as fh:
            fh.write(":root { --bgc-content-container: #831414; }")
        driver = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
        element = wait_for_class(driver, "card-pf")
        assert element[0].value_of_css_property("background-color") == "rgba(131, 20, 20, 1)"
    finally:
        shutil.move(temp_file, custom_css)


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
def test_cookie_banner(keycloak_adm_login, admin_account, ucr, keycloak_config):
    ucr.handler_set([
        "umc/cookie-banner/cookie=TESTCOOKIE",
        "umc/cookie-banner/show=true",
        "umc/cookie-banner/text/de=deutcher text",
        "umc/cookie-banner/title/de=deutscher titel",
        "umc/cookie-banner/text/en=english text",
        "umc/cookie-banner/title/en=english title",
    ])
    # check that the login does not work
    with pytest.raises(ElementClickInterceptedException):
        keycloak_adm_login(admin_account.username, admin_account.bindpw)
    # check the popup
    driver = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    assert wait_for_id(driver, "cookie-text").text == "english text"
    assert wait_for_id(driver, "cookie-title").text == "english title"
    button = wait_for_class(driver, "cookie-banner-button")
    # accept the popup and check the cookie
    assert button[0].text == "ACCEPT"
    button[0].click()
    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie["name"] == "TESTCOOKIE":
            if cookie["value"] == "do-not-change-me":
                # ...
                break
    else:
        raise Exception(f"cookie TESTCOOKIE not found: {cookies}")
    # just to test if this is interactable")
    driver.find_element(By.ID, keycloak_config.login_id).click()


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.parametrize("lang, link_count", [(lang, count) for lang, count in product(["en"], [0, LINK_COUNT + 1])])
def test_invalid_link_count(lang: str, link_count: int):
    with pytest.raises(CalledProcessError):
        run_command(["univention-keycloak", "login-links", "set", lang, str(link_count), "href", "desc"])


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails without keycloak locally installed")
@pytest.mark.parametrize("lang, link_count", [(lang, count) for lang, count in product(["en"], [1, 5, 12])])
def test_login_links(lang, link_count, login_links, portal_login_via_keycloak, admin_account):
    driver = portal_login_via_keycloak(admin_account.username, admin_account.bindpw, no_login=True)
    login_links_parent = wait_for_id(driver, "umcLoginLinks")
    links_found = login_links_parent.find_elements_by_tag_name("a")
    assert link_count == len(links_found)
    for link in links_found:
        try:
            link.click()
        except WebDriverException:
            pytest.fail(f"{link.text} is not clickable")
