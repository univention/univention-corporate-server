#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test asynchronous client and reports
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest
##   - univention-directory-reports
## execute with: --tb=native -s -l -vv --cov-report=term-missing  --cov-report=html --cov=univention.admin.rest.async_client


import os
from urllib.parse import parse_qsl, urlparse

import pytest

from univention.admin.rest.async_client import UDM, Unauthorized
from univention.config_registry import ucr as _ucr


check_delegation = pytest.mark.skipif(not _ucr.is_true('umc/udm/delegation'), reason='umc/udm/delegation not activated')


async def create_rest_report(
    username: str,
    objects: list[str],
    module: str,
    expected_success: bool = True,
    expected_contents: list[str] | None = None,
    forbidden_contents: list[str] | None = None,
    password: str = 'univention',
) -> None:
    uri = 'http://localhost/univention/udm/'
    try:
        async with UDM.http(uri, username, password) as client:
            response = await client.create_report(module, {'report': 'CSV Report', 'objects': objects})
            if not expected_success:
                pytest.fail('Expected failure but got success')

            report_url = response.get('URL')
            report = parse_qsl(urlparse(report_url).query)[0][1]
            assert os.path.isfile(os.path.join('/usr/share/univention-management-console-module-udm', report))

            report_data = await client.get_report(report)
            assert report_data
            assert report.endswith('.csv')

            report_content = report_data.decode('utf-8') if isinstance(report_data, bytes) else report_data
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


@check_delegation
@pytest.mark.asyncio
async def test_user_report_access(ou, ucr, account, ldap_base) -> None:
    other_user_dn = f'cn=users,ou=ou2,{ldap_base}'
    other_user_username = 'user1-ou2'
    await create_rest_report(
        account.username,
        [ou.user_dn, ou.admin_dn, ou.lesser_admin_dn, other_user_dn],
        'users/user',
        expected_success=True,
        expected_contents=[ou.user_username, ou.admin_username, ou.lesser_admin_username, other_user_username],
        password=account.bindpw,
    )
    await create_rest_report(
        ou.admin_username,
        [ou.admin_dn, ou.user_dn],
        'users/user',
        expected_success=True,
        expected_contents=[ou.admin_username, ou.user_username],
        forbidden_contents=[other_user_username],
    )
    await create_rest_report(ou.admin_username, [ou.user_dn, other_user_dn], 'users/user', expected_success=False)
    await create_rest_report(ou.lesser_admin_username, [ou.user_dn], 'users/user', expected_success=False)
    await create_rest_report(ou.lesser_admin_username, [ou.admin_dn], 'users/user', expected_success=False)


@check_delegation
@pytest.mark.asyncio
async def test_group_report_access(ou, ucr, account, ldap_base) -> None:
    other_group_dn = f'cn=groups,ou=ou2,{ldap_base}'
    other_group_username = 'group1-ou2'

    await create_rest_report(
        account.username,
        [ou.group_dn, other_group_dn],
        'groups/group',
        expected_success=True,
        expected_contents=[ou.group_username, other_group_username],
        password=account.bindpw,
    )

    await create_rest_report(
        ou.admin_username,
        [ou.group_dn],
        'groups/group',
        expected_success=True,
        expected_contents=[ou.group_username],
    )

    await create_rest_report(ou.admin_username, [ou.group_dn, other_group_dn], 'groups/group', expected_success=False)

    await create_rest_report(
        ou.lesser_admin_username,
        [ou.group_dn, other_group_dn],
        'groups/group',
        expected_success=False,
    )

    await create_rest_report(ou.lesser_admin_username, [ou.group_dn], 'groups/group', expected_success=False)
