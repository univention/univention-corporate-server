#!/usr/share/ucs-test/runner pytest-3 -s
## desc: UDM property filtering authorization tests for directory reports
## bugs: []
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import csv
import os
from types import SimpleNamespace

import pytest

import univention.admin.authorization as udm_auth
from univention.admin import authorization, uldap
from univention.config_registry import ucr as _ucr
from univention.directory.reports import Report
from univention.testing.udm import UCSTestUDM


REPORTS_PATH = '/usr/share/univention-management-console-module-udm'
REPORTS = {'CSV Report', 'PDF Document'}


check_delegation = pytest.mark.skipif(
    not _ucr.is_true('directory/manager/web/delegative-administration/enabled'),
    reason='directory/manager/web/delegative-administration/enabled not activated',
)


@pytest.fixture
def admin_connection(ldap_base):
    """Create admin LDAP connection for testing."""
    connection = uldap.access(
        base=ldap_base,
        binddn=f'cn=admin,{ldap_base}',
        bindpw=open('/etc/ldap.secret').read().strip(),
    )
    return connection


@pytest.fixture
def existing_users(ou, ldap_base):
    """Use existing users created by setup script."""
    return SimpleNamespace(
        base_user_dn=f'uid=ou1admin,cn=users,{ldap_base}',
        base_username='ou1admin',
        ou1_user_dn=f'uid=user1-ou1,cn=users,ou=ou1,{ldap_base}',
        ou1_username='user1-ou1',
        ou2_user_dn=f'uid=user1-ou2,cn=users,ou=ou2,{ldap_base}',
        ou2_username='user1-ou2',
    )


@pytest.fixture
def restricted_user_connection():
    """Create a restricted user connection factory."""
    def _create_connection(user_dn: str, password: str, ldap_base: str):
        lo = uldap.access(
            host=_ucr.get('ldap/master'),
            port=int(_ucr.get('ldap/master/port', '7389')),
            base=ldap_base,
            binddn=user_dn,
            bindpw=password,
            start_tls=2,
        )
        if not lo:
            pytest.fail(f"Failed to create connection for {user_dn}")

        authorized_connection = udm_auth.Authorization.inject_ldap_connection(lo)
        return authorized_connection

    return _create_connection


def create_report_with_auth(connection: uldap.access, objects: list[str], module: str, report_type: str = 'CSV Report') -> bytes:
    """Create a report with authorization handling."""
    report = Report(connection)
    result_file = report.create(module, report_type, objects)

    with open(result_file, 'rb') as f:
        result = f.read()

    try:
        os.unlink(result_file)
    except OSError:
        pass

    return result


def get_report(umc_result):
    file = os.path.join(REPORTS_PATH, umc_result['URL'].split('?report=')[1])
    with open(file) as fh:
        csvfile = csv.reader(fh, delimiter='\t')
        return list(csvfile)


@check_delegation
def test_ou_admin_query_umc(ouadmin_umc_client, admin_umc_client):
    res = ouadmin_umc_client.umc_command('udm/reports/query', {'objectType': 'users/user'}, 'users/user').result
    assert {x['id'] for x in res} == REPORTS
    # no group reports
    res = ouadmin_umc_client.umc_command('udm/reports/query', {'objectType': 'groups/group'}, 'groups/group').result
    assert not res


@check_delegation
def test_ou_admin_query_udm_rest(ouadmin_umc_client, admin_umc_client):
    # TODO: add test
    pass


@check_delegation
def test_ou_admin_filter_objects_udm_rest(ou, ouadmin_umc_client, admin_umc_client, ldap_base):
    # TODO: add test
    pass


@check_delegation
def test_ou_admin_filter_objects_umc(ou, ouadmin_umc_client, admin_umc_client, ldap_base):
    options = {
        'objects': [f'uid=Administrator,cn=users,{ldap_base}', f'uid=user1-ou1,{ou.user_default_container}'],
        'report': 'CSV Report',
    }
    res = ouadmin_umc_client.umc_command('udm/reports/create', options, 'users/user').result
    report = get_report(res)
    assert len(report) == 4, report
    options = {
        'objects': [
            f'uid=user1-ou1,{ou.user_default_container}',
            f'uid=user2-ou1,{ou.user_default_container}',
            f'uid=user3-ou1,{ou.user_default_container}',
            f'uid=user4-ou1,{ou.user_default_container}',
            f'uid=user1-ou2,{ou.user_default_container}',
            f'uid=user2-ou2,{ou.user_default_container}',
            f'uid=user3-ou2,{ou.user_default_container}',
            f'uid=user4-ou2,{ou.user_default_container}',
        ],
        'report': 'CSV Report',
    }
    res = ouadmin_umc_client.umc_command('udm/reports/create', options, 'users/user').result
    report = get_report(res)
    assert len(report) == 7, report


@check_delegation
def test_reports_property_filtering(setup_role, udm, ldap_base):
    role = 'udm:test_roles:test_reports'
    acl = '''
access by role="%s"
to objecttype="users/user"
grant actions="search,read,report-create"
grant properties="*" permission="read"
grant properties="firstname,description" permission="none"
''' % role
    rest, umc = setup_role(acl, role)  # noqa: RUF059
    dn, username = udm.create_user(firstname='firstname', description='description')
    res = umc.umc_command('udm/reports/create', {'objects': [dn], 'report': 'CSV Report'}, 'users/user').result
    report = get_report(res)[2]
    # 'User name', 'Last name', 'First name', 'Description', 'Groups', 'Employee number', 'Employee type', ...
    assert report[0] == username
    assert not report[2]
    assert not report[3]
    # TODO: udm rest


@check_delegation
def test_ou_admin_can_create_reports_for_accessible_objects(ou, ldap_base, restricted_user_connection, existing_users):
    """Test that OU admin can create reports for objects within their scope."""
    user_dn = existing_users.ou1_user_dn
    restricted_conn = restricted_user_connection(ou.admin_dn, ou.admin_password, ldap_base)

    result = create_report_with_auth(restricted_conn, [user_dn], 'users/user')
    assert result is not None
    assert len(result) > 0

    content_str = result.decode('utf-8')
    assert 'User name' in content_str or 'username' in content_str.lower()


@check_delegation
def test_property_filtering_for_restricted_users(ou, ldap_base, restricted_user_connection, existing_users):
    """Test that property filtering works for restricted users."""
    user_dn = existing_users.ou1_user_dn
    restricted_conn = restricted_user_connection(ou.admin_dn, ou.admin_password, ldap_base)

    result = create_report_with_auth(restricted_conn, [user_dn], 'users/user')
    assert result is not None

    content_str = result.decode('utf-8')

    assert 'User name' in content_str or 'username' in content_str.lower()

    if authorization.Authorization.global_enabled:
        restricted_conn.authz.is_report_create_allowed(restricted_conn, 'users/user', 'CSV Report', raise_exception=True)


@check_delegation
def test_mixed_object_filtering_behavior(ou, ldap_base, restricted_user_connection, existing_users):
    """Test filtering behavior with mixed authorized and unauthorized objects."""
    ou1_user_dn = existing_users.ou1_user_dn
    ou2_user_dn = existing_users.ou2_user_dn
    ou2_username = existing_users.ou2_username
    restricted_conn = restricted_user_connection(ou.admin_dn, ou.admin_password, ldap_base)

    report = Report(restricted_conn)
    result_file = report.create('users/user', 'CSV Report', [ou1_user_dn, ou2_user_dn])

    with open(result_file, 'rb') as f:
        content = f.read()

    try:
        os.unlink(result_file)
    except OSError:
        pass

    content_str = content.decode('utf-8')

    ou2_present = ou2_username in content_str
    assert not ou2_present


@check_delegation
def test_property_filtering_demonstration(admin_connection, ldap_base):
    """Test property filtering functionality with admin user."""
    with UCSTestUDM() as udm:
        user_dn, _ = udm.create_user(
            firstname='TestUser',
            lastname='ForFiltering',
            description='Test user for property filtering demonstration',
        )

        admin_report = Report(admin_connection)
        admin_result_file = admin_report.create('users/user', 'CSV Report', [user_dn])

        with open(admin_result_file, 'rb') as f:
            admin_content = f.read().decode('utf-8')

        try:
            os.unlink(admin_result_file)
        except OSError:
            pass

        assert len(admin_content) > 0, "Admin report should not be empty"
        assert 'User name' in admin_content or 'username' in admin_content.lower()

        if authorization.Authorization.global_enabled:
            admin_connection.authz.is_report_create_allowed(admin_connection, 'users/user', 'CSV Report', raise_exception=True)


@check_delegation
def test_available_report_types_for_restricted_user(ou, ldap_base, restricted_user_connection, existing_users):
    """Test which report types (CSV, PDF) a restricted user can see and create."""
    user_dn = existing_users.ou1_user_dn
    restricted_conn = restricted_user_connection(ou.admin_dn, ou.admin_password, ldap_base)

    csv_result = create_report_with_auth(restricted_conn, [user_dn], 'users/user', 'CSV Report')
    assert csv_result is not None
    assert len(csv_result) > 0

    csv_content = csv_result.decode('utf-8')
    assert 'User name' in csv_content or 'username' in csv_content.lower()

    pdf_result = create_report_with_auth(restricted_conn, [user_dn], 'users/user', 'PDF Document')
    assert pdf_result is not None
    assert len(pdf_result) > 0

    assert pdf_result[:4] == b'%PDF'


@check_delegation
def test_report_with_mixed_users_ou_and_administrator(ou, ldap_base, restricted_user_connection, existing_users, admin_connection):
    """Test that when creating a report for OU user + Administrator, restricted user gets filtered results."""
    ou_user_dn = existing_users.ou1_user_dn
    ou_username = existing_users.ou1_username
    restricted_conn = restricted_user_connection(ou.admin_dn, ou.admin_password, ldap_base)

    admin_dn = f'uid=Administrator,cn=users,{ldap_base}'

    result = create_report_with_auth(restricted_conn, [ou_user_dn, admin_dn], 'users/user', 'CSV Report')
    assert result is not None

    content_str = result.decode('utf-8')

    assert ou_username not in content_str
    assert 'Administrator' not in content_str

    lines = [line.strip() for line in content_str.strip().split('\n') if line.strip()]

    assert len(lines) >= 1

    header_line = lines[0]
    assert 'User name' in header_line or 'username' in header_line.lower()

    data_lines = [line for line in lines[1:] if line.strip() and (ou_username in line or 'Administrator' in line)]
    assert len(data_lines) == 0
