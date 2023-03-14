#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test portal keycloak self service features
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages: [univention-self-service]

from bs4 import BeautifulSoup
from utils import wait_for_id


def test_login_denied_if_not_verified(keycloak_settings, portal_login_via_keycloak, unverified_user, portal_config):
    assert keycloak_settings["ucs/self/registration/check_email_verification"] is True
    driver = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = driver.find_element_by_css_selector("label[class='pf-c-form__label pf-c-form__label-text']")
    error_msg = BeautifulSoup(error.text, "lxml").text.replace("\n", " ")
    expected_msg = BeautifulSoup(keycloak_settings["keycloak/login/messages/en/accountNotVerifiedMsg"], "lxml").text.replace("\n", " ")
    assert expected_msg == error_msg
    # verify
    unverified_user.verify()
    # try again
    driver.find_element_by_css_selector("input[class='pf-c-button pf-m-primary pf-m-block btn-lg']").click()
    wait_for_id(driver, portal_config.header_menu_id)


def test_verified_msg(change_app_setting, unverified_user, portal_login_via_keycloak, keycloak_settings):
    assert keycloak_settings["ucs/self/registration/check_email_verification"] is True
    settings = {
        "keycloak/login/messages/en/accountNotVerifiedMsg": "en yada yada yada",
        "keycloak/login/messages/de/accountNotVerifiedMsg": "de yada yada yada",
    }
    change_app_setting("keycloak", settings)
    driver = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = driver.find_element_by_css_selector("label[class='pf-c-form__label pf-c-form__label-text']")
    error_msg = BeautifulSoup(error.text, "lxml").text.replace("\n", " ")
    assert error_msg == "en yada yada yada"
    driver.find_element_by_css_selector("input[class='pf-c-button pf-m-primary pf-m-block btn-lg']")
