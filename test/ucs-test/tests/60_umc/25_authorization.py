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
from univention.testing.umc import Client


if not _ucr.is_true('umc/udm/delegation'):
    pytest.skip('umc/udm/delegation not set', allow_module_level=True)


@pytest.fixture()
def bremen_ou(udm):
    dn_ou = udm.create_object('container/ou', name='bremen')
    # FIXME = is not allowed in guardianRoles
    # dn_user = udm.create_object('users/user', username='bremen_admin', guardianRoles=['umc:udm:ouadmin&umc:udm:ou=bremen'])
    dn_user = udm.create_object('users/user', username='bremen_admin', guardianRoles=['umc:udm:ouadmin&umc:udm:bremen'], lastname='bremen_admin', password='univention')
    yield SimpleNamespace(ou_dn=dn_ou, ouadmin_dn=dn_user, ouadmin_username='bremen_admin')
    udm.remove_object('users/user', dn=dn_user)
    udm.remove_object('container/ou', dn=dn_ou)


def test_ouadmin_user_create_in_different_ou(bremen_ou):
    client = Client()
    client.authenticate(bremen_ou.ouadmin_username, 'univention')

    options = [{
        'object': {
            'lastname': 'testou1',
            'username': 'testou1',
            'password': 'univention',
        },
        "options": {
            "container": "cn=users," + _ucr['ldap/base'],
            "objectType": "users/user",
        },
    }]
    client.umc_command('udm/add', options, 'users/user')


def test_domainadmin_create_user_everywhere():
    client = Client.get_test_connection()
    options = [{
        'object': {
            'lastname': 'test1',
            'username': 'test1',
            'password': 'univention',
        },
        "options": {
            "container": "cn=users," + _ucr['ldap/base'],
            "objectType": "users/user",
        },
    }]
    client.umc_command('udm/add', options, 'users/user')


def test_check_permissions_create():
    from univention.management.console.modules.udm.authorization import _check_permissions_create, _get_capablities

    caps = _get_capablities(['domainadmin'])
    assert caps
    assert _check_permissions_create('ou=hans', 'users/user', caps)
    assert _check_permissions_create('CONTEXT', 'users/user', caps)
    assert _check_permissions_create('xyz', 'users/user', caps)

    caps = _get_capablities(['ouadmin'])
    assert caps
    assert not _check_permissions_create(f'cn=users,{_ucr["ldap/base"]}', 'users/user', caps)
    assert _check_permissions_create('CONTEXT', 'users/user', caps)
    assert _check_permissions_create(f'cn=domain,cn=mail,{_ucr["ldap/base"]}', 'mail/domain', caps)
