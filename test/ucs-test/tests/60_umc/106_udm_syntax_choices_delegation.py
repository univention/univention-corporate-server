#!/usr/share/ucs-test/runner python3
## desc: Test syntax choices with delegated administration
## bugs: [1815]
## roles:
##  - domaincontroller_master
## packages: [python3-univention-directory-manager, univention-management-console-module-udm]
## exposure: safe

import unittest

import pytest

from univention.admin.uldap import getAdminConnection
from univention.config_registry import ucr
from univention.testing.ucs_samba import wait_for_drs_replication
from univention.testing.umc import Client


# Skip tests when delegation is not activated
check_delegation = pytest.mark.skipif(
    not ucr.is_true('umc/udm/delegation'),
    reason='umc/udm/delegation not activated',
)


@pytest.fixture
def bremen_ou(udm, random_username):
    """Create an OU with an OU admin and a normal user."""
    dn_ou = udm.create_object('container/ou', name='bremen')
    ouadmin_username = random_username()
    normal_user_username = random_username()

    dn_admin = udm.create_object(
        'users/user',
        username=ouadmin_username,
        guardianRoles=['umc:udm:ouadmin&umc:udm:ou=bremen'],
        lastname='bremen_admin',
        password='univention',
    )

    dn_user = udm.create_object(
        'users/user',
        username=normal_user_username,
        guardianRoles=['umc:udm:dummyrole'],
        position=dn_ou,
        lastname='lastname',
        password='univention',
    )

    domain_user_username = random_username()
    dn_domain_user = udm.create_object(
        'users/user',
        username=domain_user_username,
        guardianRoles=['umc:udm:dummyrole'],
        lastname='domain_user',
        password='univention',
    )

    udm.modify_object('container/ou', dn=dn_ou, userPath='1')

    yield {
        'ou_dn': dn_ou,
        'ouadmin_dn': dn_admin,
        'ouadmin_username': ouadmin_username,
        'user_dn': dn_user,
        'user_username': normal_user_username,
        'domain_user_dn': dn_domain_user,
        'domain_user_username': domain_user_username,
    }

    udm.remove_object('users/user', dn=dn_domain_user)
    udm.remove_object('users/user', dn=dn_user)
    udm.remove_object('users/user', dn=dn_admin)
    udm.remove_object('container/ou', dn=dn_ou)


class TestSyntaxChoices(unittest.TestCase):
    """Test basic syntax choices functionality."""

    def setUp(self):
        wait_for_drs_replication("(objectClass=*)")
        self.lo, self.po = getAdminConnection()
        self.base_dn = self.lo.base

    def test_syntax_choices(self):
        """Test that syntax choices for UserID and GroupID don't cause errors."""
        client = Client.get_test_connection()

        res = client.umc_command('udm/syntax/choices', {"syntax": "UserID"}, 'shares/share')
        assert res.result, "UserID syntax choices should return results"

        res = client.umc_command('udm/syntax/choices', {"syntax": "GroupID"}, 'shares/share')
        assert res.result, "GroupID syntax choices should return results"

    def test_dn_based_syntax_choices(self):
        """Test that syntax choices with DNs work properly."""
        client = Client.get_test_connection()

        res = client.umc_command('udm/syntax/choices', {"syntax": "UserDN"}, 'shares/share')
        assert res.result, "UserDN syntax choices should return results"

        res = client.umc_command('udm/syntax/choices', {"syntax": "GroupDN"}, 'shares/share')
        assert res.result, "GroupDN syntax choices should return results"

        for choice in res.result[:5]:
            assert 'id' in choice
            assert 'label' in choice
            assert 'module_name' in choice


@check_delegation
def test_userdn_delegation_filtering(bremen_ou):
    """
    Test that UserDN filtering works differently based on user roles.
    OU admin should only see users from their own OU.
    Domain admin should see all users.
    """
    admin_client = Client.get_test_connection()
    admin_res = admin_client.umc_command('udm/syntax/choices', {"syntax": "UserDN"}, 'shares/share')

    admin_dns = [choice['id'] for choice in admin_res.result]
    assert bremen_ou['user_dn'] in admin_dns
    assert bremen_ou['domain_user_dn'] in admin_dns

    ouadmin_client = Client()
    ouadmin_client.authenticate(bremen_ou['ouadmin_username'], 'univention')
    ouadmin_res = ouadmin_client.umc_command('udm/syntax/choices', {"syntax": "UserDN"}, 'shares/share')

    ouadmin_dns = [choice['id'] for choice in ouadmin_res.result]
    assert bremen_ou['user_dn'] in ouadmin_dns
    assert bremen_ou['domain_user_dn'] not in ouadmin_dns

    admin_id_res = admin_client.umc_command('udm/syntax/choices', {"syntax": "UserID"}, 'shares/share')
    ouadmin_id_res = ouadmin_client.umc_command('udm/syntax/choices', {"syntax": "UserID"}, 'shares/share')

    assert len(admin_id_res.result) == len(ouadmin_id_res.result)


if __name__ == '__main__':
    unittest.main()
