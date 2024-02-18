#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: test self registration
## tags: [apptest]
## packages:
##  - univention-self-service
##  - univention-self-service-master
##  - univention-self-service-passwordreset-umc
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

from __future__ import annotations

import email
import time
from typing import Dict
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect
from test_self_service import capture_mails

import univention.testing.strings as uts
from univention.admin.uexceptions import noObject
from univention.admin.uldap import getAdminConnection
from univention.lib.i18n import Translation
from univention.testing import utils
from univention.testing.browser.selfservice import SelfService, UserCreationAttribute


_ = Translation('ucs-test-browser').translate


MAILS_TIMEOUT = 5


@pytest.fixture()
def mails():
    with capture_mails(timeout=MAILS_TIMEOUT) as mails:
        yield mails


@pytest.fixture(autouse=True)
def activate_self_registration(ucr):
    ucr.handler_set(
        [
            'umc/self-service/account-registration/backend/enabled=true',
            'umc/self-service/account-registration/frontend/enabled=true',
            'umc/self-service/account-verification/backend/enabled=true',
            'umc/self-service/account-verification/frontend/enabled=true',
        ],
    )


@pytest.fixture()
def get_registration_info(ucr):
    class local:
        dns = []

    def _get_registration_info() -> Dict:
        container_dn = ucr.get('umc/self-service/account-registration/usercontainer')
        username = uts.random_name()
        attributes = {
            'username': UserCreationAttribute(_('User name'), username),
            'lastname': UserCreationAttribute(_('Last name'), username),
            'password': UserCreationAttribute(_('Password'), 'univention'),
            'PasswordRecoveryEmail': UserCreationAttribute(_('Email'), 'root@localhost'),
        }

        dn = f"uid={attributes['username'].value},{container_dn}"
        local.dns.append(dn)
        return {
            'dn': dn,
            'attributes': attributes,
            'data': {
                'attributes': attributes,
            },
        }

    yield _get_registration_info
    lo, _po = getAdminConnection()
    for dn in local.dns:
        try:
            lo.delete(dn)
        except noObject:
            pass


def _get_mail(mails, idx=-1):
    assert mails.data, f'No mails have been captured in {MAILS_TIMEOUT} seconds'
    assert idx < len(mails.data), f'Not enough mails have been captured to get mail of index: {idx}'
    mail = email.message_from_string(mails.data[idx].decode('utf-8'))
    body = mail.get_payload(decode=True).decode('utf-8')
    verification_links = [line for line in body.split() if line.startswith('https://')]

    auto_verify_link = verification_links[0] if len(verification_links) else ''
    verify_link = verification_links[1] if len(verification_links) else ''
    verify_fragment = urlparse(auto_verify_link).fragment
    verify_params = parse_qs(verify_fragment)
    return {
        'mail': mail,
        'body': body,
        'auto_verify_link': auto_verify_link,
        'verify_link': verify_link,
        'verify_data': {
            'username': verify_params.get('username', [''])[0],
            'token': verify_params.get('/selfservice/verifyaccount/?token', [''])[0],
            'method': verify_params.get('method', [''])[0],
        },
    }


def test_registration_enabled(self_service: SelfService, ucr, get_registration_info):
    ucr.handler_set(['umc/self-service/account-registration/frontend/enabled=false'])
    self_service.navigate()
    expect(self_service.page.get_by_text(_('Create an account'))).to_be_hidden()

    ucr.handler_set(
        [
            'umc/self-service/account-registration/frontend/enabled=true',
            'umc/self-service/account-registration/backend/enabled=false',
        ],
    )

    self_service.navigate('createaccount')
    expect(self_service.page.get_by_role('heading', name=_('Create an account'))).to_be_visible()
    info = get_registration_info()
    self_service.fill_create_account(info['attributes'])
    expect(self_service.page.get_by_text(_('The account registration was disabled via the Univention Configuration Registry.'))).to_be_visible()


def test_udm_attributes(self_service: SelfService, ucr):
    self_service.navigate_create_account()
    expected_visible = [
        self_service.page.get_by_role('textbox', name=_('Email')),
        self_service.page.get_by_role('textbox', name=_('Password'), exact=True),
        self_service.page.get_by_role('textbox', name=_('Password (retype)'), exact=True),
        self_service.page.get_by_role('textbox', name=_('First name')),
        self_service.page.get_by_role('textbox', name=_('Last name')),
        self_service.page.get_by_role('textbox', name=_('User name')),
    ]

    [expect(loc).to_be_visible() for loc in expected_visible]

    ucr.handler_set(['umc/self-service/account-registration/udm_attributes=description,title'])
    ucr.handler_set(['umc/self-service/account-registration/udm_attributes/required=title'])

    self_service.navigate_create_account()
    expected_visible = [
        self_service.page.get_by_role('textbox', name=_('Email')),
        self_service.page.get_by_role('textbox', name=_('Password'), exact=True),
        self_service.page.get_by_role('textbox', name=_('Password (retype)'), exact=True),
        self_service.page.get_by_role('textbox', name=_('Description')),
        self_service.page.get_by_role('textbox', name=_('Title')),
    ]

    [expect(loc).to_be_visible() for loc in expected_visible]


@pytest.mark.parametrize('verification_process', ['automatic', 'manual'])
def test_user_creation(self_service: SelfService, mails, get_registration_info, verification_process):
    info = create_account(self_service, get_registration_info)
    utils.verify_ldap_object(
        info['dn'],
        {'univentionRegisteredThroughSelfService': ['TRUE'], 'univentionPasswordRecoveryEmailVerified': ['FALSE']},
        retry_count=4,
        delay=2,
    )

    if verification_process == 'automatic':
        auto_verify(self_service, mails)
    elif verification_process == 'manual':
        manual_verify(self_service, mails)

    utils.verify_ldap_object(
        info['dn'],
        {
            'univentionRegisteredThroughSelfService': ['TRUE'],
            'univentionPasswordRecoveryEmailVerified': ['TRUE'],
        },
        retry_count=4,
        delay=2,
    )


def test_account_verfiyaccount_page_errors(self_service: SelfService, udm):
    self_service.navigate('verifyaccount')
    self_service.fill_create_account(
        {
            'username': UserCreationAttribute(_('Username'), 'not_existing'),
            'token': UserCreationAttribute(_('Token'), 'xxxx'),
        },
        _('Verify Account'),
    )

    expect(self_service.page.get_by_text(_('The account could not be verified. Please verify your input')))

    self_service.navigate('verifyaccount')
    self_service.fill_create_account(
        {
            'username': UserCreationAttribute(_('Username'), 'not_existing'),
        },
        _('Request new token'),
    )

    expect(self_service.page.get_by_text(_('The verification token could not be sent. Please verify your input.')))

    _dn, username = udm.create_user({'PasswordRecoveryEmail': None})
    self_service.navigate('verifyaccount')
    self_service.fill_create_account(
        {
            'username': UserCreationAttribute(_('Username'), username),
            'token': UserCreationAttribute(_('Token'), 'xxxx'),
        },
        _('Verify Account'),
    )

    expect(self_service.page.get_by_text(_('The token you supplied is either expired or invalid. Please request a new one.')))


def test_request_new_token(self_service: SelfService, mails, get_registration_info):
    create_account(self_service, get_registration_info)

    self_service.navigate('verifyaccount')
    self_service.fill_create_account(
        {
            'username': UserCreationAttribute(_('Username'), 'not_existing'),
        },
        _('Request new token'),
    )
    expect(self_service.page.get_by_text(_('Please follow the instructions in the email to verify your account')))

    self_service.page.reload()
    auto_verify(self_service, mails)
    expect(self_service.page.get_by_text(_('Your account has been successfully verified'))).to_be_visible()


def test_next_steps(self_service: SelfService, mails, ucr, get_registration_info):
    ucr.handler_set(['umc/self-service/account-verification/next-steps=Foo Bar'])

    create_account(self_service, get_registration_info)
    auto_verify(self_service, mails)


@pytest.mark.parametrize('change_email', [True, False])
def test_email_change(self_service: SelfService, mails, get_registration_info, change_email: bool):
    info = create_account(self_service, get_registration_info)
    auto_verify(self_service, mails)

    utils.verify_ldap_object(
        info['dn'],
        {
            'univentionRegisteredThroughSelfService': ['TRUE'],
            'univentionPasswordRecoveryEmailVerified': ['TRUE'],
        },
        retry_count=4,
        delay=2,
    )

    self_service.navigate('protectaccount')

    self_service.page.get_by_role('textbox', name=_('Username')).fill(info['attributes']['username'].value)
    time.sleep(1)
    self_service.page.get_by_role('textbox', name=_('Password')).fill(info['attributes']['password'].value)
    self_service.page.get_by_role('button', name=_('Next')).click()

    text = self_service.page.get_by_text(_('Your account recovery options have been updated.. Your account has to be verified again'))
    if change_email:
        new_email = 'foo@bar.com'
        self_service.page.get_by_role('textbox', name=_('Email'), exact=True).fill(new_email)
        self_service.page.get_by_role('textbox', name=_('Email (retype)'), exact=True).fill(new_email)

        self_service.page.get_by_role('button', name=_('Submit'), exact=True).click()
        expect(text).to_be_visible()
    else:
        self_service.page.get_by_role('button', name=_('Submit'), exact=True).click()
        expect(text).to_be_hidden()


def create_account(self_service: SelfService, get_registration_info):
    self_service.navigate_create_account()
    info = get_registration_info()
    self_service.fill_create_account(info['attributes'])

    expect(self_service.page.get_by_text(_('Account creation successful'))).to_be_visible()
    return info


def auto_verify(self_service: SelfService, mails):
    mail = _get_mail(mails)
    self_service.page.goto(mail['auto_verify_link'])
    self_service.page.get_by_role('button', name='Verify account').click()

    expect(self_service.page.get_by_text(_('Your account has been successfully verified'))).to_be_visible()


def manual_verify(self_service: SelfService, mails):
    mail = _get_mail(mails)
    self_service.page.goto(mail['verify_link'])
    self_service.fill_create_account(
        {
            'username': UserCreationAttribute('Username', mail['verify_data']['username']),
            'token': UserCreationAttribute('Token', mail['verify_data']['token']),
        },
        _('Verify Account'),
    )

    expect(self_service.page.get_by_text(_('Your account has been successfully verified'))).to_be_visible()
