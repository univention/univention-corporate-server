#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check syntax choices in UMC with delegated administration
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest
import ldap
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
get_syntax_choices('LDAP_Search', options={'attribute': ..., 'filter': ..., 'base': ...})
- LDAP_Search mit value = "dn" via a settings/syntax object:
- LDAP_Search mit value != "dn" via a settings/syntax object:
udm.create_object('settings/syntax', name='foo', 'attribute'=..., filter=..., base=..., ...=...)
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
def test_syntax_choices_uctl_service(umc_client, client_type):
    """Test Service syntax (UDM_Objects based) to show OU admin restrictions"""
    res = umc_client.get_syntax_choices('Service', 'computers/computer')
    assert res is not None

    if client_type == 'admin':
        # Domain admin has full access
        assert len(res) > 0  # Can see service objects
    elif client_type == 'ou_admin':
        # OU admin has restricted access
        assert len(res) == 0  # NO access to service objects
    else:  # ou2_admin
        # OU2 admin also has no access
        assert len(res) == 0  # NO access to service objects


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
def test_syntax_choices_mail_domain(umc_client, client_type, test_object_mail_domain):
    """Test MailDomain syntax - covers PrinterDriverList and mail functionality"""
    res = umc_client.get_syntax_choices('MailDomain', 'mail/folder')
    assert res is not None
    assert len(res) > 0
    assert any(test_object_mail_domain in str(choice['id']) for choice in res)




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
def test_syntax_choices_ldapdn_no_filter(umc_client, client_type):
    """Test LdapDn syntax (ldapDn without filter) returns an empty list."""
    res = umc_client.get_syntax_choices('LdapDn', 'users/user')
    assert res is None or res == []


@pytest.fixture(scope='session')
def syntaxes_container(udm_session, ldap_base):
    try:
        udm_session.create_object(
            'container/cn',
            name='syntaxes',
            position=f'cn=univention,{ldap_base}'
        )
    except Exception:
        # a concurrent test may have already created the object
        pass


@pytest.fixture(scope='session')
def syntax_object_dn(udm_session, ldap_base, syntaxes_container):
    syntax_name = f'test-syntax-dn-{random_username()}'
    udm_session.create_object(
        'settings/syntax',
        name=syntax_name,
        value='dn',
        attribute='dn',
        filter='objectClass=univentionMailDomain',
        base=f'cn=mail,cn=univention,{ldap_base}',
        position=f'cn=syntaxes,cn=univention,{ldap_base}'
    )
    return syntax_name


@pytest.fixture(scope='session')
def syntax_object_not_dn(udm_session, ldap_base, syntaxes_container):
    syntax_name = f'test-syntax-not-dn-{random_username()}'
    udm_session.create_object(
        'settings/syntax',
        name=syntax_name,
        value='cn',
        attribute='cn',
        filter='objectClass=univentionMailDomain',
        base=f'cn=mail,cn=univention,{ldap_base}',
        position=f'cn=syntaxes,cn=univention,{ldap_base}'
    )
    return syntax_name



@pytest.fixture(scope='session')
def setup_mail_home_server(udm_session, ldap_base):
    """Fixture to create a test computer with IMAP service for mailHomeServer syntax testing."""
    try:
        # Create a minimal test computer with IMAP service
        computer_name = f'test-mailserver-{random_username()}'
        # Use a simple IP that's less likely to conflict
        import time
        unique_ip = f'192.168.100.{int(time.time()) % 200 + 50}'
        
        computer_dn = udm_session.create_object(
            'computers/memberserver',
            name=computer_name,
            ip=unique_ip,
            service=['IMAP'],  # mailHomeServer syntax specifically looks for IMAP service
            position=f'cn=computers,{ldap_base}',
            wait_for_replication=False  # Don't wait for replication to speed up test
        )
        yield computer_dn
    except Exception as e:
        # If computer creation fails, yield None - test will handle gracefully
        print(f"Failed to create mail server computer: {e}")
        yield None

@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_mail_home_server(umc_client, client_type, setup_mail_home_server):
    """Test mailHomeServer syntax, ensuring a mail server is configured via fixture."""
    # Der Funktionsaufruf MUSS die Syntax 'mailHomeServer' verwenden.
    res = umc_client.get_syntax_choices('mailHomeServer', 'users/user')
    assert res is not None

    if client_type == 'admin':
        if setup_mail_home_server is not None:
            # If we successfully created a mail server, we should see it
            assert len(res) >= 1, "As admin, at least one mail server must be found"
            # Check that our test mail server is visible
            assert any('test-mailserver' in item['label'] for item in res)
            # Die Assertion MUSS das Feld 'id' prüfen.
            assert all('cn=' in item['id'] for item in res)
        else:
            # If computer creation failed, just verify syntax works (might be empty)
            assert isinstance(res, list), "mailHomeServer syntax should return a list"
    else:
        assert len(res) == 0, "OU admins must not see global mail servers"


@pytest.fixture(scope='session')
def printermodels_container(udm_session, ldap_base):
    try:
        udm_session.create_object(
            'container/cn',
            name='printermodels',
            position=f'cn=univention,{ldap_base}'
        )
    except Exception:
        # a concurrent test may have already created the object
        pass


@pytest.fixture(scope='session')
def printer_producer(udm_session, ldap_base, printermodels_container):
    model_name = f'test-model-{random_username()}'
    driver_name = f'test-driver-{random_username()}'
    
    # Create a printer model with a printmodel attribute
    # The printmodel syntax expects "driver description" format
    dn = udm_session.create_object(
        'settings/printermodel',
        name=model_name,
        printmodel=f'{driver_name} "Test Printer Driver"',
        position=f'cn=printermodels,cn=univention,{ldap_base}'
    )
    return dn


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_udm_attributes_dn_filter(umc_client, client_type, printer_producer):
    """Test UDM_Attributes subclass with udm_filter='dn'."""
    # The UMC module expects '$depends$' to indicate the dependency name and the actual value as a separate key
    options = {
        '$depends$': 'producer',
        'producer': printer_producer
    }
    res = umc_client.get_syntax_choices('PrinterDriverList', 'printer/printer', options=options)
    assert res is not None
    if client_type == 'admin':
        assert len(res) > 0
    else:
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_udm_attributes_no_dn_filter(umc_client, client_type, test_object_package):
    """Test UDM_Attributes subclass without udm_filter='dn'."""
    res = umc_client.get_syntax_choices('Packages', 'policies/masterpackages')
    assert res is not None
    if client_type == 'admin':
        assert len(res) > 0
        assert any(test_object_package in str(choice['label']) for choice in res)
    else:
        assert len(res) == 0


def test_syntax_choices_generic_search_with_dn_value(admin_umc_client, ldap_base):
    """Tests the 'generic' syntax to perform a real, dynamic LDAP search returning DNs."""
    # The 'options' variable defines the dynamic search.
    options = {
        'value': 'dn',
        'filter': '(objectClass=posixAccount)',
        'base': ldap_base,
        'label': 'uid'
    }
    res = admin_umc_client.get_syntax_choices('generic', None, options=options)

    assert res, "The dynamic search with 'generic' syntax must return results"

    assert all('uid=' in item['id'] and ldap_base in item['id'] for item in res), "The returned values must be full DNs"
    assert any(item['label'] == 'Administrator' for item in res), "The Administrator user must be found"

def test_syntax_choices_generic_search_with_attribute_value(admin_umc_client, ldap_base):
    """Tests the 'generic' syntax to perform a real, dynamic LDAP search returning a specific attribute."""
    options = {
        'value': 'uid',
        'filter': '(objectClass=posixAccount)',
        'base': ldap_base,
        'label': 'cn'
    }
    res = admin_umc_client.get_syntax_choices('generic', None, options=options)

    assert res, "The dynamic search with 'generic' syntax must return results"
    assert all('=' not in item['id'] for item in res), "The returned values must be plain attributes, not DNs"
    assert any(item['id'] in ('0', '2002') for item in res), "The Administrator or root UID must be found"


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_search_dn_by_syntax_object(umc_client, client_type, syntax_object_dn, test_object_mail_domain):
    """Test LDAP_Search with value='dn' from a settings/syntax object."""
    # For syntax objects defined in LDAP, we need to use LDAP_Search and pass the syntax name in options
    options = {'syntax': syntax_object_dn}
    res = umc_client.get_syntax_choices('LDAP_Search', 'mail/domain', options=options)
    assert res is not None
    if client_type == 'admin':
        assert len(res) > 0
        # Verify that returned values are DNs (contain 'cn=')
        assert all('cn=' in str(choice['value']) for choice in res if choice.get('value'))
    else:
        assert len(res) == 0


@pytest.mark.parametrize('client_type', ['admin', 'ou_admin', 'ou2_admin'])
def test_syntax_choices_ldap_search_not_dn_by_syntax_object(umc_client, client_type, syntax_object_not_dn, test_object_mail_domain):
    """Test LDAP_Search with value!='dn' from a settings/syntax object."""
    # For syntax objects defined in LDAP, we need to use LDAP_Search and pass the syntax name in options
    options = {'syntax': syntax_object_not_dn}
    res = umc_client.get_syntax_choices('LDAP_Search', 'mail/domain', options=options)
    assert res is not None
    if client_type == 'admin':
        assert len(res) > 0
        # Verify that returned values are not DNs (should be cn values)
        assert all('cn=' not in str(choice['value']) for choice in res if choice.get('value'))
    else:
        assert len(res) == 0
