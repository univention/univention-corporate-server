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


def goto_selfservice(chrome, user=None):
    if user:
        chrome.get("/univention/login/?location=/univention/selfservice/")
        time.sleep(2)
        chrome.enter_input('username', user.username)
        chrome.enter_input('password', user.password)
        chrome.enter_return()
        time.sleep(10)
    else:
        chrome.get('/univention/selfservice/')
        time.sleep(2)


def change_lang(chrome, lang, user=None):
    goto_selfservice(chrome, user)
    chrome.find_first('button#header-button-menu').click()
    time.sleep(0.5)
    chrome.find_first("div.portal-sidenavigation__menu-item").click()
    time.sleep(0.5)
    element = chrome.find_first(f"div#menu-item-language-{lang}")
    try:
        element.click()
        time.sleep(0.5)
    except Exception:
        pass


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
def test_frontend_translations(chrome, ucr, lang, hash, labels):
    ucr.set({
        'umc/self-service/protect-account/backend/enabled': 'true',
        'umc/self-service/passwordreset/backend/enabled': 'true',
        'umc/self-service/passwordchange/frontend/enabled': 'true',
        'umc/self-service/profiledata/enabled': 'true',
        'umc/self-service/account-registration/backend/enabled': 'true',
        'umc/self-service/account-registration/frontend/enabled': 'true',
        'umc/self-service/account-verification/backend/enabled': 'true',
        'umc/self-service/account-verification/frontend/enabled': 'true',
        'umc/self-service/service-specific-passwords/backend/enabled': 'true',
    })

    change_lang(chrome, lang)
    chrome.driver.execute_script("localStorage.clear();")
    chrome.get(f'/univention/selfservice/#/selfservice/{hash}')
    time.sleep(0.5)
    chrome.driver.refresh()
    time.sleep(2)
    lables_to_check = chrome.find_all('label')
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

    lables_to_check = lables_to_check_d
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
def test_frontend_login_translations(chrome, ucr, lang, hash, labels):
    ucr.set({
        'umc/self-service/protect-account/backend/enabled': 'true',
        'umc/self-service/passwordreset/backend/enabled': 'true',
        'umc/self-service/passwordchange/frontend/enabled': 'true',
        'umc/self-service/profiledata/enabled': 'true',
        'umc/self-service/account-registration/backend/enabled': 'true',
        'umc/self-service/account-registration/frontend/enabled': 'true',
        'umc/self-service/account-verification/backend/enabled': 'true',
        'umc/self-service/account-verification/frontend/enabled': 'true',
        'umc/self-service/service-specific-passwords/backend/enabled': 'true',
    })
    reset_mail_address = f'{random_username()}@{random_username()}'
    with self_service_user(mailPrimaryAddress=reset_mail_address, language="en-US") as user:
        change_lang(chrome, lang, user=user)
        chrome.driver.execute_script("localStorage.clear();")
        chrome.get(f'/univention/selfservice/#/selfservice/{hash}')
        time.sleep(0.5)
        chrome.driver.refresh()
        time.sleep(2)
        lables_to_check = chrome.find_all('label')

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

        lables_to_check = lables_to_check_d
        for label_name, expected_value in labels.items():
            assert label_name in lables_to_check, f'Label {label_name} is not in {list(lables_to_check.keys())}'
            if isinstance(expected_value, list):
                for value in expected_value:
                    assert value in lables_to_check[label_name], f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {value}'
            else:
                assert lables_to_check[label_name] == expected_value, f'Label {label_name} has wrong value: {lables_to_check[label_name]} instead of {expected_value}'


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
