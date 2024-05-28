#!/usr/share/ucs-test/runner pytest-3
## desc: Tests the Univention Self Service Invitation
## bugs: [57226]
## tags: [udm, apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
## - univention-self-service-invitation

import secrets
import subprocess
import time
from collections.abc import Callable

import pytest

from univention.testing import utils
from univention.testing.udm import UCSTestUDM


WAIT_TIME_SYSTEMMAIL = 45.0


@pytest.fixture()
def restart_services():
    subprocess.call(['service', 'postfix', 'restart'], close_fds=True)
    subprocess.call(
        ['service', 'univention-self-service-invitation', 'restart'], close_fds=True)
    time.sleep(3)


def systemmail_contains_string(expected_string: str):
    with open('/var/spool/mail/systemmail', 'rb') as f:
        for line in f.readlines():
            if expected_string.lower() in line.decode('UTF-8', 'replace').lower():
                return True
    return False


def assert_user_has_invitation_mail(username: str) -> (bool, str):
    """Check if invitation mail has been sent for user `username`"""
    expected = f'Dear user {username}'
    has_mail = systemmail_contains_string(expected)
    assert has_mail, f'Expected user invitation "{expected}" not found in /var/spool/mail/systemmail'


def assert_user_has_no_invitation_mail(username: str) -> (bool, str):
    """Check if invitation mail has been sent for user `username`"""
    expected = f'Dear user {username}'
    has_mail = systemmail_contains_string(expected_string=expected)
    assert not has_mail, f'Unexpected user invitation "{expected}" found in /var/spool/mail/systemmail'


def test_mail_invitation(restart_services, udm: UCSTestUDM, random_string: Callable) -> None:
    container_dn = udm.create_object(
        'container/cn', position=f'{udm.LDAP_BASE}', name=random_string())

    username = udm.create_user(
        position=container_dn, pwdChangeNextLogin='1', PasswordRecoveryEmail='root@localhost')[1]
    utils.wait_for_replication_and_postrun()
    time.sleep(WAIT_TIME_SYSTEMMAIL)
    assert_user_has_invitation_mail(username)


def test_mail_invitation_with_policy(restart_services, udm: UCSTestUDM, random_string: Callable) -> None:
    """
    Test if invitation mail gets delivered when a password policy is applied to the user container

    Bug #57226
    """
    policy_dn = udm.create_object(
        'policies/pwhistory', name=random_string(), expiryInterval=5, length=5, pwLength=12)
    container_dn = udm.create_object(
        'container/cn', position=f'{udm.LDAP_BASE}', name=random_string(), policy_reference=policy_dn)

    username = udm.create_user(position=container_dn, password=secrets.token_hex(
        12), pwdChangeNextLogin='1', PasswordRecoveryEmail='root@localhost')[1]
    utils.wait_for_replication_and_postrun()
    time.sleep(WAIT_TIME_SYSTEMMAIL)
    assert_user_has_invitation_mail(username)


def test_no_mail_invitation(restart_services, udm: UCSTestUDM, random_string: Callable) -> None:
    """Test that no invitation mail gets delivered when the pwdChangeNextLogin flag is not set, but the reocvery email is"""
    username = udm.create_user(password=secrets.token_hex(
        12), PasswordRecoveryEmail='root@localhost')[1]
    utils.wait_for_replication_and_postrun()
    time.sleep(WAIT_TIME_SYSTEMMAIL)
    assert_user_has_no_invitation_mail(username)


def test_no_mail_invitation_with_policy(restart_services, udm: UCSTestUDM, random_string: Callable) -> None:
    """
    Test that no invitation mail gets delivered when the pwdChangeNextLogin flag is not set, but the recovery mail is

    additionally: password policy is applied to the created user
    """
    policy_dn = udm.create_object(
        'policies/pwhistory', name=random_string(), expiryInterval=5, length=5, pwLength=12)
    container_dn = udm.create_object(
        'container/cn', position=f'{udm.LDAP_BASE}', name=random_string(), policy_reference=policy_dn)

    username = udm.create_user(position=container_dn, password=secrets.token_hex(
        12), PasswordRecoveryEmail='root@localhost')[1]
    utils.wait_for_replication_and_postrun()
    time.sleep(WAIT_TIME_SYSTEMMAIL)
    assert_user_has_no_invitation_mail(username)
