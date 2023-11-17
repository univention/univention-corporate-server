#!/usr/share/ucs-test/runner python3
## desc: Tests the Self Service Translations
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service

import importlib
import os
import sys
import time

import pytest
from selenium.common.exceptions import ElementClickInterceptedException
from test_self_service import self_service_user

from univention.testing.strings import random_username


test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
try:
    test_lib = importlib.import_module(test_lib)
except ImportError:
    print(f'Could not import {test_lib}. Maybe set $UCS_TEST_LIB')
    sys.exit(1)


LINK_HASHES = ['profile', 'createaccount', 'verifyaccount', 'passwordchange', 'passwordforgotten', 'protectaccount', 'servicespecificpasswords']


def wait_for_loading(chrome):
    while True:
        time.sleep(0.5)
        element = chrome.find_first("div.standbyWrapper circle")
        if element:
            if element.is_displayed():
                continue
            break


def wait_for_element(chrome, css_selector, timeout=10):
    for _ in range(timeout * 10):
        element = chrome.find_first(css_selector)
        if element:
            return element
        time.sleep(0.1)
    raise Exception(f"Element {css_selector} not found")


def wait_for_input(chrome, input_name, timeout=10):
    return wait_for_element(chrome, f'[name={input_name}]', timeout)


def goto_selfservice(chrome, user=None):
    if user:
        chrome.get("/univention/login/?location=/univention/selfservice/")
        wait_for_input(chrome, 'username')
        chrome.enter_input('username', user.username)
        chrome.enter_input('password', user.password)
        chrome.enter_return()
    else:
        chrome.get('/univention/selfservice/')


def click(chrome, css_selector):
    for _ in range(9):
        try:
            wait_for_element(chrome, css_selector).click()
            return
        except ElementClickInterceptedException:
            time.sleep(0.1)
    chrome.find_first(css_selector).click()


def change_lang(chrome, lang, user=None):
    goto_selfservice(chrome, user)
    wait_for_element(chrome, 'button#header-button-menu').click()
    wait_for_element(chrome, "div.portal-sidenavigation__menu-item").click()
    element = wait_for_element(chrome, f"div#menu-item-language-{lang}")
    try:
        element.click()
    except ElementClickInterceptedException:
        pass


def process_labels(lables_to_check, labels):
    lables_to_check_d = {}
    for label in lables_to_check:
        label_name = label.get_attribute('for').split('--')[0]
        value = label.text.splitlines()
        if label_name not in labels or len(value) == 0:
            continue
        if label_name != "":
            lables_to_check_d[label_name] = value[0]
        else:
            lables_to_check_d.setdefault(label_name, []).append(value[0])
    return lables_to_check_d


def get_labels(chrome, labels):
    for _ in range(10):
        lables_to_check = chrome.find_all('label')
        lables_to_check = process_labels(lables_to_check, labels)
        print(lables_to_check)
        if len(lables_to_check) >= len(labels):
            break
        time.sleep(0.1)
    return lables_to_check


@pytest.fixture(autouse=True)
def activate_self_service(ucr_module):
    ucr_module.handler_set(
        [
            "umc/self-service/account-registration/backend/enabled=true",
            "umc/self-service/account-registration/frontend/enabled=true",
            "umc/self-service/account-verification/backend/enabled=true",
            "umc/self-service/account-verification/frontend/enabled=true",
            "umc/self-service/passwordchange/frontend/enabled=true",
            "umc/self-service/passwordreset/backend/enabled=true",
            "umc/self-service/profiledata/enabled=true",
            "umc/self-service/protect-account/backend/enabled=true",
            "umc/self-service/service-specific-passwords/backend/enabled=true",
        ],
    )


@pytest.mark.parametrize('lang, hash, labels', [
    ('en-US', 'profile', {'username': 'Username', 'password': 'Password'}),
    ('de-DE', 'profile', {'username': 'Benutzername', 'password': 'Passwort'}),
    ('en-US', 'createaccount', {'PasswordRecoveryEmail': 'Email', 'password': 'Password (retype)', 'firstname': 'First name', 'lastname': 'Last name', 'username': 'User name'}),
    ('de-DE', 'createaccount', {'PasswordRecoveryEmail': 'E-Mail', 'password': 'Passwort (Wiederholung)', 'firstname': 'Vorname', 'lastname': 'Nachname', 'username': 'Benutzername'}),
    ('en-US', 'verifyaccount', {'username': 'Username', 'token': 'Token'}),
    ('de-DE', 'verifyaccount', {'username': 'Benutzername', 'token': 'Token'}),
    ('en-US', 'passwordchange', {'oldPassword': 'Old password', 'newPassword': 'New password', 'newPasswordRetype': 'New password (retype)'}),
    ('de-DE', 'passwordchange', {'oldPassword': 'Altes Passwort', 'newPassword': 'Neues Passwort', 'newPasswordRetype': 'Neues Passwort (Wiederholung)'}),
    ('en-US', 'passwordforgotten', {'username': 'Username'}),
    ('de-DE', 'passwordforgotten', {'username': 'Benutzername'}),
    ('en-US', 'protectaccount', {'username': 'Username', 'password': 'Password'}),
    ('de-DE', 'protectaccount', {'username': 'Benutzername', 'password': 'Passwort'}),
    ('en-US', 'servicespecificpasswords', {'username': 'Username', 'password': 'Password'}),
    ('de-DE', 'servicespecificpasswords', {'username': 'Benutzername', 'password': 'Passwort'}),
])
def test_frontend_translations(chrome, lang, hash, labels):
    chrome.driver.implicitly_wait(10)
    change_lang(chrome, lang)
    chrome.driver.execute_script("localStorage.clear();")
    chrome.get(f'/univention/selfservice/#/selfservice/{hash}')
    chrome.driver.refresh()
    wait_for_element(chrome, 'label')

    lables_to_check = get_labels(chrome, labels)
    for label_name, expected_value in labels.items():
        assert label_name in lables_to_check, f'Label {label_name} is not in {list(lables_to_check.keys())}'
        if isinstance(expected_value, list):
            for value in expected_value:
                assert value in lables_to_check[label_name], f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {value}'
        else:
            assert lables_to_check[label_name] == expected_value, f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {expected_value}'


@pytest.mark.parametrize('lang, hash, labels', [
    ('en-US', 'profile', {"jpegPhoto": 'Your picture', "e-mail": 'E-mail address', "phone": 'Telephone number', "departmentNumber": 'Department number', "country": 'Country', "homeTelephoneNumber": 'Private telephone number', "mobileTelephoneNumber": 'Mobile phone number', "homePostalAddress": 'Private postal address', "": ['Street', 'Postal code', 'City']}),
    ('de-DE', 'profile', {"jpegPhoto": 'Ihr Foto', "e-mail": 'E-Mail-Adresse', "phone": 'Telefonnummer', "departmentNumber": 'Abteilungsnummer', "country": 'Land', "homeTelephoneNumber": 'Telefonnummer Festnetz', "mobileTelephoneNumber": 'Telefonnummer Mobil', "homePostalAddress": 'Private Adresse', "": ['Straße', 'Postleitzahl', 'Stadt']}),
    ('en-US', 'verifyaccount', {'username': 'Username', 'token': 'Token'}),
    ('de-DE', 'verifyaccount', {'username': 'Benutzername', 'token': 'Token'}),
    ('en-US', 'passwordchange', {'oldPassword': 'Old password', 'newPassword': 'New password', 'newPasswordRetype': 'New password (retype)'}),
    ('de-DE', 'passwordchange', {'oldPassword': 'Altes Passwort', 'newPassword': 'Neues Passwort', 'newPasswordRetype': 'Neues Passwort (Wiederholung)'}),
    ('en-US', 'passwordforgotten', {'username': 'Username'}),
    ('de-DE', 'passwordforgotten', {'username': 'Benutzername'}),
    ('en-US', 'protectaccount', {'username': 'Username', 'password': 'Password'}),
    ('de-DE', 'protectaccount', {'username': 'Benutzername', 'password': 'Passwort'}),
    ('en-US', 'servicespecificpasswords', {'username': 'Username', 'password': 'Password'}),
    ('de-DE', 'servicespecificpasswords', {'username': 'Benutzername', 'password': 'Passwort'}),
])
def test_frontend_login_translations(chrome, lang, hash, labels):
    chrome.driver.implicitly_wait(10)
    reset_mail_address = f'{random_username()}@{random_username()}'
    with self_service_user(mailPrimaryAddress=reset_mail_address, language="en-US") as user:
        change_lang(chrome, lang, user=user)
        chrome.driver.execute_script("localStorage.clear();")
        chrome.get(f'/univention/selfservice/#/selfservice/{hash}')
        chrome.driver.refresh()
        wait_for_element(chrome, 'label')

        lables_to_check = get_labels(chrome, labels)

        for label_name, expected_value in labels.items():
            assert label_name in lables_to_check, f'Label {label_name} is not in {list(lables_to_check.keys())}'
            if isinstance(expected_value, list):
                for value in expected_value:
                    assert value in lables_to_check[label_name], f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {value}'
            else:
                assert lables_to_check[label_name] == expected_value, f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {expected_value}'


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
