#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import re
import time
from types import SimpleNamespace

import pytest

from univention.config_registry import ucr as _ucr
from univention.lib.umc import Forbidden
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(not _ucr.is_true('umc/udm/delegation'), reason='umc/udm/delegation not activated')


@pytest.fixture
def bremen_ou(udm, random_username):
    dn_ou = udm.create_object('container/ou', name='bremen')
    ouadmin_username = random_username()
    normal_user_username = random_username()
    dn_admin = udm.create_object('users/user', username=ouadmin_username, guardianRoles=['umc:udm:ouadmin&umc:udm:ou=bremen'], lastname='bremen_admin', password='univention')
    dn_user = udm.create_object('users/user', username=normal_user_username, guardianRoles=['umc:udm:dummyrole'], position=dn_ou, lastname='lastname', password='univention')
    # set user default container
    udm.modify_object('container/ou', dn=dn_ou, userPath='1')
    udm.modify_object('container/ou', dn=dn_ou, groupPath='1')
    ou_cn_users = udm.create_object('container/cn', name='users', position=dn_ou)
    ou_cn_groups = udm.create_object('container/cn', name='groups', position=dn_ou)
    yield SimpleNamespace(
        ou_dn=dn_ou,
        ouadmin_dn=dn_admin,
        ouadmin_username=ouadmin_username,
        normal_user_username=normal_user_username,
        user_dn=dn_user,
        user_default_container=dn_ou,
        group_default_container=dn_ou,
        udm=udm,
        ou_cn_users=ou_cn_users,
        ou_cn_groups=ou_cn_groups,
    )
    udm.remove_object('container/ou', dn=dn_ou)
    udm.remove_object('users/user', dn=dn_admin)


@check_delegation
def test_ouadmin_default_containers(bremen_ou, ldap_base):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    res = client.umc_command('udm/containers', {"objectType": "users/user"}, 'users/user').result
    assert {x['id'] for x in res} == {bremen_ou.user_default_container}
    res = client.umc_command('udm/containers', {"objectType": "groups/group"}, 'groups/group').result
    assert {x['id'] for x in res} == {bremen_ou.group_default_container, f'cn=groups,{ldap_base}'}


@check_delegation
@pytest.mark.parametrize('login_user, position, expected', [
    ('admin', 'cn=users,{ldap_base}', True),
    ('admin', 'cn=users,{ou_dn}', True),
    ('admin', '{ou_dn}', True),
    ('admin', '{ldap_base}', True),
    ('ou_admin', 'cn=users,{ou_dn}', True),
    ('ou_admin', '{ou_dn}', True),
    ('ou_admin', 'cn=users,{ldap_base}', False),
    ('ou_admin', '{ldap_base}', False),
])
def test_delete(bremen_ou, ldap_base, random_username, login_user, position, expected):
    cn_user = bremen_ou.udm.create_object('users/user', lastname=random_username(), username=random_username(), password='univention', position=position.format(ou_dn=bremen_ou.ou_dn, ldap_base=ldap_base))
    client = Client()
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': cn_user,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]
    if not expected:
        with pytest.raises(Forbidden):
            client.umc_command('udm/remove', options, 'users/user')
        bremen_ou.udm.remove_object('users/user', dn=cn_user)
    else:
        client.umc_command('udm/remove', options, 'users/user')


@check_delegation
@pytest.mark.parametrize('login_user, position, expected', [
    ('admin', 'cn=users,{ldap_base}', True),
    ('admin', 'cn=users,{ou_dn}', True),
    ('admin', '{ou_dn}', True),
    ('admin', '{ldap_base}', True),
    ('ou_admin', 'cn=users,{ou_dn}', True),
    ('ou_admin', '{ou_dn}', True),
    ('ou_admin', 'cn=users,{ldap_base}', False),
    ('ou_admin', '{ldap_base}', False),
])
def test_create(bremen_ou, ldap_base, random_username, login_user, position, expected):
    client = Client()
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': {
            'lastname': random_username(),
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": position.format(ou_dn=bremen_ou.ou_dn, ldap_base=ldap_base),
            "objectType": "users/user",
        },
    }]
    if not expected:
        with pytest.raises(Forbidden):
            client.umc_command('udm/add', options, 'users/user')
    else:
        client.umc_command('udm/add', options, 'users/user')


@check_delegation
@pytest.mark.parametrize('login_user, objectProperty, objectPropertyValue, expected', [
    ('admin', 'None', '', ["all"]),
    ('admin', 'None', '*trator', ["admin"]),
    ('admin', 'description', 'test', ["cn_test"]),
    ('admin', 'description', 'tes*', ["cn_test"]),
    ('admin', 'description', '*est', ["cn_test"]),
    ('ou_admin', 'None', '', ["all", "not-self"]),
    ('ou_admin', 'description', 'test', ["cn_test"]),
    ('ou_admin', 'description', 'tes*', ["cn_test"]),
    ('ou_admin', 'description', '*est', ["cn_test"]),
])
def test_search(random_username, bremen_ou, login_user, objectProperty, objectPropertyValue, expected):
    dn_test = None
    if objectProperty != "None":
        config = {
            'username': random_username(),
            'lastname': random_username(),
            'password': 'univention',
            objectProperty: "test",
        }
        if login_user == "ou_admin":
            config['position'] = bremen_ou.ou_dn
        dn_test = bremen_ou.udm.create_object('users/user', **config)
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = {
        "container": "all",
        "hidden": "all" in expected,
        "objectType": "users/user",
        "objectProperty": objectProperty,
        "objectPropertyValue": objectPropertyValue,
        "fields": [
            "name",
            "path",
            "displayName",
            "mailPrimaryAddress",
            "firstname",
            "lastname",
        ],
    }
    res = client.umc_command('udm/query', options, 'users/user').result
    names = [x['name'] for x in res]
    assert res
    if "all" in expected:
        all_objects = bremen_ou.udm.list_objects('users/user', properties=["DN"]) if login_user == "admin" else bremen_ou.udm.list_objects('users/user', properties=["DN"], position=bremen_ou.ou_dn)
        assert {obj[0] for obj in all_objects} == {x['$dn$'] for x in res}
    if "admin" in expected:
        assert "Administrator" in names, "Administrator not found"
    if objectProperty != "None":
        rex = re.compile(objectPropertyValue.replace('*', '.*'))
        assert all(rex.match(x[objectProperty]) for x in res)
        assert dn_test in [x['$dn$'] for x in res]
    if "not-self" in expected:
        assert bremen_ou.ouadmin_username not in names, f"{bremen_ou.normal_user_username} found"


def wait_for_progress(client, progress_id):
    while True:
        req = client.umc_command('udm/progress', {"progress_id": progress_id}, 'users/user')
        res = req.result
        if res['finished']:
            return req
        time.sleep(1)


@check_delegation
@pytest.mark.parametrize('login_user, user_dn, target_position, expected', [
    ('admin', '{normal_user}', 'cn=users,{ldap_base}', True),
    ('ou_admin', '{normal_user}', 'cn=users,{ldap_base}', False),
    ('admin', '{normal_user}', '{ou_cn_users}', True),
    ('ou_admin', '{normal_user}', '{ou_cn_users}', True),
])
def test_move(ldap_base, bremen_ou, login_user, user_dn, target_position, expected):
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': user_dn.format(admin_ou=bremen_ou.ouadmin_dn, normal_user=bremen_ou.user_dn, ldap_base=ldap_base),
        "options": {
            "container": target_position.format(ou_dn=bremen_ou.ou_dn, ldap_base=ldap_base, ou_cn_users=bremen_ou.ou_cn_users),
        },
    }]
    if not expected:
        result = client.umc_command('udm/move', options, 'users/user').result
        with pytest.raises(Forbidden):
            wait_for_progress(client, result['id'])
    else:
        result = client.umc_command('udm/move', options, 'users/user').result
        res = wait_for_progress(client, result['id'])
        for intermediate in res.result['intermediate']:
            assert intermediate['success']


@check_delegation
@pytest.mark.parametrize('login_user, user_dn, attribute, expected', [
    ('admin', 'uid=Administrator,cn=users,{ldap_base}', 'guardianInheritedRoles', True),
    ('ou_admin', 'uid=Administrator,cn=users,{ldap_base}', None, False),
    ('admin', '{admin_ou}', 'guardianRoles', True),
    ('ou_admin', '{admin_ou}', None, False),
    ('admin', '{normal_user}', 'guardianRoles', True),
    ('ou_admin', '{normal_user}', 'guardianRoles', True),
])
def test_read(ldap_base, bremen_ou, login_user, user_dn, attribute, expected):
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [
        user_dn.format(admin_ou=bremen_ou.ouadmin_dn, normal_user=bremen_ou.user_dn, ldap_base=ldap_base),
    ]
    if not expected:
        with pytest.raises(Forbidden):
            client.umc_command('udm/get', options, 'users/user')
    else:
        res = client.umc_command('udm/get', options, 'users/user').result
        assert res
        assert res[0]['$dn$'] == user_dn.format(admin_ou=bremen_ou.ouadmin_dn, normal_user=bremen_ou.user_dn, ldap_base=ldap_base)
        if attribute:
            assert attribute in res[0]
            assert res[0][attribute]


@check_delegation
@pytest.mark.parametrize('login_user, user_dn, changes, expected', [
    ('admin', '{normal_user}', {"guardianRoles": ["umc:udm:ouadmin&umc:udm:ou=bremen"]}, True),
    ('ou_admin', '{normal_user}', {"guardianRoles": ["umc:udm:ouadmin&umc:udm:ou=bremen"]}, False),
    ('admin', '{normal_user}', {'description': 'dsfdsf'}, True),
    ('ou_admin', '{normal_user}', {'description': 'dsfdsf'}, True),
    ('admin', 'uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, True),
    ('ou_admin', 'uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_modify_attr(ldap_base, bremen_ou, login_user, user_dn, changes, expected):
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(bremen_ou.ouadmin_username, 'univention')
    changes['$dn$'] = user_dn.format(normal_user=bremen_ou.user_dn, ldap_base=ldap_base)
    options = [
        {
            "object": changes,
        },
    ]
    if not expected:
        with pytest.raises(Forbidden):
            client.umc_command('udm/put', options, 'users/user')
    else:
        res = client.umc_command('udm/put', options, 'users/user').result
        assert res
        assert res[0]['$dn$'] == user_dn.format(admin_ou=bremen_ou.ouadmin_dn, normal_user=bremen_ou.user_dn, ldap_base=ldap_base)
