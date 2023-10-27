#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test portal keycloak self service features
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages: [univention-self-service]

from selenium.webdriver.common.by import By
from utils import wait_for_class, wait_for_id


def test_login_denied_if_not_verified(keycloak_settings, portal_login_via_keycloak, unverified_user, portal_config, keycloak_config):
    assert keycloak_settings["ucs/self/registration/check_email_verification"] is True
    driver = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = wait_for_class(driver, "ucs-p")[0]
    error_msg = error.get_attribute("innerHTML")
    expected_msg = keycloak_settings["keycloak/login/messages/de/accountNotVerifiedMsg"].replace("/>", ">").encode('unicode-escape').replace(b'\\\\u', b'\\u').decode('unicode-escape')
    assert expected_msg == error_msg
    # verify
    unverified_user.verify()
    # try again
    driver.find_element(By.CSS_SELECTOR, "input[class='pf-c-button pf-m-primary pf-m-block btn-lg']").click()
    # verify that we are in the portal now
    wait_for_id(driver, portal_config.header_menu_id)


def test_verified_msg(change_app_setting, unverified_user, portal_login_via_keycloak, keycloak_settings):
    assert keycloak_settings["ucs/self/registration/check_email_verification"] is True
    settings = {
        "keycloak/login/messages/en/accountNotVerifiedMsg": "en yada yada yada",
        "keycloak/login/messages/de/accountNotVerifiedMsg": "de yada yada yada",
    }
    change_app_setting("keycloak", settings)
    driver = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = wait_for_class(driver, "ucs-p")[0]
    error_msg = error.get_attribute("innerHTML")
    lang = driver.execute_script("return window.navigator.userLanguage || window.navigator.language")
    assert error_msg == settings["keycloak/login/messages/de/accountNotVerifiedMsg"] if lang == 'de-DE' else settings["keycloak/login/messages/en/accountNotVerifiedMsg"]
    driver.find_element(By.CSS_SELECTOR, "input[class='pf-c-button pf-m-primary pf-m-block btn-lg']")
