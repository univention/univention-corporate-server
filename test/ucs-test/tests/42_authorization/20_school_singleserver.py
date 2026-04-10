#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check delegated administration in ucs@school
## bugs: [59150]
## roles:
##  - domaincontroller_master
## exposure: dangerous
## packages:
##  - ucs-school-singleserver


import pytest
from conftest import RestClientHelper

from univention.admin.uldap import getAdminConnection
from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_username
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(
    not _ucr.is_true('directory/manager/web/delegative-administration/enabled'),
    reason='directory/manager/web/delegative-administration/enabled not activated',
)


class schoolWizard:

    def __init__(self):
        self.connection = Client.get_test_connection()
        self.lo = getAdminConnection()[0]
        self.cleanup_users = []

    def create_student(self, school: str = "DEMOSCHOOL", school_class: str = "Democlass", username: str | None = None):
        username = username or random_username()
        options = [{
            "object": {
                "school": school,
                "type": "student",
                "firstname": username,
                "lastname": username,
                "name": username,
                "school_classes": {
                    school: [
                        f"{school}-{school_class}",
                    ],
                },
            },
        }]
        result = self.connection.umc_command("schoolwizards/users/add", options, "schoolwizards/users").result[0]
        dn = None
        if result is True:
            dn = self.lo.searchDn(f'uid={username}')[0]
            self.cleanup_users.append({"dn": dn, "school": school})
        return result, username, dn

    def remove_user(self, dn: str, school: str):
        options = [{
            "object": {
                "$dn$": dn,
                "school": school,
                "remove_from_school": school,
            },
        }]
        return self.connection.umc_command("schoolwizards/users/remove", options, "schoolwizards/users").result[0]

    def cleanup(self):
        for user in self.cleanup_users:
            self.remove_user(user["dn"], user["school"])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f'Cleanup after exception: {exc_type} {exc_value}')
        self.cleanup()


@pytest.fixture
def school_wizard():
    with schoolWizard() as wizard:
        yield wizard


@check_delegation
def test_ucsschoolPurgeTimestamp(
    ldap_base: str,
    admin_rest_client: RestClientHelper,
    school_wizard: schoolWizard,
):
    result, username, dn = school_wizard.create_student()
    assert result
    changes = {'ucsschoolPurgeTimestamp': '2099-12-12'}
    admin_rest_client.modify_user(dn, changes)
    # check normal user module with delegated administration, this fail with
    # The given date does not conform to iso8601, example: "2009-01-01"."
    admin_rest_client.search_user(f'uid={username}')
