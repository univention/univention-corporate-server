#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import re
import subprocess

import pytest

from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


def test_default_containers(admin_umc_client, udm):
    container = udm.list_objects('container/cn', attr=['userPath'])
    user_container = {x[0] for x in container if x[1].get('userPath') == ['1']}
    group_container = {x[0] for x in container if x[1].get('groupPath') == ['1']}
    res = admin_umc_client.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert {x['id'] for x in res} == user_container
    res = admin_umc_client.umc_command('udm/containers', {'objectType': 'groups/group'}, 'groups/group').result
    assert {x['id'] for x in res} == group_container


@pytest.mark.parametrize('position', [
    ('cn=users,{ldap_base}'),
    ('cn=users,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_user_delete(ou, ldap_base, random_username, position, udm, admin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    res = admin_umc_client.delete_object('users/user', dn)
    assert res['success']


@pytest.mark.parametrize('position', [
    ('cn=users,{ldap_base}'),
    ('cn=users,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_user_create(ou, ldap_base, random_username, position, admin_umc_client):
    res = admin_umc_client.create_user(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    assert res['success']
    admin_umc_client.delete_object('users/user', res['$dn$'])


@pytest.mark.parametrize('position', [
    ('cn=groups,{ldap_base}'),
    ('cn=groups,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_group_create(ou, ldap_base, position, admin_umc_client):
    res = admin_umc_client.create_group(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    assert res['success']
    admin_umc_client.delete_object('groups/group', res['$dn$'])


@pytest.mark.parametrize('position', [
    ('cn=groups,{ldap_base}'),
    ('cn=groups,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_delete_group(ou, ldap_base, position, udm, random_username, admin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    res = admin_umc_client.delete_object('groups/group', dn)
    assert res['success']


@pytest.mark.parametrize('group_position, group_target_position', [
    ('cn=groups,{ou_dn}', 'cn=groups,{ldap_base}'),
    ('cn=groups,{ldap_base}', '{ou_cn_groups}'),
])
def test_move_group(ldap_base, ou, group_position, group_target_position, udm, random_username, admin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=group_position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    position = group_target_position.format(ou_dn=ou.dn, ldap_base=ldap_base, ou_cn_groups=ou.group_default_container)
    res = admin_umc_client.move_object('groups/group', dn, position)
    assert res['success']


@pytest.mark.parametrize('group_position, changes', [
    ('cn=groups,{ldap_base}', {'description': 'dsfdsf'}),
    ('cn=groups,{ou_dn}', {'guardianMemberRoles': 'app:namespace:role'}),
    ('{ou_dn}', {'description': 'dsfdsf'}),
    ('{ldap_base}', {'guardianMemberRoles': 'app:namespace:role'}),
])
def test_modify_group(ou, ldap_base, random_username, udm, group_position, changes, admin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=group_position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    res = admin_umc_client.modify_object('groups/group', dn, changes)
    assert res['success']


@pytest.mark.parametrize('objectProperty, objectPropertyValue, expected', [
    ('None', '', ['all']),
    ('None', '*trator', ['admin']),
    ('description', 'test', ['cn_test']),
    ('description', 'tes*', ['cn_test']),
    ('description', '*est', ['cn_test']),
])
def test_user_search(random_username, ou, objectProperty, objectPropertyValue, expected, udm, admin_umc_client):
    dn_test = None
    if objectProperty != 'None':
        config = {
            'username': random_username(),
            'lastname': random_username(),
            'password': 'univention',
            objectProperty: 'test',
        }
        dn_test = udm.create_object('users/user', **config)
    options = {
        'container': 'all',
        'hidden': 'all' in expected,
        'objectType': 'users/user',
        'objectProperty': objectProperty,
        'objectPropertyValue': objectPropertyValue,
        'fields': [
            'name',
            'path',
            'displayName',
            'mailPrimaryAddress',
            'firstname',
            'lastname',
        ],
    }
    res = admin_umc_client.umc_command('udm/query', options, 'users/user').result
    names = [x['name'] for x in res]
    assert res
    if 'all' in expected:
        all_objects = udm.list_objects('users/user', properties=['DN'])
        assert {obj[0] for obj in all_objects} == {x['$dn$'] for x in res}
    if 'admin' in expected:
        assert 'Administrator' in names, 'Administrator not found'
    if objectProperty != 'None':
        rex = re.compile(objectPropertyValue.replace('*', '.*'))
        assert all(rex.match(x[objectProperty]) for x in res)
        assert dn_test in [x['$dn$'] for x in res]
    if 'not-self' in expected:
        assert ou.admin_username not in names, f'{ou.normal_user_username} found'


@pytest.mark.parametrize('position, target_position', [
    ('cn=users,{ou_dn}', 'cn=users,{ldap_base}'),
    ('cn=users,{ldap_base}', '{ou_cn_users}'),
])
def test_user_move(ldap_base, ou, position, target_position, udm, admin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    position = target_position.format(ou_dn=ou.dn, ldap_base=ldap_base, ou_cn_users=ou.user_default_container)
    res = admin_umc_client.move_object('users/user', dn, position)
    assert res['success']


@pytest.mark.parametrize('user_dn, attribute', [
    ('uid=Administrator,cn=users,{ldap_base}', 'guardianInheritedRoles'),
    ('{admin_ou}', 'guardianRoles'),
    ('{normal_user}', 'guardianRoles'),
])
def test_user_read(ldap_base, ou, user_dn, attribute, admin_umc_client):
    dn = user_dn.format(admin_ou=ou.admin_dn, normal_user=ou.user_dn, ldap_base=ldap_base)
    res = admin_umc_client.get_object('users/user', dn)
    assert res['$dn$'] == dn
    if attribute:
        assert attribute in res
        assert res[attribute]


@pytest.mark.parametrize('position, changes', [
    ('cn=users,{ou_dn}', {'guardianRoles': ['udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen']}),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}),
    ('cn=users,{ldap_base}', {'description': 'dsfdsf'}),
])
def test_user_modify(ldap_base, ou, position, changes, udm, admin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    res = admin_umc_client.modify_object('users/user', dn, changes)
    assert res['success']
    assert res['$dn$'] == dn


def test_mail_domain_remove(ldap_base, udm, admin_umc_client, random_username):
    domain_name = f'{random_username()}.test.com'
    mail_domain_dn = udm.create_object('mail/domain', name=domain_name, position=f'cn=domain,cn=mail,{ldap_base}')
    res = admin_umc_client.delete_object('mail/domain', mail_domain_dn)
    assert res['success']


def test_mail_domain_create(ldap_base, random_username, udm, admin_umc_client):
    domain_name = f'{random_username()}.test.com'
    position = f'cn=domain,cn=mail,{ldap_base}'
    res = admin_umc_client.create_mail_domain(domain_name, position)
    assert res['success']
    domains = udm.list_objects('mail/domain')
    assert res['$dn$'] in [x[0] for x in domains]
    admin_umc_client.delete_object('mail/domain', res['$dn$'])


@pytest.mark.parametrize('position', [
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_query_and_read_mail_domain(udm, ldap_base, ou, position, admin_umc_client) -> None:
    position = position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    domain_name = f'test-{ou.user_username}.com'
    object_dn = f'cn={domain_name},{position}'
    query_options = {
        'container': 'all',
        'hidden': False,
        'objectType': 'mail/domain',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': [
            'name',
            'labelObjectType',
            'path',
        ],
    }
    get_option = [
        object_dn,
    ]

    # get (should be impossible, as not created yet)
    with pytest.raises(BadRequest):
        admin_umc_client.umc_command('udm/get', get_option, 'mail/domain')  # type: ignore[call-arg]

    # create
    udm.create_object(
        'mail/domain',
        name=domain_name,
        position=position,
    )

    # query
    res = admin_umc_client.umc_command('udm/query', query_options, 'mail/mail').result  # type: ignore[call-arg]
    assert object_dn in [x['$dn$'] for x in res]
    assert len(res) == len(udm.list_objects('mail/domain', properties=['DN']))

    # get (should be possible)
    res = admin_umc_client.umc_command('udm/get', get_option, 'mail/domain').result  # type: ignore[call-arg]
    assert res
    assert res[0]['$dn$'] == object_dn
    assert len(res) == 1

    # delete
    udm.remove_object('mail/domain', dn=object_dn)

    # query all should be empty
    res = admin_umc_client.umc_command('udm/query', query_options, 'mail/mail').result  # type: ignore[call-arg]
    assert len(res) == len(udm.list_objects('mail/mail', properties=['DN']))

    # get (should not be possible)
    with pytest.raises(BadRequest):
        admin_umc_client.umc_command('udm/get', get_option, 'mail/mail')  # type: ignore[call-arg]


def test_syntax_choices_admin(admin_umc_client):
    for syntax in ['UserDN', 'GroupDN', 'UserID', 'GroupID']:
        res = admin_umc_client.umc_command('udm/syntax/choices', {'syntax': syntax}, 'shares/share')
        assert res.result


def test_syntax_choices(udm, ou, admin_umc_client):
    """
    Test that UserDN filtering works differently based on user roles.
    OU admin should only see users from their own OU.
    Domain admin should see all users.
    """
    res = admin_umc_client.umc_command('udm/syntax/choices', {'syntax': 'UserDN'}, 'shares/share').result
    assert len(res) == len(udm.list_objects('users/user', properties=['DN']))

    res = admin_umc_client.umc_command('udm/syntax/choices', {'syntax': 'UserID'}, 'shares/share').result
    # all user + root
    assert len(res) == len(udm.list_objects('users/user', properties=['DN'])) + 1


def test_shares_create_admin(ldap_base, random_username, admin_umc_client):
    # get default container
    res = admin_umc_client.umc_command('udm/containers', {'objectType': 'shares/share'}, 'shares/share').result
    assert res
    # syntax choices
    res = admin_umc_client.umc_command('udm/syntax/choices', {'syntax': 'UCS_Server'}, 'shares/share').result
    assert res
    # create share
    options = [{
        'object': {
            'name': random_username(),
            'host': f'{random_username()}.{random_username()}',
            'path': f'/{random_username()}',
        },
        'options': {
            'container': ldap_base,
            'objectType': 'shares/share',
        },
    }]
    res = admin_umc_client.umc_command('udm/add', options, 'shares/share').result[0]
    assert res['success']
    admin_umc_client.delete_object('shares/share', res['$dn$'])
