#!/usr/share/ucs-test/runner pytest-3 -s
## desc: TODO
## bugs: [TODO]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

from types import SimpleNamespace

import pytest

from univention.config_registry import ucr as _ucr
from univention.lib.umc import Forbidden
from univention.testing.umc import Client


if not _ucr.is_true('umc/udm/delegation'):
    pytest.skip('umc/udm/delegation not set', allow_module_level=True)


@pytest.fixture()
def bremen_ou(udm, random_username):
    dn_ou = udm.create_object('container/ou', name='bremen')
    ouadmin_username = random_username()
    dn_admin = udm.create_object('users/user', username=ouadmin_username, guardianRoles=['umc:udm:ouadmin&umc:udm:ou=bremen'], lastname='bremen_admin', password='univention')
    dn_user = udm.create_object('users/user', username=random_username(), position=dn_ou, lastname='lastname', password='univention')
    # set user default container
    udm.modify_object('container/ou', dn=dn_ou, userPath='1')
    udm.modify_object('container/ou', dn=dn_ou, groupPath='1')
    yield SimpleNamespace(
        ou_dn=dn_ou,
        ouadmin_dn=dn_admin,
        ouadmin_username=ouadmin_username,
        user_dn=dn_user,
        user_default_container=dn_ou,
        group_default_container=dn_ou,
    )
    udm.remove_object('container/ou', dn=dn_ou)
    udm.remove_object('users/user', dn=dn_admin)


def test_ouadmin_default_containers(bremen_ou, ldap_base):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    res = client.umc_command('udm/containers', {"objectType": "users/user"}, 'users/user').result
    assert {x['id'] for x in res} == {bremen_ou.user_default_container}
    res = client.umc_command('udm/containers', {"objectType": "groups/group"}, 'groups/group').result
    assert {x['id'] for x in res} == {bremen_ou.group_default_container, f'cn=groups,{ldap_base}'}


def test_ouadmin_can_delete_user(bremen_ou):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': bremen_ou.user_dn,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]
    client.umc_command('udm/remove', options, 'users/user')


def test_ouadmin_can_not_delete_user(bremen_ou):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': bremen_ou.ouadmin_dn,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]
    with pytest.raises(Forbidden):
        client.umc_command('udm/remove', options, 'users/user')


def test_ouadmin_can_create_user(bremen_ou, random_username):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': {
            'lastname': 'lastname',
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": bremen_ou.ou_dn,
            "objectType": "users/user",
        },
    }]
    client.umc_command('udm/add', options, 'users/user')


def test_ouadmin_can_not_create_user(bremen_ou, ldap_base, random_username):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': {
            'lastname': 'lastname',
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": ldap_base,
            "objectType": "users/user",
        },
    }]
    with pytest.raises(Forbidden):
        client.umc_command('udm/add', options, 'users/user')


def test_ouadmin_can_modify_user(bremen_ou):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': {
            'description': 'dsfdsf',
            '$dn$': bremen_ou.user_dn,
        },
    }]
    client.umc_command('udm/put', options, 'users/user')


def test_ouadmin_can_not_modify_user(bremen_ou, ldap_base):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')
    options = [{
        'object': {
            'description': 'dsfdsf',
            '$dn$': f'uid=Administrator,cn=users,{ldap_base}',
        },
    }]
    with pytest.raises(Forbidden):
        client.umc_command('udm/put', options, 'users/user')


def test_domainadmin_can_create_user(random_username, ldap_base):
    client = Client.get_test_connection()
    options = [{
        'object': {
            'lastname': random_username(),
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": f"cn=users,{ldap_base}",
            "objectType": "users/user",
        },
    }]
    client.umc_command('udm/add', options, 'users/user')
    options = [{
        'object': {
            'lastname': random_username(),
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": ldap_base,
            "objectType": "users/user",
        },
    }]
