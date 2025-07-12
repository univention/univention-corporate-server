#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check linux-client-manager role in UMC
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import subprocess

import pytest
from conftest import translate

from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest
from univention.testing.strings import random_ip


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='directory/manager/web/delegative-administration/enabled not activated')


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


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
def test_default_containers(linux_client_manager_umc_client, ou):
    res = linux_client_manager_umc_client.umc_command('udm/containers', {"objectType": 'computers/linux'}, 'computers/linux').result
    assert {x['id'] for x in res} == {ou.computer_default_container}


@check_delegation
def test_linux_client_read_allowed(linux_client_manager_umc_client, test_computer_in_ou):
    """Test that linux client manager can read computers in their OU."""
    res = linux_client_manager_umc_client.get_object('computers/linux', test_computer_in_ou)
    assert res
    assert res['$dn$'] == test_computer_in_ou
    assert 'name' in res
    assert 'ip' in res


@check_delegation
def test_linux_client_read_denied_cross_ou(linux_client_manager_umc_client, test_computer_at_base):
    """Test that linux client manager cannot read computers outside their OU."""
    with pytest.raises(BadRequest):
        linux_client_manager_umc_client.get_object('computers/linux', test_computer_at_base)


@check_delegation
def test_linux_client_modify_allowed(linux_client_manager_umc_client, test_computer_in_ou):
    """Test that linux client manager can modify computers in their OU."""
    res = linux_client_manager_umc_client.modify_object('computers/linux', test_computer_in_ou, {
        'description': 'Modified by linux client manager',
    })
    assert res['success']
    assert res['$dn$'] == test_computer_in_ou

    read_res = linux_client_manager_umc_client.get_object('computers/linux', test_computer_in_ou)
    assert read_res['description'] == 'Modified by linux client manager'


@check_delegation
def test_linux_client_modify_denied_cross_ou(linux_client_manager_umc_client, test_computer_at_base):
    """Test that linux client manager cannot modify computers outside their OU."""
    res = linux_client_manager_umc_client.modify_object('computers/linux', test_computer_at_base, {
        'description': 'Should not work',
    })
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_password_reset_allowed(linux_client_manager_umc_client, test_computer_in_ou):
    """Test that linux client manager can reset passwords of computers in their OU."""
    res = linux_client_manager_umc_client.modify_object('computers/linux', test_computer_in_ou, {
        'password': 'newpassword123',
    })
    assert res['success']
    assert res['$dn$'] == test_computer_in_ou


@check_delegation
def test_linux_client_password_reset_denied_cross_ou(linux_client_manager_umc_client, test_computer_at_base):
    """Test that linux client manager cannot reset passwords of computers outside their OU."""
    res = linux_client_manager_umc_client.modify_object('computers/linux', test_computer_at_base, {
        'password': 'shouldnotwork',
    })
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_search_scope(linux_client_manager_umc_client, ou, ldap_base, test_computer_in_ou, test_computer_at_base, udm):
    """Test that linux client manager can only search computers in their OU."""
    # Test 1: Search in the specific OU container should work
    res_ou = linux_client_manager_umc_client.search_objects('computers/linux', container=f"cn=computers,{ou.dn}")
    found_dns_ou = {x['$dn$'] for x in res_ou}

    # Should find the computer in the OU
    assert test_computer_in_ou in found_dns_ou

    # Test 2: Global "all containers" search should be restricted
    res_all = linux_client_manager_umc_client.search_objects('computers/linux', container="all")
    found_dns_all = {x['$dn$'] for x in res_all}
    expected_dns = {x[0] for x in udm.list_objects('computers/linux', properties=["DN"], position=ou.dn)}
    assert found_dns_all == expected_dns

    # Test 3: Search in base-level computers container should be restricted
    with pytest.raises(BadRequest):
        linux_client_manager_umc_client.search_objects('computers/linux', container=f"cn=computers,{ldap_base}")


@check_delegation
def test_linux_client_delete_allowed(linux_client_manager_umc_client, ou, udm, random_username):
    """Test that linux client manager can delete computers in their OU."""
    computer_name = f'delete-test-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou.dn}',
    )

    res = linux_client_manager_umc_client.remove_object('computers/linux', computer_dn)
    assert res['success']


@check_delegation
def test_linux_client_delete_denied_cross_ou(linux_client_manager_umc_client, test_computer_at_base):
    """Test that linux client manager cannot delete computers outside their OU."""
    res = linux_client_manager_umc_client.remove_object('computers/linux', test_computer_at_base)
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_manager_cannot_access_users(linux_client_manager_umc_client, ou, udm, random_username):
    """Test that linux client manager cannot access user objects."""
    user_dn = udm.create_object(
        'users/user',
        username=f'testuser-{random_username()}',
        lastname='TestUser',
        password='univention',
        position=f'cn=users,{ou.dn}',
    )

    with pytest.raises(BadRequest):
        linux_client_manager_umc_client.get_object('users/user', user_dn)

    res = linux_client_manager_umc_client.create_object('users/user', f'cn=users,{ou.dn}', {
        'lastname': f'newuser-{random_username()}',
        'username': f'newuser-{random_username()}',
        'password': 'univention',
    })
    assert not res['success']
    assert res['details'] == translate('Permission denied.')


@check_delegation
def test_linux_client_manager_cannot_access_global_features(linux_client_manager_umc_client):
    """Test that linux client manager cannot access global system administration features."""
    res = linux_client_manager_umc_client.search_objects('mail/domain')
    assert res == []

    res = linux_client_manager_umc_client.search_objects('dns/forward_zone')
    assert res == []


@check_delegation
def test_linux_client_manager_cross_ou_complete_denial(linux_client_manager_umc_client, ou, ldap_base, udm, random_username):
    """Test comprehensive access denial to other OUs."""
    ou2_dn = f'ou=ou2,{ldap_base}'

    computer_name = f'testlinux-ou2-{random_username()}'
    unique_ip = random_ip()

    computer_in_ou2 = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou2_dn}',
    )

    with pytest.raises(BadRequest):
        linux_client_manager_umc_client.get_object('computers/linux', computer_in_ou2)

    res = linux_client_manager_umc_client.modify_object('computers/linux', computer_in_ou2, {
        'description': 'Should not work',
    })
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {computer_in_ou2}.'

    res = linux_client_manager_umc_client.remove_object('computers/linux', computer_in_ou2)
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {computer_in_ou2}.'


@check_delegation
def test_linux_client_create_computer_allowed(linux_client_manager_umc_client, ou, random_username):
    """Test that linux client manager can create new computers in their OU."""
    computer_name = f'new-linux-{random_username()}'
    unique_ip = random_ip()

    res = linux_client_manager_umc_client.create_object('computers/linux', ou.computer_default_container, {
        'name': computer_name,
        'ip': [unique_ip],
        'unixhome': '/dev/null',
        'shell': '/bin/bash',
    })

    try:
        assert res['success']
        assert computer_name in res['$dn$']
        assert ou.dn in res['$dn$']
    finally:
        if res.get('success'):
            linux_client_manager_umc_client.remove_object('computers/linux', res['$dn$'])


@check_delegation
def test_linux_client_create_computer_denied_cross_ou(linux_client_manager_umc_client, ldap_base, random_username):
    """Test that linux client manager cannot create computers outside their OU."""
    ou2_dn = f'ou=ou2,{ldap_base}'

    computer_name = f'denied-linux-{random_username()}'
    unique_ip = random_ip()

    res = linux_client_manager_umc_client.create_object('computers/linux', f'cn=computers,{ou2_dn}', {
        'name': computer_name,
        'ip': [unique_ip],
        'unixhome': '/dev/null',
        'shell': '/bin/bash',
    })
    assert not res['success']
    assert res['details'] == translate('Permission denied.')


@check_delegation
def test_linux_client_create_computer_denied_at_base(linux_client_manager_umc_client, ldap_base, random_username):
    """Test that linux client manager cannot create computers at base level."""
    computer_name = f'base-linux-{random_username()}'
    unique_ip = random_ip()

    res = linux_client_manager_umc_client.create_object('computers/linux', f'cn=computers,{ldap_base}', {
        'name': computer_name,
        'ip': [unique_ip],
        'unixhome': '/dev/null',
        'shell': '/bin/bash',
    })
    assert not res['success']
    assert res['details'] == translate('Permission denied.')


@check_delegation
def test_linux_client_manager_can_access_groups_in_ou(linux_client_manager_umc_client, test_group_in_ou):
    """Test that linux client manager can access group objects within their OU (OU-specific security model)."""
    res = linux_client_manager_umc_client.get_object('groups/group', test_group_in_ou)
    assert res['$dn$'] == test_group_in_ou
    assert 'name' in res


@check_delegation
def test_linux_client_manager_cannot_access_base_level_groups(linux_client_manager_umc_client, test_group_at_base):
    """Test that linux client manager cannot access base-level groups (security improvement)."""
    with pytest.raises(BadRequest):
        linux_client_manager_umc_client.get_object('groups/group', test_group_at_base)


@check_delegation
def test_linux_client_manager_can_modify_group_memberships_in_ou(linux_client_manager_umc_client, test_computer_in_ou, test_group_in_ou):
    """Test that linux client manager can modify group memberships within their OU."""
    current_res = linux_client_manager_umc_client.get_object('groups/group', test_group_in_ou)
    current_hosts = current_res.get('hosts', [])

    res = linux_client_manager_umc_client.modify_object('groups/group', test_group_in_ou, {
        'hosts': [*current_hosts, test_computer_in_ou],
    })
    assert res['success']
    assert res['$dn$'] == test_group_in_ou


@check_delegation
def test_linux_client_manager_cannot_access_policies(linux_client_manager_umc_client):
    """Test that linux client manager cannot access policy objects."""
    policy_types = ['policies/desktop', 'policies/pwhistory', 'policies/umc']

    for policy_type in policy_types:
        res = linux_client_manager_umc_client.search_objects(policy_type)
        assert res == []


@check_delegation
def test_linux_client_manager_container_restrictions(linux_client_manager_umc_client, ou):
    """Test that linux client manager can only access containers within their OU context."""
    res = linux_client_manager_umc_client.umc_command('udm/containers', {"objectType": "computers/linux"}, 'computers/linux').result
    container_ids = {x['id'] for x in res}

    for container_id in container_ids:
        assert ou.dn in container_id or container_id == ou.computer_default_container
