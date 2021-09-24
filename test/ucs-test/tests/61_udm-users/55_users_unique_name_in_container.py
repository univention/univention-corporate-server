#!/usr/share/ucs-test/runner /usr/bin/pytest -s -l -v
## desc: Containers and Users of the same name may not exist in the same position
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## bugs: [53102]


import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.uldap


@pytest.fixture
def username():
	return uts.random_username()


def get_position(dn):
	return univention.uldap.parentDn(dn)


def test_user_creation_fails(udm, username):
	container = udm.create_object('container/cn', name=username)
	position = get_position(container)

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_user(username=username, position=position)


def test_user_move_fails(udm, username):
	container = udm.create_object('container/cn', name=username)
	position = get_position(container)

	# also tests that creating another object with the same name is allowed
	# as long as the positions differ
	user = udm.create_user(username=username)[0]
	with pytest.raises(udm_test.UCSTestUDM_MoveUDMObjectFailed):
		udm.move_object('users/user', dn=user, position=position)


def test_user_rename_fails(udm, username):
	container = udm.create_object('container/cn', name=username)
	position = get_position(container)

	user = udm.create_user(username=username + '-user', position=position)[0]
	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('users/user', dn=user, username=username)


def test_container_creation_fails(udm, username):
	user = udm.create_user(username=username)[0]
	position = get_position(user)

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_object('container/cn', name=username, position=position)


def test_container_move_fails(udm, username):
	user = udm.create_user(username=username)[0]
	position = get_position(user)

	# also tests that creating another object with the same name is allowed
	# as long as the positions differ
	container = udm.create_object('container/cn', name=username)
	with pytest.raises(udm_test.UCSTestUDM_MoveUDMObjectFailed):
		udm.move_object('container/cn', dn=container, position=position)


@pytest.mark.parametrize('container_type', ['container/cn', 'container/ou', 'groups/group', 'computers/windows'])
def test_container_rename_fails(udm, container_type, username, ucr):
	user = udm.create_user(username=username, position=ucr['ldap/base'])[0]
	position = get_position(user)

	container = udm.create_object(container_type, name=username + '-container', position=position)
	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object(container_type, dn=container, name=username)


def test_username_matches_users_cn_can_be_created(udm, username):
	lastname = uts.random_username()
	user = udm.create_user(username=username, lastname=lastname, firstname='')[0]
	udm.verify_ldap_object(user, {'cn': [lastname]})
	position = get_position(user)
	udm.create_user(username=lastname, position=position)
