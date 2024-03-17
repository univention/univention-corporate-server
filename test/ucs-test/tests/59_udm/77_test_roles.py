#!/usr/share/ucs-test/runner pytest-3
## desc: Test guardianRoles and guardianInheritedRoles
## tags: [udm,udm-settings,apptest]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from univention.admin import modules
from univention.admin.rest.client import UDM as UDM_REST


@pytest.fixture()
def udm_rest_client(ucr, account):
    udm_rest = UDM_REST(
        uri='https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
        username=account.username,
        password=account.bindpw,
    )
    return udm_rest.get('users/user')


@pytest.fixture()
def user_with_roles(udm, random_string):
    role = random_string()
    g_roles = [f'app:group:{role}{i}' for i in range(3)]
    u_roles = [f'app:user:{role}{i}' for i in range(3)]
    user_dn, username = udm.create_user(guardianRoles=u_roles)
    udm.create_group(users=user_dn, guardianMemberRoles=g_roles)
    return SimpleNamespace(
        dn=user_dn,
        username=username,
        guardianInheritedRoles=g_roles,
        guardianRoles=u_roles,
    )


@pytest.fixture()
def REST_get(account, ucr):
    s = requests.Session()
    s.auth = (account.username, account.bindpw)
    s.headers.update({'accept': 'application/json'})
    base_url = 'https://{hostname}.{domainname}/univention/udm/'.format(**ucr)

    def get(url, params=None):
        res = s.get(f'{base_url}/{url}', params=params)
        assert res.status_code == 200
        return res.json()

    return get


# not supported currently
# def test_roles_nested_groups(udm, ucr):
#     lo, _po = getMachineConnection(ldap_master=True)
#     user_dn, username = udm.create_user()
#     group_dn, _ = udm.create_group(users=user_dn)
#     nested1_group_dn, _ = udm.create_group(nestedGroup=group_dn)
#     nested2_group_dn, _ = udm.create_group(nestedGroup=nested1_group_dn)
#     nested3_group_dn, _ = udm.create_group(nestedGroup=nested2_group_dn)
#     _dn, attr = udm.list_objects('users/user', filter=f'username={username}')[0]
#     all_groups = get_nested_groups(lo, attr['groups'])
#     expected_groups = [group_dn, nested1_group_dn, nested2_group_dn, nested3_group_dn, f'cn=Domain Users,cn=groups,{ucr["ldap/base"]}']
#     assert set(all_groups) == set(expected_groups)


def test_CLI_roles_from_groups(udm, random_string):
    role = random_string()
    roles1 = [f'app:ns1:{role}{i}' for i in range(3)]
    roles2 = [f'app:ns2:{role}{i}' for i in range(3)]
    roles3 = [f'app:ns3:{role}{i}' for i in range(3)]
    user_dn, username = udm.create_user()
    udm.create_group(users=user_dn, guardianMemberRoles=roles1)
    udm.create_group(users=user_dn, guardianMemberRoles=roles2)
    udm.create_group(users=user_dn, guardianMemberRoles=roles3)
    _dn, attr = udm.list_objects('users/user', filter=f'username={username}', properties=['*', 'guardianInheritedRoles'])[0]
    assert set(roles1 + roles2 + roles3) == set(attr.get('guardianInheritedRoles', []))


def test_CLI_list_roles(udm, user_with_roles):
    # with guardianInheritedRoles
    _dn, attr = udm.list_objects('users/user', filter=f'username={user_with_roles.username}', properties=['*', 'guardianInheritedRoles'])[0]
    assert attr['username'] == [user_with_roles.username]
    assert set(attr['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert set(attr['guardianRoles']) == set(user_with_roles.guardianRoles)
    # without
    _dn, attr = udm.list_objects('users/user', filter=f'username={user_with_roles.username}')[0]
    assert 'guardianInheritedRoles' not in attr
    assert attr['username'] == [user_with_roles.username]
    assert set(attr['guardianRoles']) == set(user_with_roles.guardianRoles)
    _dn, attr = udm.list_objects('users/user', filter=f'username={user_with_roles.username}', properties='*')[0]
    assert 'guardianInheritedRoles' not in attr
    assert attr['username'] == [user_with_roles.username]
    assert set(attr['guardianRoles']) == set(user_with_roles.guardianRoles)


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
@pytest.mark.parametrize('opened', [True, False], ids=lambda d: f'opened={d}')
def test_REST_search_with_guardianInheritedRoles(udm, udm_rest_client, random_string, opened):
    roles = ['qwe:asd:zxc', 'poi:lkj:mnb&rty:fgh:vbn', 'qwe:asd:mnbvcxz', 'poi:lkj:qwerty&rty:fgh:vbn']
    group_name = random_string()
    groups = [
        udm.create_group(name=f'Guardian Test Group 1 {group_name}', guardianMemberRoles=roles[:2]),
        udm.create_group(name=f'Guardian Test Group 2 {group_name}', guardianMemberRoles=roles[2:]),
    ]
    user = udm.create_user()
    udm.modify_object('groups/group', dn=groups[0][0], users=user[0])
    udm.modify_object('groups/group', dn=groups[1][0], users=user[0])
    for user in udm_rest_client.search('uid=%s' % user[1], opened=opened, properties=['*', 'guardianInheritedRoles']):
        if not opened:
            user = user.open()
        gIR = user.properties.get('guardianInheritedRoles')
        # check first if we got the guardianInheritedRoles
        assert gIR
        # Check for the existence of the InheritedRoles on the original list of roles
        for inheritedRole in gIR:
            assert inheritedRole in roles
            roles.remove(inheritedRole)
        # Check to ensure all roles are present in the user
        assert not roles


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
@pytest.mark.parametrize('opened', [True, False], ids=lambda d: f'opened={d}')
def test_REST_search_without_guardianInheritedRoles(udm, udm_rest_client, random_string, opened):
    roles = ['qwe:asd:zxc', 'poi:lkj:mnb&rty:fgh:vbn', 'qwe:asd:mnbvcxz', 'poi:lkj:qwerty&rty:fgh:vbn']
    group_name = random_string()
    groups = [
        udm.create_group(name=f'Guardian Test Group 1 {group_name}', guardianMemberRoles=roles[:2]),
        udm.create_group(name=f'Guardian Test Group 2 {group_name}', guardianMemberRoles=roles[2:]),
    ]
    user = udm.create_user()
    udm.modify_object('groups/group', dn=groups[0][0], users=user[0])
    udm.modify_object('groups/group', dn=groups[1][0], users=user[0])
    for user in udm_rest_client.search('uid=%s' % user[1], opened=opened, properties=['*']):
        if not opened:
            user = user.open()
        assert not user.properties.get('guardianInheritedRoles')


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
def test_REST_get_roles(udm_rest_client, user_with_roles):
    # with
    user = udm_rest_client.get(user_with_roles.dn, properties=['*', 'guardianInheritedRoles'])
    assert user.properties['username'] == user_with_roles.username
    assert set(user.properties['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert set(user.properties['guardianRoles']) == set(user_with_roles.guardianRoles)
    user = udm_rest_client.get(user_with_roles.dn, properties=['guardianInheritedRoles'])
    assert 'username' not in user.properties
    assert 'guardianRoles' not in user.properties
    assert set(user.properties['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    # without
    user = udm_rest_client.get(user_with_roles.dn, properties=['*'])
    assert user.properties['username'] == user_with_roles.username
    assert set(user.properties['guardianRoles']) == set(user_with_roles.guardianRoles)
    assert not user.properties['guardianInheritedRoles']
    user = udm_rest_client.get(user_with_roles.dn)
    assert set(user.properties['guardianRoles']) == set(user_with_roles.guardianRoles)
    assert user.properties['username'] == user_with_roles.username
    assert not user.properties['guardianInheritedRoles']


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
def test_REST_requests_get_roles(user_with_roles, REST_get):
    # without
    user = REST_get(f'users/user/{user_with_roles.dn}')
    assert not user['properties']['guardianInheritedRoles']
    assert user['properties']['username'] == user_with_roles.username
    assert set(user['properties']['guardianRoles']) == set(user_with_roles.guardianRoles)
    # with
    params = {'properties': ['*', 'guardianInheritedRoles']}
    user = REST_get(f'users/user/{user_with_roles.dn}', params=params)
    assert user['properties']['username'] == user_with_roles.username
    assert set(user['properties']['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert set(user['properties']['guardianRoles']) == set(user_with_roles.guardianRoles)
    params = {'properties': ['guardianInheritedRoles']}
    user = REST_get(f'users/user/{user_with_roles.dn}', params=params)
    assert 'username' not in user['properties']
    assert set(user['properties']['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert 'guardianRoles' not in user['properties']


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
def test_REST_requests_search_roles(REST_get, user_with_roles):
    # without
    params = {'query[username]': user_with_roles.username}
    user = REST_get('users/user/', params=params)['_embedded']['udm:object'][0]
    assert not user['properties']['guardianInheritedRoles']
    assert user['properties']['username'] == user_with_roles.username
    assert set(user['properties']['guardianRoles']) == set(user_with_roles.guardianRoles)
    # with
    params = {'query[username]': user_with_roles.username, 'properties': ['*', 'guardianInheritedRoles']}
    user = REST_get('users/user/', params=params)['_embedded']['udm:object'][0]
    assert user['properties']['username'] == user_with_roles.username
    assert set(user['properties']['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert set(user['properties']['guardianRoles']) == set(user_with_roles.guardianRoles)
    params = {'query[username]': user_with_roles.username, 'properties': ['guardianInheritedRoles']}
    user = REST_get('users/user/', params=params)['_embedded']['udm:object'][0]
    assert set(user['properties']['guardianInheritedRoles']) == set(user_with_roles.guardianInheritedRoles)
    assert 'username' not in user['properties']
    assert 'guardianRoles' not in user['properties']


def test_role_attributes_on_modules():
    roles_and_inherited_roles_mods = [
        'users/user',
        'computers/domaincontroller_backup',
        'computers/windows',
        'computers/linux',
        'computers/memberserver',
        'computers/macos',
        'computers/domaincontroller_master',
        'computers/ubuntu',
        'computers/windows_domaincontroller',
        'computers/domaincontroller_slave',
        'computers/trustaccount',
        'users/ldap',
        'users/self',
    ]
    expected = {
        'guardianRoles': roles_and_inherited_roles_mods,
        'guardianMemberRoles': ['groups/group'],
        'guardianInheritedRoles': roles_and_inherited_roles_mods,
    }
    modules.update()
    for mod_name, mod in modules.modules.items():
        for prop in expected:
            if prop in mod.property_descriptions:
                assert mod_name in expected[prop], f'{mod_name} should not have {prop}'
            else:
                assert mod_name not in expected[prop], f'{mod_name} should have {prop}'
