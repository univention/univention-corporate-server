import pytest

from univention.lib.misc import custom_groupname
from univention.testing.strings import random_name, random_username
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.ucr import UCSTestConfigRegistry

@pytest.fixture
def base_user(ucr):
	return 'cn=users,%s' % (ucr.get('ldap/base'),)


@pytest.fixture
def base_group(ucr):
	return 'cn=groups,%s' % (ucr.get('ldap/base'),)


@pytest.fixture
def dn_domain_users(ucr, base_group):
	return 'cn=%s,%s' % (custom_groupname('Domain Users', ucr), base_group,)

def create_new_user(udm, base_user):
	return udm.create_object('users/user', position=base_user, username=random_name(),
								 lastname=random_name(), password=random_name(), wait_for_replication=False)

def create_new_group(udm, base_group):
	return udm.create_object('groups/group', position=base_group, name=random_name(),
								 wait_for_replication=False)
@pytest.fixture
def user1(udm, base_user):
	return create_new_user(udm, base_user)

@pytest.fixture
def user2(udm, base_user):
	return create_new_user(udm, base_user)

@pytest.fixture
def user3(udm, base_user):
	return create_new_user(udm, base_user)

@pytest.fixture
def group1(udm, base_group):
	return create_new_group(udm, base_group)

@pytest.fixture
def group2(udm, base_group):
	return create_new_group(udm, base_group)

@pytest.fixture
def group3(udm, base_group):
	return create_new_group(udm, base_group)

@pytest.fixture
def group_with_users(udm, group1, user1, user2, user3):
	udm.modify_object('groups/group', dn=group1, users=[user1, user2, user3], wait_for_replication=False)


class Helpers:
	@staticmethod
	def help_me():
		return "no"

@pytest.fixture
def helpers():
	return Helpers