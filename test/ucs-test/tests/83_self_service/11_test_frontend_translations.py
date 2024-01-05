#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Tests the Self Service Translations
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service

import re
import time
from typing import Dict, Union

import pytest
from playwright.sync_api import Locator, Page, expect
from test_self_service import SelfServiceUser, do_create_user

from univention.testing.browser import logger
from univention.testing.browser.lib import UCSLanguage
from univention.testing.browser.selfservice import SelfService
from univention.testing.strings import random_username


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


@pytest.fixture(scope='module')
def self_service_user(udm_module_scope) -> SelfServiceUser:
    reset_mail_address = f'{random_username()}@{random_username()}'
    return do_create_user(udm_module_scope, mailPrimaryAddress=reset_mail_address, language='en-US')


def find_label(page: Page, label_display_text: str) -> Union[Locator, None]:
    label_display_locators = page.get_by_text(label_display_text).all()
    return next((label_display_locator for label_display_locator in label_display_locators if label_display_locator.evaluate('(element) => element.tagName') == 'LABEL'), None)


def check_labels(page: Page, labels: Dict[str, str]):
    for label_display, label_tag in labels.items():
        logger.info("checking for label with text %r and with attribute 'for=%r'", label_display, label_tag)
        found_label = find_label(page, label_display)
        assert found_label is not None, f'A label with the text {label_display} has not been found.'
        expect(found_label).to_be_visible()
        expect(found_label, f"Expected locator to have tag {label_tag}--\\d\\d, but found {found_label.get_attribute('for')}").to_have_attribute(
            'for', re.compile(rf'{label_tag}--\d\d')
        )


@pytest.mark.parametrize(
    'lang, hash, labels',
    [
        (UCSLanguage.EN_US, 'profile', {'Username': 'username', 'Password': 'password'}),
        (UCSLanguage.DE_DE, 'profile', {'Benutzername': 'username', 'Passwort': 'password'}),
        (
            UCSLanguage.EN_US,
            'createaccount',
            {'Email': 'PasswordRecoveryEmail', 'Password (retype)': 'password--retype', 'First name': 'firstname', 'Last name': 'lastname', 'User name': 'username'},
        ),
        (
            UCSLanguage.DE_DE,
            'createaccount',
            {'E-Mail': 'PasswordRecoveryEmail', 'Passwort (Wiederholung)': 'password--retype', 'Vorname': 'firstname', 'Nachname': 'lastname', 'Benutzername': 'username'},
        ),
        (UCSLanguage.EN_US, 'verifyaccount', {'Username': 'username', 'Token': 'token'}),
        (UCSLanguage.DE_DE, 'verifyaccount', {'Benutzername': 'username', 'Token': 'token'}),
        (UCSLanguage.EN_US, 'passwordchange', {'Old password': 'oldPassword', 'New password': 'newPassword', 'New password (retype)': 'newPasswordRetype'}),
        (UCSLanguage.DE_DE, 'passwordchange', {'Altes Passwort': 'oldPassword', 'Neues Passwort': 'newPassword', 'Neues Passwort (Wiederholung)': 'newPasswordRetype'}),
        (UCSLanguage.EN_US, 'passwordforgotten', {'Username': 'username'}),
        (UCSLanguage.DE_DE, 'passwordforgotten', {'Benutzername': 'username'}),
        (UCSLanguage.EN_US, 'protectaccount', {'Username': 'username', 'Password': 'password'}),
        (UCSLanguage.DE_DE, 'protectaccount', {'Benutzername': 'username', 'Passwort': 'password'}),
        (UCSLanguage.EN_US, 'servicespecificpasswords', {'Username': 'username', 'Password': 'password'}),
        (UCSLanguage.DE_DE, 'servicespecificpasswords', {'Benutzername': 'username', 'Passwort': 'password'}),
    ],
)
def test_frontend_translations(self_service: SelfService, lang: UCSLanguage, hash: str, labels: Dict[str, str]):
    page: Page = self_service.tester.page
    self_service.tester.set_language(lang)
    self_service.navigate(hash)
    time.sleep(1)

    check_labels(page, labels)


@pytest.mark.parametrize(
    'lang, hash, labels',
    [
        (
            UCSLanguage.EN_US,
            'profile',
            {
                'Your picture Y': 'jpegPhoto',
                'E-mail address E': 'e-mail',
                'Telephone number': 'phone',
                'Department number': 'departmentNumber',
                'Country': 'country',
                'Private telephone number': 'homeTelephoneNumber',
                'Mobile phone number': 'mobileTelephoneNumber',
                'Private postal address': 'homePostalAddress',
                'Street': '',
                'Postal code': '',
                'City': '',
            },
        ),
        (
            UCSLanguage.DE_DE,
            'profile',
            {
                'Ihr Foto I': 'jpegPhoto',
                'E-Mail-Adresse E': 'e-mail',
                'Telefonnummer': 'phone',
                'Abteilungsnummer': 'departmentNumber',
                'Land': 'country',
                'Telefonnummer Festnetz': 'homeTelephoneNumber',
                'Telefonnummer Mobil': 'mobileTelephoneNumber',
                'Private Adresse': 'homePostalAddress',
                'Straße': '',
                'Postleitzahl': '',
                'Stadt': '',
            },
        ),
        (UCSLanguage.EN_US, 'verifyaccount', {'Username': 'username', 'Token': 'token'}),
        (UCSLanguage.DE_DE, 'verifyaccount', {'Benutzername': 'username', 'Token': 'token'}),
        (UCSLanguage.EN_US, 'passwordchange', {'Old password': 'oldPassword', 'New password': 'newPassword', 'New password (retype)': 'newPasswordRetype'}),
        (UCSLanguage.DE_DE, 'passwordchange', {'Altes Passwort': 'oldPassword', 'Neues Passwort': 'newPassword', 'Neues Passwort (Wiederholung)': 'newPasswordRetype'}),
        (UCSLanguage.EN_US, 'passwordforgotten', {'Username': 'username'}),
        (UCSLanguage.DE_DE, 'passwordforgotten', {'Benutzername': 'username'}),
        (UCSLanguage.EN_US, 'protectaccount', {'Username': 'username', 'Password': 'password'}),
        (UCSLanguage.DE_DE, 'protectaccount', {'Benutzername': 'username', 'Passwort': 'password'}),
        (UCSLanguage.EN_US, 'servicespecificpasswords', {'Username': 'username', 'Password': 'password'}),
        (UCSLanguage.DE_DE, 'servicespecificpasswords', {'Benutzername': 'username', 'Passwort': 'password'}),
    ],
)
def test_frontend_login_translations(self_service: SelfService, lang: UCSLanguage, hash: str, labels: Dict[str, str], self_service_user):
    page: Page = self_service.tester.page
    self_service.tester.set_language(lang)
    self_service.navigate(hash, username=self_service_user.username, password=self_service_user.password)
    time.sleep(3)
    check_labels(page, labels)
