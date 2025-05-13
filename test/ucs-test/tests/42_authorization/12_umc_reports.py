#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## exposure: dangerous
## desc: check if directory reports can be generated
## packages:
##  - univention-directory-reports
##  - univention-management-console-module-udm

import os
from urllib.parse import parse_qsl, urlparse

import pytest

from univention.config_registry import ucr as _ucr
from univention.lib.umc import Unauthorized
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(not _ucr.is_true('umc/udm/delegation'), reason='umc/udm/delegation not activated')


def create_umc_report(
    client: Client,
    objects: list[str],
    module: str,
    expected_contents: list[str],
    expected_success: bool = True,
    forbidden_contents: list[str] | None = None,
) -> None:
    """
    Create and verify a UMC report
    :param client: The authenticated client to use
    :param objects: List of DNs to include in report
    :param module: UDM module to query
    :param expected_contents: List of strings that must appear in the report
    :param expected_success: Whether the operation should succeed
    :param forbidden_contents: Strings that must not appear in the report
    """
    try:
        r = client.umc_command('udm/reports/create', {'report': 'CSV Report', 'objects': objects}, module)
        if not expected_success:
            pytest.fail('Expected failure but got success')
        assert r.status == 200
        report = parse_qsl(urlparse(r.result.get('URL')).query)[0][1]
        assert os.path.isfile(os.path.join('/usr/share/univention-management-console-module-udm', report))

        r = client.umc_command('udm/reports/get', {'report': report}, print_response=False)
        assert r.status == 200
        assert r.data
        assert report.endswith('.csv')

        report_content = r.data.decode('utf-8') if isinstance(r.data, bytes) else r.data
        print(report_content)

        if expected_contents:
            for content in expected_contents:
                assert content in report_content, f"Expected content '{content}' not found in report"

        if forbidden_contents:
            for content in forbidden_contents:
                assert content not in report_content, f"Forbidden content '{content}' found in report"

    except Unauthorized:
        if expected_success:
            raise
        # Expected unauthorized for restricted users


@check_delegation
def test_user_report_access(ou, ldap_base, admin_account) -> None:
    admin_client = Client.get_test_connection()
    ouadmin_client = Client()
    ouadmin_client.authenticate(ou.admin_username, 'univention')
    lesser_ouadmin_client = Client()
    lesser_ouadmin_client.authenticate(ou.lesser_admin_username, 'univention')

    other_user_dn = f'cn=users,ou=ou2,{ldap_base}'
    other_user_username = 'user1-ou2'

    create_umc_report(
        admin_client,
        [ou.user_dn, ou.admin_dn, ou.lesser_admin_dn, other_user_dn],
        'users/user',
        expected_success=True,
        expected_contents=[admin_account.username, ou.admin_username, ou.lesser_admin_username, other_user_username],
    )

    create_umc_report(
        ouadmin_client,
        [ou.admin_dn, ou.user_dn],
        'users/user',
        expected_success=True,
        expected_contents=[ou.admin_username, ou.user_username],
        forbidden_contents=[other_user_username],
    )

    create_umc_report(ouadmin_client, [ou.user_dn, other_user_dn], 'users/user', expected_success=False)
    create_umc_report(lesser_ouadmin_client, [ou.user_dn], 'users/user', expected_success=False)
    create_umc_report(lesser_ouadmin_client, [ou.admin_dn], 'users/user', expected_success=False)


@check_delegation
def test_group_report_access(ou, ldap_base) -> None:
    admin_client = Client.get_test_connection()
    ouadmin_client = Client()
    ouadmin_client.authenticate(ou.admin_username, 'univention')
    lesser_ouadmin_client = Client()
    lesser_ouadmin_client.authenticate(ou.lesser_admin_username, 'univention')

    other_group_dn = f'cn=groups,ou=ou2,{ldap_base}'
    other_group_username = 'group1-ou2'

    create_umc_report(
        admin_client,
        [ou.group_dn, other_group_dn],
        'groups/group',
        expected_success=True,
        expected_contents=[ou.group_username, other_group_username],
    )

    create_umc_report(ouadmin_client, [ou.group_dn], 'groups/group', expected_success=True, expected_contents=[ou.group_username])
    create_umc_report(ouadmin_client, [ou.group_dn, other_group_dn], 'groups/group', expected_success=False)

    create_umc_report(
        lesser_ouadmin_client,
        [other_group_dn],
        'groups/group',
        expected_success=False,
    )

    create_umc_report(lesser_ouadmin_client, [ou.group_dn], 'groups/group', expected_success=False)
