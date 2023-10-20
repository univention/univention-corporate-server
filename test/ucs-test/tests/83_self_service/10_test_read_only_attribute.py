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
from test_self_service import self_service_user

from univention.testing.strings import random_username


@pytest.fixture()
def close_all_processes():
    """force all module processes to close"""
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service', 'univention-self-service-passwordreset-umc.service'])
    time.sleep(3)


@pytest.fixture()
def self_service_prepare(ucr, udm, close_all_processes,):
    """force all module processes to close"""
    ucr.handler_set([
        'self-service/udm_attributes/read-only=title',
        'self-service/udm_attributes=title,jpegPhoto,e-mail,phone,roomnumber,departmentNumber,country,homeTelephoneNumber,mobileTelephoneNumber,homePostalAddress',
    ])
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service', 'univention-self-service-passwordreset-umc.service'])
    time.sleep(3)


def test_self_service_read_only_attribute(ucr, self_service_prepare,):
    reset_mail_address = f'{random_username()}@{random_username()}'
    with self_service_user(mailPrimaryAddress=reset_mail_address, language="en-US",) as user:
        user.auth()
        # check that title is returned by get_user_attributes_descriptions
        response = user.command('passwordreset/get_user_attributes_descriptions', **{},)  # noqa: PIE804
        attributes = [attr['id'] for attr in response.result]
        assert response.status == 200
        assert 'title' in attributes

        # check that title is returned by get_user_attributes_values
        data = {
            "attributes": attributes,
        }
        response = user.command('passwordreset/get_user_attributes_values', **data,)
        assert response.status == 200
        assert "title" in response.result

        # check that title is read-only
        data = {
            "attributes": {
                "title": "Dr.",
            },
        }
        with pytest.raises(Exception) as exc:
            user.command('passwordreset/set_user_attributes', **data,)
        response = exc.value.response
        assert response.status == 400
        assert response.message == 'The attribute title is read-only.'
