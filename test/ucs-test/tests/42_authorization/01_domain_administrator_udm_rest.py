#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/enable-delegative-administration'), reason='authz not activated')


@pytest.mark.parametrize('position', [
    ('cn=users,{ldap_base}'),
    ('cn=users,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_create(position, ou, admin_rest_client, ldap_base):
    user = admin_rest_client.create_user(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    user.delete()


@pytest.mark.parametrize('position', [
    ('cn=users,{ldap_base}'),
    ('cn=users,{ou_dn}'),
    ('{ou_dn}'),
    ('{ldap_base}'),
])
def test_delete(position, ou, ldap_base, admin_rest_client, udm):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    admin_rest_client.delete_user(dn)


def test_search(udm, admin_rest_client):
    user_list = admin_rest_client.search_user('uid=*')
    assert len(user_list) == len(udm.list_objects('users/user', properties=['DN']))


@pytest.mark.parametrize('position, target_position', [
    ('cn=users,{ou_dn}', 'cn=users,{ldap_base}'),
    ('{ldap_base}', 'cn=users,{ou_dn}'),
])
def test_move(position, target_position, admin_rest_client, udm, ou, ldap_base):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    user = admin_rest_client.move_user(dn, target_position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    user.delete()


@pytest.mark.parametrize('position, changes', [
    ('cn=users,{ou_dn}', {'guardianRoles': ['umc:udm:ouadmin&umc:udm:ou=bremen']}),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}),
    ('cn=users,{ldap_base}', {'description': 'dsfdsf'}),
])
def test_modify(position, changes, ou, ldap_base, admin_rest_client, udm):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    admin_rest_client.modify_user(dn, changes)
    user = admin_rest_client.user_module.get(dn)
    for prop, value in changes.items():
        assert user.properties[prop] == value


def test_mail_domain_create(random_string, admin_rest_client):
    mail_domain = admin_rest_client.create_mail_domain()
    mail_domain.delete()


def test_mail_domain_delete(random_string, udm, ldap_base, admin_rest_client):
    dn = udm.create_object('mail/domain', name=random_string(), position=f'cn=domain,cn=mail,{ldap_base}')
    admin_rest_client.delete_mail_domain(dn)


@pytest.mark.parametrize('position, changes', [
    ('cn=groups,{ou_dn}', {'guardianMemberRoles': ['umc:udm:ouadmin&umc:udm:ou=bremen']}),
    ('{ou_dn}', {'description': 'dsfdsf'}),
    ('cn=groups,{ldap_base}', {'description': 'dsfdsf'}),
])
def test_modify_group(position, changes, ou, ldap_base, admin_rest_client, udm, random_username):
    dn = udm.create_object(
        'groups/group',
        name=random_username(),
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    admin_rest_client.modify_group(dn, changes)
    group = admin_rest_client.group_module.get(dn)
    for prop, value in changes.items():
        assert group.properties[prop] == value
