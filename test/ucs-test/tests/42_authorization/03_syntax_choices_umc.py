#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check syntax choices in UMC with delegated administration
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous


import pytest
from conftest import ClientHelper

from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_username


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')

"""
## ldapDN
- without searchFilter: LdapDn
- with searchFilter: primaryGroup

## UDM_Attribute
- without udm_filter: Packages, MailDomain
- with udm_filter=dn: PrinterDriverList

## UDM_Objects
| use_objects | udm_filter | udm_module with lookup_filter | mapping of the attribute specified in .key | names |
| :-----:  | :-----:  | :-----: | :-----: | :-----: |
| False | False |  False  | ???   | UserDN, UserID, UserName, GroupDN, GroupID, GroupName
| True  | True  |  False  | ???   | HostDN
| True  | False |  True   | True  | Service
| True  | True  |  True   |


- LDAP_Search mit value = "dn" via given parameters in get-syntax-choices request: LDAP_Search
- LDAP_Search mit value != "dn" via given parameters in get-syntax-choices request: LDAP_Search
get_syntax_choices('LDAP_Search', options={'attribute': …, 'filter': …, 'base': …})
- LDAP_Search mit value = "dn" via a settings/syntax object:
- LDAP_Search mit value != "dn" via a settings/syntax object:
udm.create_object('settings/syntax', name='foo', 'attribute'=…, filter=…, base=…, …=…)
get_syntax_choices('foo')
- static subclass of LDAP_Search mit value = "dn": mailHomeServer


- IComputer_FQDN based: UCS_Server
- emailAddressValidDomain
"""


def get_umc_client(client_type, ou=None):
    """Create a UMC client for the specified client type and organizational unit"""
    client = ClientHelper()
    if client_type == 'admin':
        client = ClientHelper.get_test_connection()
    elif client_type == 'ou_admin':
        client.authenticate(ou.admin_username, 'univention')
    elif client_type == 'ou2_admin':
        client.authenticate('ou2-admin', 'univention')
    return client


@pytest.fixture(scope='session')
def umc_clients(ou):
    """Create all UMC clients once per session"""
    return {
        'admin': get_umc_client('admin'),
        'ou_admin': get_umc_client('ou_admin', ou),
        'ou2_admin': get_umc_client('ou2_admin'),
    }


@pytest.fixture
def umc_client(client_type, umc_clients):
    """Get the appropriate UMC client based on client_type parameter"""
    return umc_clients[client_type]


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
@pytest.mark.parametrize('dn_id', ['UserDN', 'UserID', 'UserName'])
def test_syntax_choices_user_dn(umc_client, client_type, udm_session, ou, dn_id):
    """Test UserDN syntax choices for all admin types"""
    res = umc_client.get_syntax_choices(dn_id, 'users/user')
    assert res

    root_user_count = 1 if dn_id == 'UserID' else 0
    if client_type == 'admin':
        # Domain admin should see all users
        total_users = len(udm_session.list_objects('users/user', properties=['DN'])) + root_user_count
        assert len(res) == total_users
        assert any(ou.user_username in str(choice['label']) for choice in res)
        assert any(ou.user2_username in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see users from OU1 + admin users
        ou1_users = len(udm_session.list_objects('users/user', properties=['DN'], position=ou.dn)) + root_user_count + 1  # +1 for ou_admin
        assert len(res) == ou1_users
        assert any(ou.user_username in choice['label'] for choice in res)
        assert not any(ou.user2_username in str(choice['label']) for choice in res)
    else:  # ou2_admin
        # OU2 admin should see users from OU2 + admin users
        ou2_users = len(udm_session.list_objects('users/user', properties=['DN'], position=ou.dn2)) + root_user_count + 1  # +1 for ou2_admin
        assert len(res) == ou2_users
        assert any(ou.user2_username in choice['label'] for choice in res)
        assert not any(ou.user_username in str(choice['label']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
@pytest.mark.parametrize('dn_id', ['GroupDN', 'GroupID', 'GroupName'])
def test_syntax_choices_group_dn(umc_client, client_type, udm_session, ou, dn_id):
    """Test GroupDN syntax choices for all admin types"""
    res = umc_client.get_syntax_choices(dn_id, 'groups/group')
    assert res

    root_group_count = 1 if dn_id == 'GroupID' else 0

    if client_type == 'admin':
        # Domain admin should see all groups
        total_groups = len(udm_session.list_objects('groups/group', properties=['DN'])) + root_group_count
        assert len(res) == total_groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see groups from OU1
        ou1_groups = len(udm_session.list_objects('groups/group', properties=['DN'], position=ou.dn)) + root_group_count
        assert len(res) == ou1_groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert not any(ou.group_name2 in str(choice['label']) for choice in res)
    else:  # ou2_admin
        # OU2 admin should see groups from OU2
        ou2_groups = len(udm_session.list_objects('groups/group', properties=['DN'], position=ou.dn2)) + root_group_count
        assert len(res) == ou2_groups
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
        assert not any(ou.group_name in str(choice['label']) for choice in res)


@pytest.fixture(scope='session')
def test_object_package(ldap_base, udm_session):
    package_name = f'test-package-{random_username()}'
    udm_session.create_object(
        'settings/packages',
        name=package_name,
        packageList=['test-package1', 'test-package2'],
        position=f'cn=packages,cn=univention,{ldap_base}',
    )
    return package_name


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_packages(umc_client, client_type, udm_session, test_object_package):
    """Test Packages syntax (UDM_Attribute based) for all admin types"""
    res = umc_client.get_syntax_choices('Packages', 'policies/masterpackages')
    if client_type == 'admin':
        assert len(res) > 0
        # Check that our created package object is visible
        assert any(test_object_package in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        assert len(res) == 0
    elif client_type == 'ou2_admin':
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_kde_profile(umc_client, client_type):
    """Test KDE_Profile syntax (UDM_Attribute based) for all admin types"""
    res = umc_client.get_syntax_choices('KDE_Profile', 'policies/desktop')
    assert res == []


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ucs_server(umc_client, client_type):
    res = umc_client.get_syntax_choices('UCS_Server', 'shares/share')
    assert res is not None
    if client_type == 'admin':
        assert len(res) > 0
        assert any(_ucr.get('hostname') in str(choice['label']) for choice in res)
    else:
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_network(umc_client, client_type):
    """Test network syntax for all admin types"""
    res = umc_client.get_syntax_choices('network', 'computers/computer')
    assert res
    # Network syntax should return network objects
    # Just verify we get some results back (could be empty or contain default network)
    assert isinstance(res, list)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_mail_home_server(umc_client, client_type):
    """Test mailHomeServer syntax (UDM_Objects based) for all admin types"""
    res = umc_client.get_syntax_choices('mailHomeServer', 'computers/computer')
    assert res is not None

    if client_type == 'admin':
        # Domain admin should see mail home servers
        assert len(res) > 0
        assert any(_ucr.get('hostname') in str(choice['label']) for choice in res)
    else:
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_service_mail(umc_client, client_type):
    """Test ServiceMail syntax (UDM_Objects based) for all admin types"""
    res = umc_client.get_syntax_choices('ServiceMail', 'mail/folder')
    assert res == []


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_network_type(umc_client, client_type):
    """Test NetworkType syntax (select-based) for all admin types"""
    res = umc_client.get_syntax_choices('NetworkType', 'computers/computer')
    assert res
    assert any('ethernet' in str(choice['id']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ip_protocol(umc_client, client_type):
    """Test ipProtocol syntax (select-based) for all admin types"""
    res = umc_client.get_syntax_choices('ipProtocol', 'settings/portal_entry')
    assert res
    assert any('tcp' in str(choice['id']) for choice in res)


@pytest.fixture(scope='session')
def test_object_service(ou, ldap_base, udm_session):
    # Create service object for Service syntax testing
    service_name = f'test-service-{random_username()}'
    udm_session.create_object(
        'settings/service',
        name=service_name,
        position=f'cn=services,cn=univention,{ldap_base}',
    )
    return service_name


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_service(umc_client, client_type, test_object_service):
    """Test Service syntax for all admin types"""
    res = umc_client.get_syntax_choices('Service', 'computers/computer')
    assert res is not None
    if client_type == 'admin':
        assert any(test_object_service in str(choice['label']) for choice in res)
    else:
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_primary_group(umc_client, client_type, udm_session, ou):
    """Test primaryGroup syntax (ldapDn with filter) for all admin types"""
    res = umc_client.get_syntax_choices('primaryGroup', 'users/user')
    assert res

    if client_type == 'admin':
        # Domain admin should see all posix groups
        total_groups = len(udm_session.list_objects('groups/group', properties=['DN'], filter='objectClass=posixGroup'))
        assert len(res) >= total_groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see groups from OU1
        ou1_groups = len(udm_session.list_objects('groups/group', properties=['DN'], position=ou.dn, filter='objectClass=posixGroup'))
        assert len(res) >= ou1_groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        # May also see some global groups, so we don't assert that ou.group_name2 is NOT present
    else:  # ou2_admin
        # OU2 admin should see groups from OU2
        ou2_groups = len(udm_session.list_objects('groups/group', properties=['DN'], position=ou.dn2, filter='objectClass=posixGroup'))
        assert len(res) >= ou2_groups
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
        # May also see some global groups, so we don't assert that ou.group_name is NOT present


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_non_existent_syntax(umc_client, client_type):
    """Test edge case: non-existent syntax"""
    res = umc_client.get_syntax_choices('NonExistentSyntax', 'users/user')
    assert res is None


def test_syntax_choices_empty_syntax_name(admin_umc_client):
    """Test edge case: empty syntax name"""
    res = admin_umc_client.get_syntax_choices('', 'users/user')
    assert res is None


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_host_dn(umc_client, client_type):
    """Test HostDN syntax choices for all admin types"""
    res = umc_client.get_syntax_choices('HostDN', 'computers/computer')
    assert res is not None

    if client_type == 'admin':
        # Domain admin should see computer objects
        assert len(res) >= 1
        # Check that our test computer is visible
        assert any(_ucr.get('hostname') in str(choice['label']) for choice in res)
    else:
        # OU admins might have limited access to computer objects
        # Just verify we get a list back (could be empty)
        assert isinstance(res, list)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_dn(umc_client, client_type, ou, ldap_base):
    """Test custom ldapDN syntax choices for all admin types"""
    # Use UserDN syntax for testing authorization with user objects
    res = umc_client.get_syntax_choices('ldapDN', 'users/user', options={'attribute': 'dn', 'value': 'dn', 'base': ldap_base})
    assert res is not None

    if client_type == 'admin':
        # Domain admin should see all users matching the filter
        assert len(res) >= 2  # At least the test users
        assert any(ou.user_username in str(choice['label']) for choice in res)
        assert any(ou.user2_username in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see users from OU1
        assert len(res) >= 1
        assert any(ou.user_username in str(choice['label']) for choice in res)
        assert not any(ou.user2_username in str(choice['label']) for choice in res)
    else:  # ou2_admin
        # OU2 admin should see users from OU2
        assert len(res) >= 1
        assert any(ou.user2_username in str(choice['label']) for choice in res)
        assert not any(ou.user_username in str(choice['label']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_search(umc_client, client_type, udm_session, ou):
    """Test custom LDAP_Search syntax choices for all admin types"""
    # Use GroupDN syntax for testing authorization with group objects
    res = umc_client.get_syntax_choices('LDAP_Search', 'groups/group', options={'value': 'dn'})
    assert res is not None

    if client_type == 'admin':
        # Domain admin should see all groups matching the filter
        assert len(res) >= 2  # At least the test groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see groups from OU1
        assert len(res) >= 1
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert not any(ou.group_name2 in str(choice['label']) for choice in res)
    else:  # ou2_admin
        # OU2 admin should see groups from OU2
        assert len(res) >= 1
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
        assert not any(ou.group_name in str(choice['label']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_search_using_object(umc_client, client_type, udm_session, ou, ldap_base):
    syntax_name = random_username()
    udm_session.create_object(
        'settings/syntax',
        name=syntax_name,
        attribute=['dn'],
        base=ldap_base,
        position=f'cn=custom attributes,cn=univention,{ldap_base}',
        filter='(objectClass=*)',
        viewonly='TRUE',
        value='dn',
    )
    res = umc_client.get_syntax_choices(syntax_name, 'groups/group')
    assert res is not None

    if client_type == 'admin':
        # Domain admin should see all groups matching the filter
        assert len(res) >= 2  # At least the test groups
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
    elif client_type == 'ou_admin':
        # OU1 admin should see groups from OU1
        assert len(res) >= 1
        assert any(ou.group_name in str(choice['label']) for choice in res)
        assert not any(ou.group_name2 in str(choice['label']) for choice in res)
    else:  # ou2_admin
        # OU2 admin should see groups from OU2
        assert len(res) >= 1
        assert any(ou.group_name2 in str(choice['label']) for choice in res)
        assert not any(ou.group_name in str(choice['label']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_server(umc_client, client_type, ou):
    """Test custom LDAP_Server syntax choices for all admin types"""
    res = umc_client.get_syntax_choices('LDAP_Server', 'computers/domaincontroller_master')
    assert res is not None

    if client_type == 'admin':
        assert len(res) >= 1
        assert any(_ucr.get('hostname') in str(choice['label']) for choice in res)
    else:
        assert len(res) == 0


@pytest.fixture(scope='session')
def test_object_mail_domain(ldap_base, udm_session):
    mail_domain = f'{random_username()}.test'
    udm_session.create_object(
        'mail/domain',
        name=mail_domain,
        position=f'cn=domain,cn=mail,{ldap_base}',
    )
    return mail_domain


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_mail_domain(umc_client, client_type, test_object_mail_domain):
    res = umc_client.get_syntax_choices('MailDomain', 'mail/folder')
    assert res is not None
    assert len(res) >= 1
    assert any(test_object_mail_domain in str(choice['id']) for choice in res)


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_email_address_valid_domain(umc_client, client_type, test_object_mail_domain):
    """Test email address syntax choices for valid domain"""
    res = umc_client.get_syntax_choices('emailAddressValidDomain', 'mail/domain')
    assert res is not None
    assert len(res) >= 1
    assert any(test_object_mail_domain in str(choice['label']) for choice in res)


@pytest.fixture(scope='session')
def test_object_printer_driver(ldap_base, udm_session):
    # Create service object for Service syntax testing
    service_name = f'test-service-{random_username()}'
    udm_session.create_object(
        'settings/service',
        name=service_name,
        position=ldap_base,
    )
    return service_name


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_printer_driver_list(umc_client, client_type, udm_session, ldap_base, test_object_printer_driver):
    """Test PrinterDriverList syntax choices for all admin types"""
    res = umc_client.get_syntax_choices('PrinterDriverList', 'settings/printermodel')
    assert res is not None
    assert len(res) >= 1
    assert any(test_object_printer_driver in str(choice['label']) for choice in res)
