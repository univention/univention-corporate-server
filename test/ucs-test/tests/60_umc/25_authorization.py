#!/usr/share/ucs-test/runner pytest-3 -s
## desc: TODO
## bugs: [TODO]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

from types import SimpleNamespace
from unittest import mock

import pytest

from univention.config_registry import ucr as _ucr
from univention.testing.umc import Client


if not _ucr.is_true('umc/udm/delegation'):
    pytest.skip('umc/udm/delegation not set', allow_module_level=True)


@pytest.fixture()
def bremen_ou(udm):
    dn_ou = udm.create_object('container/ou', name='bremen')
    dn_user = udm.create_object('users/user', username='bremen_admin', guardianRoles=['umc:udm:ouadmin&umc:udm:ou=bremen'], lastname='bremen_admin', password='univention')
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
            "container": bremen_ou.ou_dn,
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


def create_mock_object(dn, position, module):
    obj = mock.MagicMock()
    if dn:
        obj.dn = dn
    if position:
        obj.position.getDn.return_value = position
    else:
        obj.position.getDn.return_value = dn.split(',', 1)[1]
    obj.module = module
    return obj


def test_check_permissions_create():
    from univention.management.console.modules.udm.authorization import _check_permissions_create, _get_capablities

    caps = _get_capablities({'domainadmin': []})
    assert caps
    assert _check_permissions_create(create_mock_object(None, 'ou=hans', 'users/user'), caps)
    # assert _check_permissions_create(create_mock_object(None, 'CONTEXT', 'users/user'), caps)
    assert _check_permissions_create(create_mock_object(None, 'xyz', 'users/user'), caps)
    assert _check_permissions_create(create_mock_object(None, 'dc=bla', 'whatever'), caps)

    caps = _get_capablities({'ouadmin': []})
    assert caps
    assert not _check_permissions_create(create_mock_object(None, f'cn=users,{_ucr["ldap/base"]}', 'users/user'), caps)
    # assert _check_permissions_create(create_mock_object(None, 'CONTEXT', 'users/user'), caps)
    assert _check_permissions_create(create_mock_object(None, f'cn=domain,cn=mail,{_ucr["ldap/base"]}', 'mail/domain'), caps)
    assert not _check_permissions_create(create_mock_object(None, 'dc=bla', 'whatever'), caps)


def test_check_permissions_read():
    ldap_base = _ucr["ldap/base"]
    from univention.management.console.modules.udm.authorization import ROLES, _check_permissions_read, _get_capablities
    ROLES["test_ouadmin"] = [
        # ouadmin can read and write all attributes of all udm modules in the ou except guardianRole attributes
        {
            "target": {
                "position": "cn=users,ou=ou1",
            },
            "permissions": {
                "*": {
                    "attributes": {
                        "*": "write",
                        "guardianRole": "read",
                        "guardianMemberRoles": "read",
                    },
                    "create": True,
                    "delete": True,
                },
            },
        },
    ]

    objs = [
        f"uid=Administrator,cn=users,{ldap_base}",
        f"uid=join-backup,cn=users,{ldap_base}",
        f"uid=join-slave,cn=users,{ldap_base}",
        f"uid=krbkeycloak,cn=users,{ldap_base}",
        f"uid=Guest,cn=users,{ldap_base}",
        f"uid=krbtgt,cn=users,{ldap_base}",
        f"uid=dns-ucs-5833,cn=users,{ldap_base}",
        f"uid=ou1admin,cn=users,{ldap_base}",
        f"uid=user1-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user2-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user3-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user4-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user5-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user6-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user7-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user8-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user9-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=user10-ou1,cn=users,ou=ou1,{ldap_base}",
        f"uid=ou2admin,cn=users,{ldap_base}",
        f"uid=user1-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user2-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user3-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user4-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user5-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user6-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user7-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user8-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user9-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=user10-ou2,cn=users,ou=ou2,{ldap_base}",
        f"uid=ou3admin,cn=users,{ldap_base}",
        f"uid=user1-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user2-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user3-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user4-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user5-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user6-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user7-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user8-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user9-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=user10-ou3,cn=users,ou=ou3,{ldap_base}",
        f"uid=ou4admin,cn=users,{ldap_base}",
        f"uid=user1-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user2-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user3-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user4-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user5-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user6-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user7-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user8-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user9-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=user10-ou4,cn=users,ou=ou4,{ldap_base}",
        f"uid=ou5admin,cn=users,{ldap_base}",
        f"uid=user1-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user2-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user3-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user4-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user5-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user6-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user7-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user8-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user9-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=user10-ou5,cn=users,ou=ou5,{ldap_base}",
        f"uid=ou6admin,cn=users,{ldap_base}",
        f"uid=user1-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user2-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user3-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user4-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user5-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user6-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user7-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user8-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user9-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=user10-ou6,cn=users,ou=ou6,{ldap_base}",
        f"uid=ou7admin,cn=users,{ldap_base}",
        f"uid=user1-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user2-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user3-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user4-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user5-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user6-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user7-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user8-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user9-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=user10-ou7,cn=users,ou=ou7,{ldap_base}",
        f"uid=ou8admin,cn=users,{ldap_base}",
        f"uid=user1-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user2-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user3-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user4-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user5-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user6-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user7-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user8-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user9-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=user10-ou8,cn=users,ou=ou8,{ldap_base}",
        f"uid=ou9admin,cn=users,{ldap_base}",
        f"uid=user1-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user2-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user3-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user4-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user5-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user6-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user7-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user8-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user9-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=user10-ou9,cn=users,ou=ou9,{ldap_base}",
        f"uid=ou10admin,cn=users,{ldap_base}",
        f"uid=user1-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user2-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user3-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user4-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user5-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user6-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user7-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user8-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user9-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=user10-ou10,cn=users,ou=ou10,{ldap_base}",
        f"uid=test1,cn=users,{ldap_base}",
    ]
    objs_mock = [create_mock_object(obj, None, 'users/user') for obj in objs]
    caps = _get_capablities({'domainadmin': []})
    assert caps
    assert set(_check_permissions_read(objs_mock, caps)) == set(objs_mock)
    assert set(_check_permissions_read(objs, caps)) == set(objs)

    caps = _get_capablities({'test_ouadmin': []})
    assert caps
    assert set(_check_permissions_read(objs_mock, caps)) == {obj for obj in objs_mock if "cn=users,ou=ou1," in obj.dn}
    assert set(_check_permissions_read(objs, caps)) == {obj for obj in objs if "cn=users,ou=ou1," in obj}
