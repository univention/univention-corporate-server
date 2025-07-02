#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check linux-client-manager role in UDM-REST
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import locale
from types import SimpleNamespace

import pytest
import requests

from univention.admin.rest.client import UDM as UDM_REST, Forbidden, UnprocessableEntity
from univention.config_registry import ucr as _ucr
from univention.testing import utils
from univention.testing.strings import random_ip


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='directory/manager/rest/delegative-administration/enabled not activated')


TRANSLATIONS = {
    'de_DE': {
        'Insufficient privileges': 'Unzureichende Berechtigung',
        'Permission denied': 'Zugriff verweigert',
        'No such object': 'Das Objekt existiert nicht',
    },
}


def _(string: str) -> str:
    code, _ = locale.getlocale()
    return TRANSLATIONS.get(code, {}).get(string, string)


def create_udm_rest_client(username):
    """Create UDM-REST client for the given username."""
    return UDM_REST(
        'https://%(hostname)s.%(domainname)s/univention/udm/' % _ucr,
        username=username,
        password=utils.UCSTestDomainAdminCredentials().bindpw,
    )


def make_udm_rest_request(method, object_type, object_dn, username, body=None):
    """
    Make direct UDM-REST HTTP request.

    Args:
        method: HTTP method ('GET', 'PATCH', 'DELETE', etc.)
        object_type: UDM object type (e.g., 'computers/linux')
        object_dn: Distinguished name of the object
        username: Username for authentication
        body: Request body (dict) for PATCH/PUT requests

    Returns:
        requests.Response object
    """
    url = f'https://{_ucr["hostname"]}.{_ucr["domainname"]}/univention/udm/{object_type}/{object_dn}'

    auth = (username, utils.UCSTestDomainAdminCredentials().bindpw)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    return requests.request(
        method,
        url,
        json=body,
        auth=auth,
        headers=headers,
        verify=False,
    )


@pytest.fixture
def ou(ldap_base):
    return SimpleNamespace(
        dn=f'ou=ou1,{ldap_base}',
        client_manager_username='ou1-clientmanager',
        client_manager_dn=f'uid=ou1-clientmanager,cn=users,{ldap_base}',
        computer_default_container=f'cn=computers,ou=ou1,{ldap_base}',
        admin_username='ou1-admin',
        admin_dn=f'uid=ou1-admin,cn=users,{ldap_base}',
    )


@pytest.fixture
def linux_client_manager_user(ou, ldap_base):
    """Get the existing linux client manager user created by setup script."""
    return f'uid={ou.client_manager_username},cn=users,{ldap_base}'


@pytest.fixture
def test_computer_in_ou(ou, udm, random_username):
    """Create a test computer in the OU for testing read/modify/delete operations."""
    computer_name = f'testlinux-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou.dn}',
    )
    return computer_dn


@pytest.fixture
def test_computer_at_base(ldap_base, udm, random_username):
    """Create a test computer at base level for testing cross-OU access denial."""
    computer_name = f'testlinux-base-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ldap_base}',
    )
    return computer_dn


@pytest.fixture
def test_group_in_ou(ou, udm, random_username):
    """Create a test group in the OU for testing group membership operations."""
    group_name = f'testgroup-{random_username()}'
    group_dn = udm.create_object(
        'groups/group',
        name=group_name,
        position=f'cn=groups,{ou.dn}',
    )
    return group_dn


@pytest.fixture
def test_group_at_base(ldap_base, udm, random_username):
    """Create a test group at base level for testing cross-OU group access denial."""
    group_name = f'testgroup-base-{random_username()}'
    group_dn = udm.create_object(
        'groups/group',
        name=group_name,
        position=f'cn=groups,{ldap_base}',
    )
    return group_dn


@check_delegation
def test_linux_client_read_allowed(ou, test_computer_in_ou):
    """Test that linux client manager can read computers in their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    computer = computers_module.get(test_computer_in_ou)
    assert computer
    assert computer.dn == test_computer_in_ou
    assert 'name' in computer.properties
    assert 'ip' in computer.properties


@check_delegation
def test_linux_client_read_denied_cross_ou(ou, test_computer_at_base):
    """Test that linux client manager cannot read computers outside their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    with pytest.raises(UnprocessableEntity):
        computers_module.get(test_computer_at_base)


@check_delegation
def test_linux_client_search_scope(ou, test_computer_in_ou, test_computer_at_base, udm):
    """Test that linux client manager can only search computers in their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    # Test 1: Global search should be restricted
    computers = list(computers_module.search())
    found_dns = {computer.dn for computer in computers}

    # Global search should be restricted
    assert found_dns == {x[0] for x in udm.list_objects('computers/linux', properties=["DN"], position=ou.dn)}

    # Test 2: Direct access to computer in OU should work
    computer = computers_module.get(test_computer_in_ou)
    assert computer.dn == test_computer_in_ou

    # Test 3: Cannot access computers outside OU
    with pytest.raises(UnprocessableEntity):
        computers_module.get(test_computer_at_base)


@check_delegation
def test_linux_client_modify_allowed(ou, test_computer_in_ou):
    """Test that linux client manager can modify computers in their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    computer = computers_module.get(test_computer_in_ou)
    computer.properties['description'] = 'Modified by linux client manager via UDM-REST'
    computer.save()

    computer.reload()
    assert computer.properties['description'] == 'Modified by linux client manager via UDM-REST'


@check_delegation
def test_linux_client_modify_denied_cross_ou(ou, test_computer_at_base):
    """
    Test that linux client manager cannot modify computers outside their OU via UDM-REST.

    Uses direct HTTP request instead of UDM-REST client because computers_module.get()
    is expected to fail for cross-OU computers that the user doesn't have access to.
    This approach directly tests the password modification operation without requiring
    the object to be retrieved first.
    """
    body = {
        "properties": {
            "password": "shouldnotwork",
        },
    }

    response = make_udm_rest_request(
        'PATCH',
        'computers/linux',
        test_computer_at_base,
        ou.client_manager_username,
        body,
    )

    assert response.status_code == 404


@check_delegation
def test_linux_client_create_computer_allowed(ou, random_username):
    """Test that linux client manager can create new computers in their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    computer_name = f'new-linux-{random_username()}'
    unique_ip = random_ip()

    computer = computers_module.new(position=ou.computer_default_container)
    computer.properties['name'] = computer_name
    computer.properties['ip'] = [unique_ip]
    computer.properties['unixhome'] = '/dev/null'
    computer.properties['shell'] = '/bin/bash'
    computer.save()

    assert computer.dn
    assert computer_name in computer.dn
    assert ou.dn in computer.dn

    # Cleanup
    computer.delete()


@check_delegation
def test_linux_client_create_computer_denied_cross_ou(ou, ldap_base, udm, random_username):
    """Test that linux client manager cannot create computers outside their OU via UDM-REST."""
    ou2_dn = f'ou=ou2,{ldap_base}'

    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    computer_name = f'denied-linux-{random_username()}'
    unique_ip = random_ip()

    computer = computers_module.new(position=f'cn=computers,{ou2_dn}')
    computer.properties['name'] = computer_name
    computer.properties['ip'] = [unique_ip]
    computer.properties['unixhome'] = '/dev/null'
    computer.properties['shell'] = '/bin/bash'

    with pytest.raises(Forbidden):
        computer.save()


@check_delegation
def test_linux_client_delete_allowed(ou, udm, random_username):
    """Test that linux client manager can delete computers in their OU via UDM-REST."""
    computer_name = f'delete-test-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou.dn}',
    )

    udm_rest = create_udm_rest_client(ou.client_manager_username)
    computers_module = udm_rest.get('computers/linux')

    computer = computers_module.get(computer_dn)
    computer.delete()

    computers = list(computers_module.search(f'name={computer_name}'))
    assert computers == []


@check_delegation
def test_linux_client_delete_denied_cross_ou(ou, test_computer_at_base):
    """
    Test that linux client manager cannot delete computers outside their OU via UDM-REST.

    Uses direct HTTP request instead of UDM-REST client because computers_module.get()
    is expected to fail for cross-OU computers that the user doesn't have access to.
    This approach directly tests the delete operation without requiring
    the object to be retrieved first.
    """
    response = make_udm_rest_request(
        'DELETE',
        'computers/linux',
        test_computer_at_base,
        ou.client_manager_username,
    )

    assert response.status_code == 404


@check_delegation
def test_linux_client_manager_can_access_groups_in_ou(ou, test_group_in_ou):
    """Test that linux client manager can access group objects within their OU via UDM-REST (OU-specific security model)."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    groups_module = udm_rest.get('groups/group')

    group = groups_module.get(test_group_in_ou)
    assert group.dn == test_group_in_ou
    assert 'name' in group.properties


@check_delegation
def test_linux_client_manager_cannot_access_base_level_groups(ou, test_group_at_base):
    """Test that linux client manager cannot access base-level groups via UDM-REST (security improvement)."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    groups_module = udm_rest.get('groups/group')

    # Should not be able to access base-level groups anymore
    with pytest.raises(UnprocessableEntity):
        groups_module.get(test_group_at_base)


@check_delegation
def test_linux_client_manager_can_modify_group_memberships_in_ou(ou, test_computer_in_ou, test_group_in_ou):
    """Test that linux client manager can modify group memberships for groups within their OU via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)
    groups_module = udm_rest.get('groups/group')

    group = groups_module.get(test_group_in_ou)
    current_hosts = group.properties.get('hosts', [])
    group.properties['hosts'] = [*current_hosts, test_computer_in_ou]
    group.save()

    group.reload()
    assert test_computer_in_ou in group.properties.get('hosts', [])


@check_delegation
def test_linux_client_manager_cannot_access_users(ou, udm, random_username):
    """Test that linux client manager cannot access user objects via UDM-REST."""
    user_dn = udm.create_object(
        'users/user',
        username=f'testuser-{random_username()}',
        lastname='TestUser',
        password='univention',
        position=f'cn=users,{ou.dn}',
    )

    udm_rest = create_udm_rest_client(ou.client_manager_username)
    users_module = udm_rest.get('users/user')

    with pytest.raises(UnprocessableEntity):
        users_module.get(user_dn)

    user = users_module.new(position=f'cn=users,{ou.dn}')
    user.properties['username'] = f'newuser-{random_username()}'
    user.properties['lastname'] = 'TestUser'
    user.properties['password'] = 'univention'

    with pytest.raises(Forbidden):
        user.save()


@check_delegation
def test_linux_client_manager_cannot_access_global_features(ou):
    """Test that linux client manager cannot access global system administration features via UDM-REST."""
    udm_rest = create_udm_rest_client(ou.client_manager_username)

    # Test mail domain access
    mail_module = udm_rest.get('mail/domain')
    mail_domains = list(mail_module.search())
    assert mail_domains == []

    # Test DNS zone access
    dns_module = udm_rest.get('dns/forward_zone')
    dns_zones = list(dns_module.search())
    assert dns_zones == []

    # Test policy access
    policy_types = ['policies/desktop', 'policies/pwhistory', 'policies/umc']
    for policy_type in policy_types:
        policy_module = udm_rest.get(policy_type)
        policies = list(policy_module.search())
        assert policies == []
