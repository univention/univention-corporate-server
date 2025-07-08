#!/usr/share/ucs-test/runner python3
## desc: Test querying UDM with a non-posix UMC user
## bugs: [37178]
## roles:
##  - domaincontroller_master
## exposure: dangerous

import sys

import pytest

from univention.config_registry import ucr
from univention.lib.umc import BadRequest
from univention.testing import utils
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM
from univention.testing.umc import Client

from umc import UMCBase


class TestUMCUserAuthentication(UMCBase):

    def __init__(self):
        """Test Class constructor"""
        super().__init__()

        self.UDM = None

        self.test_user_dn = ''
        self.test_username = ''
        self.test_password = ''

    def create_user(self):
        """Creates a group and a user in it for the test."""
        print(f"\nCreating a user '{self.test_username}' without posix")

        self.test_user_dn = self.UDM.create_ldap_user(
            password=self.test_password,
            username=self.test_username,
            policy_reference='cn=default-umc-all,cn=UMC,cn=policies,%s' % self.ucr['ldap/base'],
        )[0]
        utils.verify_ldap_object(self.test_user_dn)

    def query_udm(self):
        """Queries UDM's users/ldap from UMC"""
        delegation_enabled = ucr.is_true('directory/manager/web/delegative-administration/enabled')
        if delegation_enabled:
            with pytest.raises(BadRequest):
                self.request('udm/query', {'objectType': 'users/ldap', 'objectProperty': 'username', 'objectPropertyValue': self.test_username}, 'users/user')
        else:
            assert self.request('udm/query', {'objectType': 'users/ldap', 'objectProperty': 'username', 'objectPropertyValue': self.test_username}, 'users/user')

    def authenticate_to_umc(self, username, password):
        """
        Authenticates to UMC using 'self.client' and given
        'password' with 'username'. Updates the cookie.
        Returns 'True' on success and 'False' in any other case.
        """
        try:
            response = self.client.authenticate(username, password)
            assert response.status == 200
            return True
        except Exception as exc:
            utils.fail(f"An exception while trying to authenticate to UMC with a 'username'={self.test_username} and 'password'={password}: {exc!r}")

    def main(self):
        """Tests the UMC user authentication and various password change cases."""
        self.test_username = 'umc_test_user_' + random_username(6)
        self.test_password = 'univention'

        with UCSTestUDM() as self.UDM:
            self.create_user()
            self.client = Client()
            self.authenticate_to_umc(self.test_username, self.test_password)
            self.query_udm()


if __name__ == '__main__':
    TestUMC = TestUMCUserAuthentication()
    sys.exit(TestUMC.main())
