import subprocess

import pytest

from univention.ldap_cache.cache import get_cache as lib_get_cache

from univention.lib.misc import custom_groupname
from univention.testing.strings import random_name


@pytest.fixture
def base_user(ucr, ldap_base):
	return 'cn=users,%s' % ldap_base


@pytest.fixture
def base_group(ucr, ldap_base):
	return 'cn=groups,%s' % ldap_base


@pytest.fixture
def dn_builtin_users(ldap_base):
	return 'cn=Users,cn=Builtin,%s' % ldap_base


@pytest.fixture
def dn_domain_users(ucr, base_group):
	return 'cn=%s,%s' % (custom_groupname('Domain Users', ucr), base_group,)


def create_new_user(udm, base_user):
	return udm.create_object('users/user', position=base_user, username=random_name(), lastname=random_name(), password=random_name(), wait_for=True)


def create_new_group(udm, base_group):
	return udm.create_object('groups/group', position=base_group, name=random_name(), wait_for=True)


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
	udm.modify_object('groups/group', dn=group1, users=[user1, user2, user3], wait_for=True)


@pytest.fixture
def get_cache():
	yield lib_get_cache
	lib_get_cache._cache = None


@pytest.fixture
def add_cache():
	caches = []

	def _add_cache(*cache):
		subprocess.call(['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'add-cache'] + list(cache))
		subprocess.call(['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'rebuild', cache[0]])
		subprocess.call(['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'create-listener-modules'])
		caches.append(cache)
	yield _add_cache
	for cache in caches:
		subprocess.call(['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'rm-cache'] + list(cache))
	subprocess.call(['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'create-listener-modules'])
