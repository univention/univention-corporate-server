#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.admin.rest.client import BadRequest, Forbidden, NotFound
from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/enable-delegative-administration'), reason='authz not activated')


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
        with pytest.raises(NotFound):
            ouadmin_rest_client.delete_user(dn)


def test_search(udm, ouadmin_rest_client, ou):
    user_list = ouadmin_rest_client.search_user('uid=*')
    assert len(user_list) > 0
    assert len(user_list) < len(udm.list_objects('users/user', properties=['DN']))
    assert len(user_list) == len(udm.list_objects('users/user', properties=['DN'], position=ou.dn))


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
            with pytest.raises(BadRequest):
                ouadmin_rest_client.move_user(dn, target_position)
        else:
            with pytest.raises(NotFound):
                ouadmin_rest_client.move_user(dn, target_position)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=users,{ou_dn}', {'guardianRoles': ['umc:udm:ouadmin&umc:udm:ou=bremen']}, False),
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
            with pytest.raises(NotFound):
                ouadmin_rest_client.modify_user(dn, changes)


def test_mail_domain_create(random_string, ouadmin_rest_client):
    with pytest.raises(Forbidden):
        ouadmin_rest_client.create_mail_domain()


def test_mail_domain_delete(random_string, udm, ldap_base, ouadmin_rest_client):
    dn = udm.create_object('mail/domain', name=random_string(), position=f'cn=domain,cn=mail,{ldap_base}')
    with pytest.raises(NotFound):
        ouadmin_rest_client.delete_mail_domain(dn)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=groups,{ou_dn}', {'guardianMemberRoles': ['umc:udm:ouadmin&umc:udm:ou=bremen']}, False),
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
            with pytest.raises(NotFound):
                ouadmin_rest_client.modify_group(dn, changes)
