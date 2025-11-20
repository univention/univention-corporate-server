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
from conftest import translate

from univention.admin.recyclebin import RECYCLEBIN_BASE
from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')
pytest_plugins = ('univention.testing.fixtures_recyclebin')


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


def test_can_not_query_recyclebin(ouadmin_umc_client):
    options = {
        'hidden': False,
        'objectType': 'recyclebin/removedobject',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'originalObjectType', 'path'],
    }
    with pytest.raises(BadRequest) as err:
        ouadmin_umc_client.umc_command('udm/query', options, 'recyclebin/removedobject')
    assert RECYCLEBIN_BASE in err.value.message


def test_can_not_restore(deleted_user_object, ouadmin_umc_client, lo):
    _, deleted_dn = deleted_user_object
    options = [{'object': deleted_dn}]
    res = ouadmin_umc_client.umc_command('udm/restore', options, 'recyclebin/removedobject').result
    assert res[0]['success'] is False
    assert res[0]['details'] == translate('Permission denied.')


def test_default_containers(ou, ldap_base, ouadmin_umc_client):
    res = ouadmin_umc_client.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert {x['id'] for x in res} == {ou.user_default_container}
    res = ouadmin_umc_client.umc_command('udm/containers', {'objectType': 'groups/group'}, 'groups/group').result
    assert {x['id'] for x in res} == {ou.group_default_container}


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('{ou_dn}', True),
    ('cn=users,{ldap_base}', False),
    ('{ldap_base}', False),
])
def test_user_delete(ou, ldap_base, position, expected, udm, ouadmin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    res = ouadmin_umc_client.delete_object('users/user', dn)
    if not expected:
        assert not res['success']
        assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('{ou_dn}', True),
    ('cn=users,{ldap_base}', False),
    ('{ldap_base}', False),
])
def test_user_create(ou, ldap_base, position, expected, ouadmin_umc_client):
    res = ouadmin_umc_client.create_user(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if not expected:
        assert not res['success']
        assert res['details'] == translate('Permission denied.')
    else:
        assert res['success']


@pytest.mark.parametrize('position, expected', [
    ('cn=groups,{ou_dn}', True),
    ('{ou_dn}', True),
    ('{ldap_base}', False),
])
def test_create_group(ou, ldap_base, position, expected, ouadmin_umc_client):
    res = ouadmin_umc_client.create_group(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if not expected:
        assert not res['success']
        assert res['details'] == translate('Permission denied.')
    else:
        assert res['success']
        ouadmin_umc_client.delete_object('groups/group', res['$dn$'])


@pytest.mark.parametrize('position, expected', [
    ('cn=groups,{ou_dn}', True),
    ('{ou_dn}', True),
    ('{ldap_base}', False),
])
def test_delete_group(ou, ldap_base, random_username, position, expected, udm, ouadmin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    res = ouadmin_umc_client.delete_object('groups/group', dn)
    if not expected:
        assert not res['success']
        assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']


@pytest.mark.parametrize('group_position, group_target_position, expected', [
    ('cn=groups,{ldap_base}', '{ou_cn_groups}', False),
    ('cn=groups,{ou_dn}', 'cn=groups,{ldap_base}', False),
    ('cn=groups,{ou_dn}', '{ou_dn}', True),
])
def test_move_group(ldap_base, ou, group_position, group_target_position, expected, udm, random_username, ouadmin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=group_position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    position = group_target_position.format(ou_dn=ou.dn, ldap_base=ldap_base, ou_cn_groups=ou.group_default_container)
    res = ouadmin_umc_client.move_object('groups/group', dn, position)
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == translate('Permission denied.')
        else:
            assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']


@pytest.mark.parametrize('group_position, changes, expected', [
    ('cn=groups,{ldap_base}', {'description': 'dsfdsf'}, False),
    ('cn=groups,{ou_dn}', {'guardianMemberRoles': 'app:namespace:role'}, False),
    ('cn=groups,{ou_dn}', {'description': 'dsfdsf'}, True),
    ('{ou_dn}', {'description': 'dsfdsf'}, True),
    ('{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_modify_group(ou, ldap_base, random_username, udm, group_position, changes, expected, ouadmin_umc_client):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=group_position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    res = ouadmin_umc_client.modify_object('groups/group', dn, changes)
    if not expected:
        assert not res['success']
        assert res['details'] == translate('Permission denied.') or res['details'].startswith(translate('No such object:'))
    else:
        assert res['success']


@pytest.mark.parametrize('objectProperty, objectPropertyValue, container, expected', [
    ('None', '', 'all', ['all']),
    ('description', 'test', 'all', ['cn_test']),
    ('description', 'tes*', 'all', ['cn_test']),
    ('description', '*est', 'all', ['cn_test']),
    ('None', '', 'default', ['default', 'not-self']),
])
def test_user_search(random_username, ou, objectProperty, objectPropertyValue, container, expected, udm, ouadmin_umc_client, sub_container_with_user):
    dn_test = None
    if objectProperty != 'None':
        config = {
            'username': random_username(),
            'lastname': random_username(),
            'password': 'univention',
            objectProperty: 'test',
        }
        config['position'] = ou.dn
        dn_test = udm.create_object('users/user', **config)
    options = {
        'container': container,
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
    res = ouadmin_umc_client.umc_command('udm/query', options, 'users/user').result
    names = [x['name'] for x in res]
    assert res
    if 'all' in expected:
        all_objects = [*udm.list_objects('users/user', properties=['DN'], position=ou.dn), [ou.admin_dn]]
        assert sorted([obj[0] for obj in all_objects]) == sorted([x['$dn$'] for x in res])
    if 'default' in expected:
        all_objects = udm.list_objects('users/user', properties=['DN'], position=f'cn=users,{ou.dn}')
        assert sorted([obj[0] for obj in all_objects]) == sorted([x['$dn$'] for x in res])
    if objectProperty != 'None':
        rex = re.compile(objectPropertyValue.replace('*', '.*'))
        assert all(rex.match(x[objectProperty]) for x in res)
        assert dn_test in [x['$dn$'] for x in res]
    if 'not-self' in expected:
        assert ou.admin_username not in names


@pytest.mark.parametrize('position, target_position, expected', [
    ('cn=users,{ou_dn}', 'cn=users,{ldap_base}', False),
    ('cn=users,{ldap_base}', 'cn=users,{ou_dn}', False),
    ('{ou_dn}', 'cn=users,{ou_dn}', True),
])
def test_user_move(ldap_base, ou, position, target_position, expected, udm, ouadmin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    position = target_position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    res = ouadmin_umc_client.move_object('users/user', dn, position)
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == translate('Permission denied.')
        else:
            assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']


@pytest.mark.parametrize('user_dn, attribute, expected', [
    ('uid=Administrator,cn=users,{ldap_base}', None, False),
    ('{admin_ou}', None, True),
    ('{admin2_ou}', None, False),
    ('{normal_user}', None, True),
    ('{normal_user}', 'lastname', True),
])
def test_user_read(ldap_base, ou, user_dn, attribute, expected, ouadmin_umc_client):
    dn = user_dn.format(admin_ou=ou.admin_dn, admin2_ou=ou.admin_dn2, normal_user=ou.user_dn, ldap_base=ldap_base)
    if not expected:
        with pytest.raises(BadRequest):
            ouadmin_umc_client.get_object('users/user', dn)
    else:
        res = ouadmin_umc_client.get_object('users/user', dn)
        assert res['$dn$'] == dn
        if attribute:
            assert attribute in res
            assert res[attribute]


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=users,{ou_dn}', {'guardianRoles': ['udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen']}, False),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}, True),
    ('cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_user_modify(ldap_base, ou, position, changes, expected, udm, ouadmin_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    res = ouadmin_umc_client.modify_object('users/user', dn, changes)
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == translate('Permission denied.')
        else:
            assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']
        assert res['$dn$'] == dn


def test_mail_domain_remove(ldap_base, random_username, udm, ouadmin_umc_client):
    domain_name = f'{random_username()}.test.com'
    mail_domain_dn = udm.create_object('mail/domain', name=domain_name)
    res = ouadmin_umc_client.delete_object('mail/domain', mail_domain_dn)
    assert not res['success']
    assert res['details'] == f'{translate("No such object:")} {mail_domain_dn}.'


def test_mail_domain_create(ldap_base, random_username, udm, ouadmin_umc_client):
    domain_name = f'{random_username()}.test.com'
    position = f'cn=domain,cn=mail,{ldap_base}'
    res = ouadmin_umc_client.create_mail_domain(domain_name, position)
    assert not res['success']
    assert res['details'] == translate('Permission denied.')


@pytest.mark.parametrize('position, has_access', [
    ('{ldap_base}', False),
    ('cn=domain,cn=mail,{ldap_base}', True),
])
def test_query_and_read_mail_domain(udm, ldap_base, ou, position, has_access, ouadmin_umc_client):
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
        ouadmin_umc_client.umc_command('udm/get', get_option, 'mail/domain')  # type: ignore[call-arg]

    # create
    udm.create_object(
        'mail/domain',
        name=domain_name,
        position=position,
    )

    # query
    res = ouadmin_umc_client.umc_command('udm/query', query_options, 'mail/mail').result  # type: ignore[call-arg]
    if has_access:
        assert object_dn in [x['$dn$'] for x in res]
        assert len(res) == len(udm.list_objects('mail/domain', properties=["DN"]))
    else:
        assert object_dn not in [x['$dn$'] for x in res]

    # get (should be possible)
    if has_access:
        res = ouadmin_umc_client.umc_command('udm/get', get_option, 'mail/domain').result  # type: ignore[call-arg]
        assert res
        assert res[0]['$dn$'] == object_dn
        assert len(res) == 1
    else:
        with pytest.raises(BadRequest):
            ouadmin_umc_client.umc_command('udm/get', get_option, 'mail/domain')  # type: ignore[call-arg]

    # delete
    udm.remove_object('mail/domain', dn=object_dn)

    # query all should be empty
    res = ouadmin_umc_client.umc_command('udm/query', query_options, 'mail/mail').result  # type: ignore[call-arg]
    assert len(res) == len(udm.list_objects('mail/mail', properties=["DN"]))

    # get (should not be possible)
    with pytest.raises(BadRequest):
        ouadmin_umc_client.umc_command('udm/get', get_option, 'mail/mail')  # type: ignore[call-arg]


def test_non_readable_attributes_filtered_in_umc(ou, udm, ouadmin_umc_client):
    """
    Test that non-readable attributes (guardianRoles, guardianInheritedRoles, guardianMemberRoles)
    are filtered out in UMC search and get operations for OU administrators.
    These attributes should either be empty or not present when accessed by OU admins,
    even when they have values set.
    """
    group_dn, _ = udm.create_group(position=ou.dn, guardianMemberRoles=['foo:bar:grouprole'])
    user_dn, _ = udm.create_user(position=ou.dn, guardianRoles=['foo:bar:userrole'], groups=[group_dn])

    query_options = {
        'container': 'all',
        'hidden': False,
        'objectType': 'users/user',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': [
            'name',
            'username',
            'guardianRoles',
            'guardianInheritedRoles',
        ],
    }

    res = ouadmin_umc_client.umc_command('udm/query', query_options, 'users/user').result
    user_result = next((user for user in res if user['$dn$'] == user_dn), None)
    assert user_result is not None

    assert not user_result.get('guardianRoles', [])
    assert not user_result.get('guardianInheritedRoles', [])

    get_result = ouadmin_umc_client.umc_command('udm/get', [user_dn], 'users/user').result
    assert len(get_result) == 1
    user_obj = get_result[0]

    assert not user_obj.get('guardianRoles', [])
    assert not user_obj.get('guardianInheritedRoles', [])

    properties_result = ouadmin_umc_client.umc_command('udm/properties', [{'objectType': 'users/user'}], 'users/user').result
    assert len(properties_result) == 1
    properties = properties_result[0]

    guardian_roles_prop = next((prop for prop in properties if prop['id'] == 'guardianRoles'), None)
    guardian_inherited_prop = next((prop for prop in properties if prop['id'] == 'guardianInheritedRoles'), None)

    if guardian_roles_prop:
        assert not guardian_roles_prop.get('default', [])

    if guardian_inherited_prop:
        assert not guardian_inherited_prop.get('default', [])

    group_query_options = {
        'container': 'all',
        'hidden': False,
        'objectType': 'groups/group',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': [
            'name',
            'guardianMemberRoles',
        ],
    }

    res = ouadmin_umc_client.umc_command('udm/query', group_query_options, 'groups/group').result
    group_result = next((group for group in res if group['$dn$'] == group_dn), None)
    assert group_result is not None

    assert not group_result.get('guardianMemberRoles', []), f"guardianMemberRoles should be empty but got: {group_result.get('guardianMemberRoles')}"

    group_get_result = ouadmin_umc_client.umc_command('udm/get', [group_dn], 'groups/group').result
    assert len(group_get_result) == 1
    group_obj = group_get_result[0]

    assert not group_obj.get('guardianMemberRoles', []), f"guardianMemberRoles should be empty but got: {group_obj.get('guardianMemberRoles')}"

    group_properties_result = ouadmin_umc_client.umc_command('udm/properties', [{'objectType': 'groups/group'}], 'groups/group').result
    assert len(group_properties_result) == 1
    group_properties = group_properties_result[0]

    guardian_member_roles_prop = next((prop for prop in group_properties if prop['id'] == 'guardianMemberRoles'), None)
    if guardian_member_roles_prop:
        assert not guardian_member_roles_prop.get('default', [])

    # Clean up
    udm.remove_object('users/user', dn=user_dn)
    udm.remove_object('groups/group', dn=group_dn)
