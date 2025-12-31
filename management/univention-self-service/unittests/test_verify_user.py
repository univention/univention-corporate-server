#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import passlib.hash as passlib
import pytest
from univentionunittests.umc import import_umc_module

from univention.management.console.modules import UMC_Error


selfservice = import_umc_module('passwordreset')


@pytest.fixture
def verify_ucr(selfservice_ucr):
    selfservice_ucr['umc/self-service/passwordreset/email/enabled'] = 'yes'
    selfservice_ucr['umc/self-service/passwordreset/sms/enabled'] = 'yes'
    selfservice_ucr['umc/self-service/passwordreset/sms/command'] = 'testsmscmd'
    selfservice_ucr['umc/self-service/passwordreset/sms/country_code'] = '49'
    return selfservice_ucr


@pytest.fixture
def ldap_database_file():
    return 'unittests/verify.ldif'


@pytest.fixture
def jobst(ldap_database):
    return ldap_database.objs["uid=jobst,cn=self registered users,dc=intranet,dc=example,dc=de"]


def assert_user_password(user, password):
    ldap_password = user.attrs["userPassword"][0][7:].decode('ASCII')
    assert compare_password(password, ldap_password)


def compare_password(plaintext, hashed):
    if hashed.startswith("$1"):
        return passlib.md5_crypt.verify(plaintext, hashed)
    if hashed.startwith("$5"):
        return passlib.sha256_crypt.verify(plaintext, hashed)
    if hashed.startwith("$6"):
        return passlib.sha512_crypt.verify(plaintext, hashed)


def test_meta_password():
    assert compare_password("S3cr3t!!!", "$6$9N.LqdohCIFk73D3$0k6nM/G6QyRy8s5RyBIREWxWXv5u/Fmzcd4Ncy/DvVUdz2g5Hf6Nt3.4yyHCWzgNISfbhj/aZxf3IBnI0Xrpm1")
    assert compare_password("S3cr3!!!", "$6$9N.LqdohCIFk73D3$0k6nM/G6QyRy8s5RyBIREWxWXv5u/Fmzcd4Ncy/DvVUdz2g5Hf6Nt3.4yyHCWzgNISfbhj/aZxf3IBnI0Xrpm1") is False
    assert compare_password("S3cr3t!!!", "$6$9N.LqdohCIFk73D3$0k6nM/G6QyRy8s5RyBIREWxWXv5u/Fmzcd4Ncy/DvVUdz2g5Hf6Nt3.4yyHCWzgNISfbhj/aZxf3IBnI0Xrpm") is False


def test_udm_set_password_standard(selfservice_instance, mocked_conn, jobst):
    selfservice_instance.udm_set_password("jobst", "S3cr3t!!!", email_verified=False)
    assert_user_password(jobst, "S3cr3t!!!")
    assert jobst.attrs["univentionPasswordRecoveryEmailVerified"] == [b"FALSE"]


def test_udm_set_password_verified(selfservice_instance, mocked_conn, jobst):
    selfservice_instance.udm_set_password("jobst", "S3cr3t!!!", email_verified=True)
    assert_user_password(jobst, "S3cr3t!!!")
    assert jobst.attrs["univentionPasswordRecoveryEmailVerified"] == [b"TRUE"]


def test_udm_set_password_verified_admember(selfservice_instance, mocked_conn, jobst):
    selfservice_instance.udm_set_password("jobst", "S3cr3t!!!", email_verified=True)
    assert_user_password(jobst, "S3cr3t!!!")
    assert jobst.attrs["univentionPasswordRecoveryEmailVerified"] == [b"TRUE"]


def test_reset_password_with_email(mocker, mocked_conn, verify_ucr, selfservice_instance, umc_request):
    umc_request.options = {
        "token": "12345",
        "username": "jobst",
        "password": "univention",
    }
    check_token = mocker.patch.object(selfservice_instance, '_check_token')
    check_token.return_value = {"method": "email"}
    udm_set_password = mocker.patch.object(selfservice_instance, 'udm_set_password')
    with pytest.raises(UMC_Error) as exc:
        selfservice_instance.set_password(umc_request)
    assert exc.value.status == 200
    udm_set_password.assert_called_once_with("jobst", "univention", email_verified=True)


def test_reset_password_with_sms(mocker, mocked_conn, verify_ucr, selfservice_instance, umc_request):
    umc_request.options = {
        "token": "12345",
        "username": "jobst",
        "password": "univention",
    }
    check_token = mocker.patch.object(selfservice_instance, '_check_token')
    check_token.return_value = {"method": "mobile"}
    udm_set_password = mocker.patch.object(selfservice_instance, 'udm_set_password')
    with pytest.raises(UMC_Error) as exc:
        selfservice_instance.set_password(umc_request)
    assert exc.value.status == 200
    udm_set_password.assert_called_once_with("jobst", "univention", email_verified=False)
