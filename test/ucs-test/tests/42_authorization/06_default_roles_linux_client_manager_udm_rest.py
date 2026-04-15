#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check linux-client-manager role in UDM-REST
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest
import requests

from univention.admin.rest.client import Forbidden, UnprocessableEntity
from univention.config_registry import ucr as _ucr
from univention.testing import utils
from univention.testing.strings import random_ip


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='directory/manager/rest/delegative-administration/enabled not activated')


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
        verify=False,  # noqa: S501
    )


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
def test_linux_client_read_allowed(linux_client_manager_rest_client, test_computer_in_ou):
    """Test that linux client manager can read computers in their OU via UDM-REST."""
    computer = linux_client_manager_rest_client.get_object('computers/linux', test_computer_in_ou)
    assert computer
    assert computer.dn == test_computer_in_ou
    assert 'name' in computer.properties
    assert 'ip' in computer.properties


@check_delegation
def test_linux_client_read_denied_cross_ou(linux_client_manager_rest_client, test_computer_at_base):
    """Test that linux client manager cannot read computers outside their OU via UDM-REST."""
    with pytest.raises(UnprocessableEntity):
        linux_client_manager_rest_client.get_object('computers/linux', test_computer_at_base)


@check_delegation
def test_linux_client_search_scope(linux_client_manager_rest_client, ou, test_computer_in_ou, test_computer_at_base, udm):
    """Test that linux client manager can only search computers in their OU via UDM-REST."""
    # Test 1: Global search should be restricted
    computers = linux_client_manager_rest_client.search_objects('computers/linux')
    found_dns = {computer.dn for computer in computers}

    # Global search should be restricted
    assert found_dns == {x[0] for x in udm.list_objects('computers/linux', properties=["DN"], position=ou.dn)}

    # Test 2: Direct access to computer in OU should work
    computer = linux_client_manager_rest_client.get_object('computers/linux', test_computer_in_ou)
    assert computer.dn == test_computer_in_ou

    # Test 3: Cannot access computers outside OU
    with pytest.raises(UnprocessableEntity):
        linux_client_manager_rest_client.get_object('computers/linux', test_computer_at_base)


@check_delegation
def test_linux_client_modify_allowed(linux_client_manager_rest_client, test_computer_in_ou):
    """Test that linux client manager can modify computers in their OU via UDM-REST."""
    computer = linux_client_manager_rest_client.modify_object('computers/linux', test_computer_in_ou, {
        'description': 'Modified by linux client manager via UDM-REST',
    })

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
def test_linux_client_create_computer_allowed(linux_client_manager_rest_client, ou, random_username):
    """Test that linux client manager can create new computers in their OU via UDM-REST."""
    computer_name = f'new-linux-{random_username()}'
    unique_ip = random_ip()

    computer = linux_client_manager_rest_client.create_object('computers/linux', ou.computer_default_container, {
        'name': computer_name,
        'ip': [unique_ip],
        'unixhome': '/dev/null',
        'shell': '/bin/bash',
    })

    assert computer.dn
    assert computer_name in computer.dn
    assert ou.dn in computer.dn

    # Cleanup
    computer.delete()


@check_delegation
def test_linux_client_create_computer_denied_cross_ou(linux_client_manager_rest_client, ldap_base, random_username):
    """Test that linux client manager cannot create computers outside their OU via UDM-REST."""
    ou2_dn = f'ou=ou2,{ldap_base}'

    computer_name = f'denied-linux-{random_username()}'
    unique_ip = random_ip()

    with pytest.raises(Forbidden):
        linux_client_manager_rest_client.create_object('computers/linux', f'cn=computers,{ou2_dn}', {
            'name': computer_name,
            'ip': [unique_ip],
            'unixhome': '/dev/null',
            'shell': '/bin/bash',
        })


@check_delegation
def test_linux_client_delete_allowed(linux_client_manager_rest_client, ou, udm, random_username):
    """Test that linux client manager can delete computers in their OU via UDM-REST."""
    computer_name = f'delete-test-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou.dn}',
    )

    linux_client_manager_rest_client.remove_object('computers/linux', computer_dn)

    computers = linux_client_manager_rest_client.search_objects('computers/linux', f'name={computer_name}')
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
def test_linux_client_manager_can_access_groups_in_ou(linux_client_manager_rest_client, test_group_in_ou):
    """Test that linux client manager can access group objects within their OU via UDM-REST (OU-specific security model)."""
    group = linux_client_manager_rest_client.get_object('groups/group', test_group_in_ou)
    assert group.dn == test_group_in_ou
    assert 'name' in group.properties


@check_delegation
def test_linux_client_manager_cannot_access_base_level_groups(linux_client_manager_rest_client, test_group_at_base):
    """Test that linux client manager cannot access base-level groups via UDM-REST (security improvement)."""
    # Should not be able to access base-level groups anymore
    with pytest.raises(UnprocessableEntity):
        linux_client_manager_rest_client.get_object('groups/group', test_group_at_base)


@check_delegation
def test_linux_client_manager_can_modify_group_memberships_in_ou(linux_client_manager_rest_client, test_computer_in_ou, test_group_in_ou):
    """Test that linux client manager can modify group memberships for groups within their OU via UDM-REST."""
    group = linux_client_manager_rest_client.get_object('groups/group', test_group_in_ou)
    current_hosts = group.properties.get('hosts', [])

    linux_client_manager_rest_client.modify_object('groups/group', test_group_in_ou, {
        'hosts': [*current_hosts, test_computer_in_ou],
    })

    group.reload()
    assert test_computer_in_ou in group.properties.get('hosts', [])


@check_delegation
def test_linux_client_manager_cannot_access_users(linux_client_manager_rest_client, ou, udm, random_username):
    """Test that linux client manager cannot access user objects via UDM-REST."""
    user_dn = udm.create_object(
        'users/user',
        username=f'testuser-{random_username()}',
        lastname='TestUser',
        password='univention',
        position=f'cn=users,{ou.dn}',
    )

    with pytest.raises(UnprocessableEntity):
        linux_client_manager_rest_client.get_object('users/user', user_dn)

    with pytest.raises(Forbidden):
        linux_client_manager_rest_client.create_object('users/user', f'cn=users,{ou.dn}', {
            'username': f'newuser-{random_username()}',
            'lastname': 'TestUser',
            'password': 'univention',
        })


@check_delegation
def test_linux_client_manager_cannot_access_global_features(linux_client_manager_rest_client):
    """Test that linux client manager cannot access global system administration features via UDM-REST."""
    # Test mail domain access
    mail_domains = linux_client_manager_rest_client.search_objects('mail/domain')
    assert mail_domains == []

    # Test DNS zone access
    dns_zones = linux_client_manager_rest_client.search_objects('dns/forward_zone')
    assert dns_zones == []

    # Test policy access
    policy_types = ['policies/desktop', 'policies/pwhistory', 'policies/umc']
    for policy_type in policy_types:
        policies = linux_client_manager_rest_client.search_objects(policy_type)
        assert policies == []
