#!/usr/share/ucs-test/runner pytest-3
## desc: Test the password complexity message
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

import subprocess
import time

import pytest
from test_self_service import capture_mails, self_service_user

import univention.lib.umc
from univention.testing.strings import random_string, random_username


@pytest.fixture()
def close_all_processes():
    """force all module processes to close"""
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service', 'univention-self-service-passwordreset-umc.service'])
    time.sleep(3)


@pytest.fixture()
def selfservice_container_dn(ucr, udm, close_all_processes):
    """force all module processes to close"""
    ldap_base = ucr.get('ldap/base')

    pwhistory_dn = udm.create_object(
        'policies/pwhistory',
        name=random_string(),
        length="3",
        pwLength="8",
        pwQualityCheck="TRUE",
    )
    container_dn = udm.create_object(
        'container/cn',
        name=random_string(),
        position=f"cn=users,{ldap_base}",
        policy_reference=pwhistory_dn,
    )

    ucr.handler_set([
        "password/quality/credit/upper=3",
        "umc/login/password-complexity-message/en=Password must contain at least 3 upper case letters",
        "umc/login/password-complexity-message/de=Passwort muss mindestens 3 Großbuchstaben enthalten",
        "umc/self-service/passwordreset/frontend/enabled=true",
        "umc/self-service/account-registration/frontend/enabled=true",
        "umc/self-service/account-registration/backend/enabled=true",
        f"umc/self-service/account-registration/usercontainer={container_dn}",
    ])
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service', 'univention-self-service-passwordreset-umc.service'])
    time.sleep(3)
    return container_dn


@pytest.mark.parametrize("message,lang", [
    ("Password must contain at least 3 upper case letters", "en-US"),
    ("Passwort muss mindestens 3 Großbuchstaben enthalten", "de-DE"),
])
def test_expired_user_login_returns_password_complexity_message(ucr, selfservice_container_dn, message, lang):
    umc_client = univention.lib.umc.Client(language=lang.split('-')[0])
    reset_mail_address = f'{random_username()}@{random_username()}'
    with self_service_user(mailPrimaryAddress=reset_mail_address, overridePWLength=1, overridePWHistory=1, pwdChangeNextLogin=1, position=selfservice_container_dn) as user:
        with pytest.raises(Exception) as exc:
            umc_client.umc_auth(user.username, user.password)
        response = exc.value.response
        assert response.status == 401
        assert message in response.data['message']
        with pytest.raises(Exception) as exc:
            umc_client.umc_auth(user.username, user.password, new_password="U")
        response = exc.value.response
        assert response.status == 401
        assert message in response.data['message']


@pytest.mark.parametrize("message,lang", [
    ("Password must contain at least 3 upper case letters", "en-US"),
    ("Passwort muss mindestens 3 Großbuchstaben enthalten", "de-DE"),
])
def test_user_password_change_password_complexity_message(ucr, selfservice_container_dn, message, lang):
    umc_client = univention.lib.umc.Client(language=lang.split('-')[0])
    reset_mail_address = f'{random_username()}@{random_username()}'
    with self_service_user(mailPrimaryAddress=reset_mail_address, overridePWLength=1, overridePWHistory=1, position=selfservice_container_dn) as user:

        umc_client.umc_auth(user.username, user.password)
        with pytest.raises(Exception) as exc:
            data = {
                "password": {
                    "password": user.password,
                    "new_password": "U",
                },
            }
            headers = {
                "Accept-Language": lang,
            }
            umc_client.umc_set(options=data, headers=headers)

        response = exc.value.response
        assert response.status == 400
        assert message in response.data['message']


@pytest.mark.parametrize("message,lang", [
    ("Password must contain at least 3 upper case letters", "en-US"),
    ("Passwort muss mindestens 3 Großbuchstaben enthalten", "de-DE"),
])
def test_password_reset_returns_password_complexity_message(ucr, selfservice_container_dn, message, lang):
    umc_client = univention.lib.umc.Client(language=lang.split('-')[0])
    reset_mail_address = f'{random_username()}@{random_username()}'
    password = random_string()
    with self_service_user(mailPrimaryAddress=reset_mail_address, overridePWLength=1, overridePWHistory=1, password=password, position=selfservice_container_dn) as user:
        email = 'testuser@example.com'
        user.set_contact(email=email)
        assert 'email' in user.get_reset_methods()

        timeout = 5
        with capture_mails(timeout=timeout) as mails:
            user.send_token('email')

        mail = mails.data and mails.data[0]
        assert mail, f'No email has been received in {timeout} seconds'

        # test password change
        token = mail.split('and enter the following token manually:')[-1].split('Greetings from your password self service system.')[0].strip()
        assert token, f'Could not parse token from mail. Is there a token in it? {mail!r}'

        user.password = random_string().lower()
        with pytest.raises(Exception) as exc:
            headers = {
                "Accept-Language": lang,
            }
            data = {
                'username': user.username,
                'password': user.password,
                'token': token,
            }
            umc_client.umc_command('passwordreset/set_password', options=data, headers=headers)
        response = exc.value.response

        assert response.status == 400
        assert message in response.data['message']


@pytest.mark.parametrize("message,lang", [
    ("Password must contain at least 3 upper case letters", "en-US"),
    ("Passwort muss mindestens 3 Großbuchstaben enthalten", "de-DE"),
])
def test_account_registration_returns_password_complexity_message(ucr, selfservice_container_dn, message, lang):
    umc_client = univention.lib.umc.Client(language=lang.split('-')[0])
    username = random_username()
    reset_mail_address = f'{username}@{username}'
    data = {
        "attributes": {
            "PasswordRecoveryEmail": reset_mail_address,
            "password": "U1n2i3v4e5n6t7i8o9n0@#",
            "password--retype": "U1n2i3v4e5n6t7i8o9n0@#",
            "firstname": username,
            "lastname": username,
            "username": username,
        },
    }
    headers = {
        "Accept-Language": lang,
    }
    response = umc_client.umc_command(path="passwordreset/create_self_registered_account", options=data, flavor=None, headers=headers)
    assert response.status == 200
    assert response.data['result']['success'] is False
    assert response.data['result']['failType'] == 'CREATION_FAILED'
    assert message in response.data['result']['data']
