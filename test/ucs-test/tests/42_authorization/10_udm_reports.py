#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## exposure: dangerous
## desc: check if directory reports can be generated via UDM
## packages:
##   - univention-directory-reports
##   - python3-univention-directory-manager

import pytest

from univention.admin import uldap
from univention.admin.uexceptions import authFail
from univention.config_registry import ucr as _ucr
from univention.directory.reports import Report


check_delegation = pytest.mark.skipif(not _ucr.is_true('umc/udm/delegation'), reason='umc/udm/delegation not activated')


def create_report(
    connection: uldap.access,
    objects: list[str],
    module: str,
    expected_success: bool = True,
    expected_contents: list[str] | None = None,
    forbidden_contents: list[str] | None = None,
) -> None:
    try:
        report = Report(connection, module, objects, 'CSV Report')
        result = report.create()
        if not expected_success:
            pytest.fail('Expected failure but got success')

        assert result
        assert isinstance(result, bytes)

        report_content = result.decode('utf-8')
        print(report_content)

        if expected_contents:
            for content in expected_contents:
                assert content in report_content, f"Expected content '{content}' not found in report"

        if forbidden_contents:
            for content in forbidden_contents:
                assert content not in report_content, f"Forbidden content '{content}' found in report"

    except authFail:
        if expected_success:
            raise
        # Expected unauthorized for restricted users


@check_delegation
def test_user_report_access(ou, account, ldap_base) -> None:
    ouadmin_username = ou.admin_username
    lesser_ouadmin_username = ou.lesser_admin_username

    admin_connection = uldap.access(binddn=account.binddn, bindpw=account.bindpw)
    ouadmin_connection = uldap.access(binddn=f'uid={ouadmin_username}', bindpw='univention')
    lesser_ouadmin_connection = uldap.access(binddn=f'uid={lesser_ouadmin_username}', bindpw='univention')

    other_user_dn = f'cn=users,ou=ou2,{ldap_base}'
    other_user_username = 'user1-ou2'

    create_report(
        admin_connection,
        [ou.user_dn, ou.lesser_admin_dn, other_user_dn],
        'users/user',
        expected_success=True,
        expected_contents=[ou.admin_username, ou.lesser_admin_username, other_user_username],
    )
    create_report(
        ouadmin_connection,
        [ou.admin_dn, ou.lesser_admin_dn],
        'users/user',
        expected_success=True,
        expected_contents=[ou.admin_username, ou.user_username],
        forbidden_contents=[other_user_username],
    )
    create_report(ouadmin_connection, [ou.user_dn, other_user_dn], 'users/user', expected_success=False)
    create_report(lesser_ouadmin_connection, [ou.user_dn], 'users/user', expected_success=False)
    create_report(lesser_ouadmin_connection, [ou.admin_dn], 'users/user', expected_success=False)


@check_delegation
def test_group_report_access(ou, account, ldap_base) -> None:
    ouadmin_username = ou.admin_username
    lesser_ouadmin_username = ou.lesser_admin_username
    admin_connection = uldap.access(binddn=account.binddn, bindpw=account.bindpw)
    ouadmin_connection = uldap.access(binddn=f'uid={ouadmin_username}', bindpw='univention')
    lesser_ouadmin_connection = uldap.access(binddn=f'uid={lesser_ouadmin_username}', bindpw='univention')

    other_group_dn = f'cn=groups,ou=ou2,{ldap_base}'
    other_group_username = 'group1-ou2'

    create_report(
        admin_connection,
        [ou.group_dn, other_group_dn],
        'groups/group',
        expected_success=True,
        expected_contents=[ou.group_username, other_group_username],
    )

    create_report(ouadmin_connection, [ou.group_dn], 'groups/group', expected_success=True, expected_contents=[ou.group_username])
    create_report(ouadmin_connection, [ou.group_dn, other_group_dn], 'groups/group', expected_success=False)

    create_report(
        lesser_ouadmin_connection,
        [other_group_dn],
        'groups/group',
        expected_success=False,
    )

    create_report(lesser_ouadmin_connection, [ou.group_dn], 'groups/group', expected_success=False)
