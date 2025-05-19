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
from univention.lib.umc import Forbidden, HTTPError
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(not _ucr.is_true('umc/udm/delegation'), reason='umc/udm/delegation not activated')


@pytest.fixture
def ou(ldap_base):
    return SimpleNamespace(
        dn=f'ou=ou1,{ldap_base}',
        admin_username='ou1admin',
        admin_dn=f'uid=ou1admin,cn=users,{ldap_base}',
        user_username='user1-ou1',
        user_dn=f'uid=user1-ou1,cn=users,ou=ou1,{ldap_base}',
        user_default_container=f'cn=users,ou=ou1,{ldap_base}',
        group_default_container=f'cn=groups,ou=ou1,{ldap_base}',
    )


@check_delegation
def test_ouadmin_default_containers(ou, ldap_base):
    client = Client()
    client.authenticate(ou.admin_username, 'univention')
    res = client.umc_command('udm/containers', {"objectType": "users/user"}, 'users/user').result
    assert {x['id'] for x in res} == {ou.user_default_container}
    res = client.umc_command('udm/containers', {"objectType": "groups/group"}, 'groups/group').result
    assert {x['id'] for x in res} == {ou.group_default_container, f'cn=groups,{ldap_base}'}


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
def test_delete(ou, ldap_base, random_username, login_user, position, expected, udm):
    cn_user = udm.create_object(
        'users/user',
        lastname=random_username(),
        username=random_username(),
        password='univention',
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    client = Client()
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client.authenticate(ou.admin_username, 'univention')
    options = [{
        'object': cn_user,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]
    res = client.umc_command('udm/remove', options, 'users/user').result[0]
    if not expected:
        assert not res['success']
        assert res['details'].startswith('No such object:')
    else:
        assert res['success']


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
def test_create(ou, ldap_base, random_username, login_user, position, expected):
    client = Client()
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client.authenticate(ou.admin_username, 'univention')
    options = [{
        'object': {
            'lastname': random_username(),
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": position.format(ou_dn=ou.dn, ldap_base=ldap_base),
            "objectType": "users/user",
        },
    }]
    res = client.umc_command('udm/add', options, 'users/user').result[0]
    if not expected:
        assert not res['success']
        assert res['details'] == 'Permission denied.'
    else:
        assert res['success']


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
def test_search(random_username, ou, login_user, objectProperty, objectPropertyValue, expected, udm):
    dn_test = None
    if objectProperty != "None":
        config = {
            'username': random_username(),
            'lastname': random_username(),
            'password': 'univention',
            objectProperty: "test",
        }
        if login_user == "ou_admin":
            config['position'] = ou.dn
        dn_test = udm.create_object('users/user', **config)
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(ou.admin_username, 'univention')
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
        all_objects = udm.list_objects('users/user', properties=["DN"]) if login_user == "admin" else udm.list_objects('users/user', properties=["DN"], position=ou.dn)
        assert {obj[0] for obj in all_objects} == {x['$dn$'] for x in res}
    if "admin" in expected:
        assert "Administrator" in names, "Administrator not found"
    if objectProperty != "None":
        rex = re.compile(objectPropertyValue.replace('*', '.*'))
        assert all(rex.match(x[objectProperty]) for x in res)
        assert dn_test in [x['$dn$'] for x in res]
    if "not-self" in expected:
        assert ou.admin_username not in names, f"{ou.normal_user_username} found"


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
def test_move(ldap_base, ou, login_user, user_dn, target_position, expected, udm, random_username):

    dn = udm.create_object(
        'users/user',
        lastname=random_username(),
        username=random_username(),
        password='univention',
        position=ou.dn,
    )

    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(ou.admin_username, 'univention')
    options = [{
        'object': user_dn.format(admin_ou=ou.admin_dn, normal_user=dn, ldap_base=ldap_base),
        "options": {
            "container": target_position.format(ou_dn=ou.dn, ldap_base=ldap_base, ou_cn_users=ou.user_default_container),
        },
    }]
    result = client.umc_command('udm/move', options, 'users/user').result
    res = wait_for_progress(client, result['id']).result['intermediate'][0]
    if not expected:
        assert not res['success']
        assert res['details'] == 'Permission denied.'
    else:
        assert res['success']


@check_delegation
@pytest.mark.parametrize('login_user, user_dn, attribute, expected', [
    ('admin', 'uid=Administrator,cn=users,{ldap_base}', 'guardianInheritedRoles', True),
    ('ou_admin', 'uid=Administrator,cn=users,{ldap_base}', None, False),
    ('admin', '{admin_ou}', 'guardianRoles', True),
    ('ou_admin', '{admin_ou}', None, False),
    ('admin', '{normal_user}', 'guardianRoles', True),
    ('ou_admin', '{normal_user}', None, True),
    ('ou_admin', '{normal_user}', 'guardianRoles', True),
])
def test_read(ldap_base, ou, login_user, user_dn, attribute, expected):
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(ou.admin_username, 'univention')
    options = [
        user_dn.format(admin_ou=ou.admin_dn, normal_user=ou.user_dn, ldap_base=ldap_base),
    ]
    if not expected:

        # TODO: why do we get HTTPError, should this return permissionDenied?
        #  File "/usr/lib/python3/dist-packages/univention/management/console/modules/udm/__init__.py", line 265, in get_obj_module
        #    return get_obj_module(flavor, ldap_dn, self.get_ldap_connection()[0])
        #           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #  File "/usr/lib/python3/dist-packages/univention/management/console/modules/udm/udm_ldap.py", line 1239, in get_obj_module
        #    return module.get(ldap_dn, attributes=attr), module
        #           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #  File "/usr/lib/python3/dist-packages/univention/management/console/modules/udm/udm_ldap.py", line 742, in get
        #    UDM_Error(exc).reraise()
        #  File "/usr/lib/python3/dist-packages/univention/management/console/modules/udm/udm_ldap.py", line 375, in reraise
        #    raise self.with_traceback(self.exc_info[2])
        #  File "/usr/lib/python3/dist-packages/univention/management/console/modules/udm/udm_ldap.py", line 735, in get
        #    obj.acls.is_receive_allowed(obj)
        #  File "/usr/lib/python3/dist-packages/univention/admin/authorization.py", line 393, in is_receive_allowed
        #    return may_read(obj, self._user_roles(obj))
        #           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #  File "/usr/lib/python3/dist-packages/univention/admin/authorization.py", line 291, in may_read
        #    raise permissionDenied()
        # univention.management.console.modules.udm.udm_ldap.UDM_Error: Permission denied
        with pytest.raises(HTTPError):
            client.umc_command('udm/get', options, 'users/user')
    else:
        res = client.umc_command('udm/get', options, 'users/user').result
        assert res
        assert res[0]['$dn$'] == user_dn.format(admin_ou=ou.admin_dn, normal_user=ou.user_dn, ldap_base=ldap_base)
        if attribute:
            print(res[0])
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
def test_modify_attr(ldap_base, ou, login_user, user_dn, changes, expected, udm, random_username):
    dn = udm.create_object(
        'users/user',
        lastname=random_username(),
        username=random_username(),
        password='univention',
        position=ou.user_default_container,
    )
    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(ou.admin_username, 'univention')
    changes['$dn$'] = user_dn.format(normal_user=dn, ldap_base=ldap_base)
    res = client.umc_command('udm/put', [{'object': changes}], 'users/user').result[0]
    if not expected:
        assert not res['success']
        assert res['details'] in ('Permission denied.', f'No such object: {user_dn.format(normal_user=user_dn, ldap_base=ldap_base)}.')
    else:
        assert res['success']
        assert res['$dn$'] == user_dn.format(admin_ou=ou.admin_dn, normal_user=dn, ldap_base=ldap_base)


@check_delegation
@pytest.mark.parametrize('login_user, expected', [
    ('admin', True),
    ('ou_admin', False),
])
def test_mail_domain_remove(ldap_base, ou, random_username, login_user, expected, udm):
    domain_name = f"{random_username()}.test.com"
    mail_domain_dn = udm.create_object('mail/domain', name=domain_name)

    if login_user == "admin":
        client = Client.get_test_connection()
    elif login_user == "ou_admin":
        client = Client()
        client.authenticate(ou.admin_username, 'univention')

    options = [{
        'object': mail_domain_dn,
        "options": {
            "cleanup": True,
            "recursive": True,
        },
    }]

    # TODO: why do we get Forbidden, should this return noObject?
    if not expected:
        with pytest.raises(Forbidden):
            client.umc_command('udm/remove', options, 'mail/domain')
    else:
        res = client.umc_command('udm/remove', options, 'mail/domain').result[0]
        assert res['success']
