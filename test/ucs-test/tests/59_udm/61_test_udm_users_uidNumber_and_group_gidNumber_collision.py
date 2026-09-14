#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: |
##  Collisions between user uidNumbers and group gidNumbers
##  Check different scenarios where the user uidNumbers can collide with group
##  gidNumbers and vice versa
## bugs: [38796]
## tags: [udm]
## roles: [domaincontroller_master]
## versions:
##  4.0-3: found
##  4.1-0: fixed
## exposure: dangerous
## packages:
##   - python3-univention-directory-manager

import pytest

import univention.admin.modules as udm_modules
import univention.testing.udm as udm_test


UID_GID_UNIQUENESS = 'directory/manager/uid_gid/uniqueness'


def get_max_id(lo, ldap_base):
    users = udm_modules.lookup('users/user', None, lo, base=ldap_base, scope='sub')
    groups = udm_modules.lookup('groups/group', None, lo, base=ldap_base, scope='sub')

    highest_uid = max(int(user['uidNumber']) for user in users if user['uidNumber'])
    highest_gid = max(int(group['gidNumber']) for group in groups if group['gidNumber'])

    return max(highest_uid, highest_gid) + 2


@pytest.fixture
def uid_gid_uniqueness_enabled(ucr, request):
    if ucr[UID_GID_UNIQUENESS]:
        ucr.handler_unset([UID_GID_UNIQUENESS])
    udm = request.getfixturevalue('udm')
    udm.stop_cli_server()
    udm_modules.update()


@pytest.fixture
def uid_gid_uniqueness_disabled(ucr, request):
    ucr.handler_set([f'{UID_GID_UNIQUENESS}=no'])
    udm = request.getfixturevalue('udm')
    udm.stop_cli_server()
    udm_modules.update()


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_consecutive_user_creation_does_not_collide(uid_gid_uniqueness_enabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_group(gidNumber=id_to_collide_with)

    udm.create_user(uidNumber=id_to_collide_with - 1)
    testcase_user_dn = udm.create_user()[0]

    uid_number = int(lo.getAttr(testcase_user_dn, 'uidNumber')[0])
    assert uid_number != id_to_collide_with


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_consecutive_group_creation_does_not_collide(uid_gid_uniqueness_enabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_user(uidNumber=id_to_collide_with)

    udm.create_group(gidNumber=id_to_collide_with - 1)
    testcase_group_dn = udm.create_group()[0]

    gid_number = int(lo.getAttr(testcase_group_dn, 'gidNumber')[0])
    assert gid_number != id_to_collide_with


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_explicit_user_creation_collision_is_rejected(uid_gid_uniqueness_enabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_group(gidNumber=id_to_collide_with)

    with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
        udm.create_user(uidNumber=id_to_collide_with)


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_explicit_group_creation_collision_is_rejected(uid_gid_uniqueness_enabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_user(uidNumber=id_to_collide_with)

    with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
        udm.create_group(gidNumber=id_to_collide_with)


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_explicit_user_creation_collision_allowed_without_uniqueness(uid_gid_uniqueness_disabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_group(gidNumber=id_to_collide_with)

    testcase_user_dn = udm.create_user(uidNumber=id_to_collide_with)[0]
    uid_number = int(lo.getAttr(testcase_user_dn, 'uidNumber')[0])
    assert uid_number == id_to_collide_with


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_explicit_group_creation_collision_allowed_without_uniqueness(uid_gid_uniqueness_disabled, udm, lo, ldap_base):
    id_to_collide_with = get_max_id(lo, ldap_base)
    udm.create_user(uidNumber=id_to_collide_with)

    testcase_group_dn = udm.create_group(gidNumber=id_to_collide_with)[0]
    gid_number = int(lo.getAttr(testcase_group_dn, 'gidNumber')[0])
    assert gid_number == id_to_collide_with
