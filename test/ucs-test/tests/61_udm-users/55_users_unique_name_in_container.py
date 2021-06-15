#!/usr/share/ucs-test/runner /usr/bin/pytest
## desc: Containers and Users of the same name may not exist in the same position
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## bugs: [53102]


import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test


@pytest.fixture
def udm():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture
def username():
	return uts.random_username()


def get_position(dn):
	return dn.split(',', 1)[1]  # yeah, should actually be something with import ldap.dn


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


def test_container_rename_fails(udm, username):
	user = udm.create_user(username=username)[0]
	position = get_position(user)

	container = udm.create_object('container/cn', name=username + '-container', position=position)
	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('container/cn', dn=container, name=username)
