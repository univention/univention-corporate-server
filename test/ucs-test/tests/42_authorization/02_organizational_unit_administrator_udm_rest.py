#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.admin.rest.client import Forbidden, UnprocessableEntity
from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='authz not activated')


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('{ou_dn}', True),
    ('cn=users,{ldap_base}', False),
    ('{ldap_base}', False),
])
def test_create(position, expected, ouadmin_rest_client, ou, ldap_base):
    position = position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    if expected:
        user = ouadmin_rest_client.create_user(position)
        user.delete()
    else:
        with pytest.raises(Forbidden):
            ouadmin_rest_client.create_user(position)


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('{ou_dn}', True),
    ('{ldap_base}', False),
])
def test_delete(position, expected, ouadmin_rest_client, ou, ldap_base, udm):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if expected:
        ouadmin_rest_client.delete_user(dn)
    else:
        with pytest.raises(UnprocessableEntity):
            ouadmin_rest_client.delete_user(dn)


def test_search(udm, ouadmin_rest_client, ou, sub_container_with_user):
    # cn users, ou position
    user_list = ouadmin_rest_client.search_user('uid=*', position=ou.user_default_container)
    assert len(user_list) == len(udm.list_objects('users/user', properties=['DN'], position=ou.user_default_container))
    # ou position with one extra user
    udm.create_user(position=ou.dn)
    user_list = ouadmin_rest_client.search_user('uid=*', position=ou.dn)
    assert len(user_list) > 0
    assert len(user_list) < len(udm.list_objects('users/user', properties=['DN']))
    assert len(user_list) == len(udm.list_objects('users/user', properties=['DN'], position=ou.dn))
    # ldap base
    user_list = ouadmin_rest_client.search_user('uid=*')
    assert len(user_list) - 1 == len(udm.list_objects('users/user', properties=['DN'], position=ou.dn))
    # another ou
    with pytest.raises(UnprocessableEntity):
        ouadmin_rest_client.search_user('uid=*', position=ou.dn2)


@pytest.mark.parametrize('position, target_position, expected', [
    ('cn=users,{ou_dn}', 'cn=users,{ldap_base}', False),
    ('cn=users,{ldap_base}', 'cn=users,{ou_dn}', False),
    ('{ou_dn}', 'cn=users,{ou_dn}', True),
])
def test_move(position, target_position, expected, ouadmin_rest_client, udm, ou, ldap_base):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    target_position = target_position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    if expected:
        user = ouadmin_rest_client.move_user(dn, target_position)
        user.delete()
    else:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ouadmin_rest_client.move_user(dn, target_position)
        else:
            with pytest.raises(UnprocessableEntity):
                ouadmin_rest_client.move_user(dn, target_position)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=users,{ou_dn}', {'guardianRoles': ['udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen']}, False),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}, True),
    ('cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_modify(position, changes, expected, ouadmin_rest_client, udm, ou, ldap_base):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if expected:
        ouadmin_rest_client.modify_user(dn, changes)
        user = ouadmin_rest_client.user_module.get(dn)
        for prop, value in changes.items():
            assert user.properties[prop] == value
    else:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ouadmin_rest_client.modify_user(dn, changes)
        else:
            with pytest.raises(UnprocessableEntity):
                ouadmin_rest_client.modify_user(dn, changes)


def test_mail_domain_create(random_string, ouadmin_rest_client):
    with pytest.raises(Forbidden):
        ouadmin_rest_client.create_mail_domain()


def test_mail_domain_delete(random_string, udm, ldap_base, ouadmin_rest_client):
    dn = udm.create_object('mail/domain', name=random_string(), position=f'cn=domain,cn=mail,{ldap_base}')
    with pytest.raises(Forbidden):
        ouadmin_rest_client.delete_mail_domain(dn)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=groups,{ou_dn}', {'guardianMemberRoles': ['udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen']}, False),
    ('cn=groups,{ou_dn}', {'description': 'abc'}, True),
    ('{ou_dn}', {'description': 'dsfdsf'}, True),
    ('cn=groups,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_modify_group(position, changes, expected, ou, ldap_base, ouadmin_rest_client, udm, random_username):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    if expected:
        ouadmin_rest_client.modify_group(dn, changes)
        group = ouadmin_rest_client.group_module.get(dn)
        for prop, value in changes.items():
            assert group.properties[prop] == value
    else:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ouadmin_rest_client.modify_group(dn, changes)
        else:
            with pytest.raises(UnprocessableEntity):
                ouadmin_rest_client.modify_group(dn, changes)


def test_get_property_filter(ou, ouadmin_rest_client, udm):
    group_dn, _ = udm.create_group(position=ou.dn, guardianMemberRoles=['foo:bar:grouprole'])
    user_dn, _ = udm.create_user(position=ou.dn, guardianRoles=['foo:bar:userrole'], groups=[group_dn])
    user = ouadmin_rest_client.get_user(user_dn, properties=['username', 'guardianInheritedRoles', 'guardianRoles'])
    assert user.properties['guardianRoles'] == ['foo:bar:userrole']
    assert user.properties['guardianInheritedRoles'] == ['foo:bar:grouprole']


def test_readonly_attributes_readable_in_rest(ou, udm, ouadmin_rest_client):
    """OU administrators can read guardianRoles, guardianInheritedRoles and guardianMemberRoles in their OU."""
    group_dn, _ = udm.create_group(position=ou.dn, guardianMemberRoles=['foo:bar:grouprole'])
    user_dn, _ = udm.create_user(position=ou.dn, guardianRoles=['foo:bar:userrole'], groups=[group_dn])

    user = ouadmin_rest_client.get_user(user_dn, properties=['*'])

    assert user.properties['guardianRoles'] == ['foo:bar:userrole']

    user_explicit = ouadmin_rest_client.get_user(user_dn, properties=['username', 'guardianRoles', 'guardianInheritedRoles'])

    assert user_explicit.properties['guardianRoles'] == ['foo:bar:userrole']
    assert user_explicit.properties['guardianInheritedRoles'] == ['foo:bar:grouprole']

    users = ouadmin_rest_client.search_user(f'uid={user_dn.split("=")[1].split(",")[0]}', position=ou.dn)
    assert len(users) >= 1

    found_user = next((u for u in users if u.dn == user_dn), None)
    assert found_user is not None

    if hasattr(found_user, 'properties'):
        assert found_user.properties.get('guardianRoles') == ['foo:bar:userrole']

    group = ouadmin_rest_client.group_module.get(group_dn)

    assert group.properties['guardianMemberRoles'] == ['foo:bar:grouprole']
    assert user.properties.get('primaryGroup')
