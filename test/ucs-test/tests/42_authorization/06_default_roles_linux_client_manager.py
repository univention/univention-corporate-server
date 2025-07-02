#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check linux-client-manager role in UMC
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import locale
import subprocess
from types import SimpleNamespace

import pytest

from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest
from univention.testing.strings import random_ip
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='directory/manager/web/delegative-administration/enabled not activated')


TRANSLATIONS = {
    'de_DE': {
        'Permission denied.': 'Zugriff verweigert.',
        'No such object:': 'Das Objekt existiert nicht:',
    },
    'en_US': {
        'Permission denied.': 'Permission denied.',
        'No such object:': 'No such object:',
    },
}


def _(string: str) -> str:
    code, _ = locale.getlocale()
    return TRANSLATIONS.get(code, {}).get(string, string)


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


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
def linux_client_manager_user(ou, ldap_base, udm):
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
def test_default_containers(ou):
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')
    res = client.umc_command('udm/containers', {"objectType": 'computers/linux'}, 'computers/linux').result
    assert {x['id'] for x in res} == {ou.computer_default_container}


@check_delegation
def test_linux_client_read_allowed(ou, ldap_base, linux_client_manager_user, test_computer_in_ou):
    """Test that linux client manager can read computers in their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    res = client.umc_command('udm/get', [test_computer_in_ou], 'computers/linux').result
    assert res
    assert res[0]['$dn$'] == test_computer_in_ou
    assert 'name' in res[0]
    assert 'ip' in res[0]


@check_delegation
def test_linux_client_read_denied_cross_ou(ou, ldap_base, linux_client_manager_user, test_computer_at_base):
    """Test that linux client manager cannot read computers outside their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    with pytest.raises(BadRequest):
        client.umc_command('udm/get', [test_computer_at_base], 'computers/linux')


@check_delegation
def test_linux_client_modify_allowed(ou, ldap_base, linux_client_manager_user, test_computer_in_ou):
    """Test that linux client manager can modify computers in their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    changes = {
        '$dn$': test_computer_in_ou,
        'description': 'Modified by linux client manager',
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'computers/linux').result[0]
    assert res['success']
    assert res['$dn$'] == test_computer_in_ou

    read_res = client.umc_command('udm/get', [test_computer_in_ou], 'computers/linux').result[0]
    assert read_res['description'] == 'Modified by linux client manager'


@check_delegation
def test_linux_client_modify_denied_cross_ou(ou, ldap_base, linux_client_manager_user, test_computer_at_base):
    """Test that linux client manager cannot modify computers outside their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    changes = {
        '$dn$': test_computer_at_base,
        'description': 'Should not work',
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == f'{_("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_password_reset_allowed(ou, ldap_base, linux_client_manager_user, test_computer_in_ou):
    """Test that linux client manager can reset passwords of computers in their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    changes = {
        '$dn$': test_computer_in_ou,
        'password': 'newpassword123',
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'computers/linux').result[0]
    assert res['success']
    assert res['$dn$'] == test_computer_in_ou


@check_delegation
def test_linux_client_password_reset_denied_cross_ou(ou, ldap_base, linux_client_manager_user, test_computer_at_base):
    """Test that linux client manager cannot reset passwords of computers outside their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    changes = {
        '$dn$': test_computer_at_base,
        'password': 'shouldnotwork',
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == f'{_("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_search_scope(ou, ldap_base, linux_client_manager_user, test_computer_in_ou, test_computer_at_base, udm):
    """Test that linux client manager can only search computers in their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    # Test 1: Search in the specific OU container should work
    options_ou = {
        "container": f"cn=computers,{ou.dn}",
        "hidden": False,
        "objectType": "computers/linux",
        "objectProperty": "None",
        "objectPropertyValue": "",
        "fields": ["name", "path", "displayName"],
    }

    res_ou = client.umc_command('udm/query', options_ou, 'computers/linux').result
    found_dns_ou = {x['$dn$'] for x in res_ou}

    # Should find the computer in the OU
    assert test_computer_in_ou in found_dns_ou

    # Test 2: Global "all containers" search should be restricted
    options_all = {
        "container": "all",
        "hidden": False,
        "objectType": "computers/linux",
        "objectProperty": "None",
        "objectPropertyValue": "",
        "fields": ["name", "path", "displayName"],
    }
    res_all = client.umc_command('udm/query', options_all, 'computers/linux').result
    found_dns_all = {x['$dn$'] for x in res_all}
    expected_dns = {x[0] for x in udm.list_objects('computers/linux', properties=["DN"], position=ou.dn)}
    assert found_dns_all == expected_dns

    # Test 3: Search in base-level computers container should be restricted
    options_base = {
        "container": f"cn=computers,{ldap_base}",
        "hidden": False,
        "objectType": "computers/linux",
        "objectProperty": "None",
        "objectPropertyValue": "",
        "fields": ["name", "path", "displayName"],
    }

    with pytest.raises(BadRequest):
        client.umc_command('udm/query', options_base, 'computers/linux').result  # noqa: B018


@check_delegation
def test_linux_client_delete_allowed(ou, ldap_base, linux_client_manager_user, udm, random_username):
    """Test that linux client manager can delete computers in their OU."""
    computer_name = f'delete-test-{random_username()}'
    unique_ip = random_ip()

    computer_dn = udm.create_object(
        'computers/linux',
        name=computer_name,
        ip=[unique_ip],
        position=f'cn=computers,{ou.dn}',
    )

    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    options = [{
        'object': computer_dn,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]

    res = client.umc_command('udm/remove', options, 'computers/computer').result[0]
    assert res['success']


@check_delegation
def test_linux_client_delete_denied_cross_ou(ou, ldap_base, linux_client_manager_user, test_computer_at_base):
    """Test that linux client manager cannot delete computers outside their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    options = [{
        'object': test_computer_at_base,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]

    res = client.umc_command('udm/remove', options, 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == f'{_("No such object:")} {test_computer_at_base}.'


@check_delegation
def test_linux_client_manager_cannot_access_users(ou, ldap_base, linux_client_manager_user, udm, random_username):
    """Test that linux client manager cannot access user objects."""
    user_dn = udm.create_object(
        'users/user',
        username=f'testuser-{random_username()}',
        lastname='TestUser',
        password='univention',
        position=f'cn=users,{ou.dn}',
    )

    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    with pytest.raises(BadRequest):
        client.umc_command('udm/get', [user_dn], 'users/user')

    options = [{
        'object': {
            'lastname': f'newuser-{random_username()}',
            'username': f'newuser-{random_username()}',
            'password': 'univention',
        },
        "options": {
            "container": f'cn=users,{ou.dn}',
            "objectType": "users/user",
        },
    }]

    res = client.umc_command('udm/add', options, 'users/user').result[0]
    assert not res['success']
    assert res['details'] == _('Permission denied.')


@check_delegation
def test_linux_client_manager_cannot_access_global_features(ou, ldap_base, linux_client_manager_user):
    """Test that linux client manager cannot access global system administration features."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    res = client.umc_command('udm/query', {
        "container": "all",
        "objectType": "mail/domain",
        "objectProperty": "None",
        "objectPropertyValue": "",
    }, 'mail/domain').result
    assert res == []

    res = client.umc_command('udm/query', {
        "container": "all",
        "objectType": "dns/forward_zone",
        "objectProperty": "None",
        "objectPropertyValue": "",
    }, 'dns/forward_zone').result
    assert res == []


@check_delegation
def test_linux_client_manager_cross_ou_complete_denial(ou, ldap_base, linux_client_manager_user, udm, random_username):
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

    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    with pytest.raises(BadRequest):
        client.umc_command('udm/get', [computer_in_ou2], 'computers/linux')

    changes = {
        '$dn$': computer_in_ou2,
        'description': 'Should not work',
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == f'{_("No such object:")} {computer_in_ou2}.'

    options = [{
        'object': computer_in_ou2,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]

    res = client.umc_command('udm/remove', options, 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == f'{_("No such object:")} {computer_in_ou2}.'


@check_delegation
def test_linux_client_create_computer_allowed(ou, ldap_base, linux_client_manager_user, random_username):
    """Test that linux client manager can create new computers in their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    computer_name = f'new-linux-{random_username()}'
    unique_ip = random_ip()

    options = [{
        'object': {
            'name': computer_name,
            'ip': [unique_ip],
            'unixhome': '/dev/null',
            'shell': '/bin/bash',
        },
        "options": {
            "container": ou.computer_default_container,
            "objectType": "computers/linux",
        },
    }]

    try:
        res = client.umc_command('udm/add', options, 'computers/linux').result[0]
        assert res['success']
        assert computer_name in res['$dn$']
        assert ou.dn in res['$dn$']
    finally:
        if res:
            client.umc_command('udm/remove', [{'object': res['$dn$']}], 'computers/linux')


@check_delegation
def test_linux_client_create_computer_denied_cross_ou(ou, ldap_base, linux_client_manager_user, udm, random_username):
    """Test that linux client manager cannot create computers outside their OU."""
    ou2_dn = f'ou=ou2,{ldap_base}'

    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    computer_name = f'denied-linux-{random_username()}'
    unique_ip = random_ip()

    options = [{
        'object': {
            'name': computer_name,
            'ip': [unique_ip],
            'unixhome': '/dev/null',
            'shell': '/bin/bash',
        },
        "options": {
            "container": f'cn=computers,{ou2_dn}',
            "objectType": "computers/linux",
        },
    }]

    res = client.umc_command('udm/add', options, 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == _('Permission denied.')


@check_delegation
def test_linux_client_create_computer_denied_at_base(ou, ldap_base, linux_client_manager_user, random_username):
    """Test that linux client manager cannot create computers at base level."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    computer_name = f'base-linux-{random_username()}'
    unique_ip = random_ip()

    options = [{
        'object': {
            'name': computer_name,
            'ip': [unique_ip],
            'unixhome': '/dev/null',
            'shell': '/bin/bash',
        },
        "options": {
            "container": f'cn=computers,{ldap_base}',
            "objectType": "computers/linux",
        },
    }]

    res = client.umc_command('udm/add', options, 'computers/linux').result[0]
    assert not res['success']
    assert res['details'] == _('Permission denied.')


@check_delegation
def test_linux_client_manager_can_access_groups_in_ou(ou, ldap_base, linux_client_manager_user, test_group_in_ou):
    """Test that linux client manager can access group objects within their OU (OU-specific security model)."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    res = client.umc_command('udm/get', [test_group_in_ou], 'groups/group').result[0]
    assert res['$dn$'] == test_group_in_ou
    assert 'name' in res


@check_delegation
def test_linux_client_manager_cannot_access_base_level_groups(ou, ldap_base, linux_client_manager_user, test_group_at_base):
    """Test that linux client manager cannot access base-level groups (security improvement)."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    with pytest.raises(BadRequest):
        client.umc_command('udm/get', [test_group_at_base], 'groups/group')


@check_delegation
def test_linux_client_manager_can_modify_group_memberships_in_ou(ou, ldap_base, linux_client_manager_user, test_computer_in_ou, test_group_in_ou):
    """Test that linux client manager can modify group memberships within their OU."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    current_res = client.umc_command('udm/get', [test_group_in_ou], 'groups/group').result[0]
    current_hosts = current_res.get('hosts', [])

    changes = {
        '$dn$': test_group_in_ou,
        'hosts': [*current_hosts, test_computer_in_ou],
    }

    res = client.umc_command('udm/put', [{'object': changes}], 'groups/group').result[0]
    assert res['success']
    assert res['$dn$'] == test_group_in_ou


@check_delegation
def test_linux_client_manager_cannot_access_policies(ou, ldap_base, linux_client_manager_user):
    """Test that linux client manager cannot access policy objects."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    policy_types = ['policies/desktop', 'policies/pwhistory', 'policies/umc']

    for policy_type in policy_types:
        res = client.umc_command('udm/query', {
            "container": "all",
            "objectType": policy_type,
            "objectProperty": "None",
            "objectPropertyValue": "",
        }, policy_type).result
        assert res == []


@check_delegation
def test_linux_client_manager_container_restrictions(ou, ldap_base, linux_client_manager_user):
    """Test that linux client manager can only access containers within their OU context."""
    client = Client()
    client.authenticate(ou.client_manager_username, 'univention')

    res = client.umc_command('udm/containers', {"objectType": "computers/linux"}, 'computers/linux').result
    container_ids = {x['id'] for x in res}

    for container_id in container_ids:
        assert ou.dn in container_id or container_id == ou.computer_default_container
