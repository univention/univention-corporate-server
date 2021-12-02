#!/usr/share/ucs-test/runner pytest-3
## desc: Create a group with users and look at the LDAP cache
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-group-membership-cache

from ldap import explode_dn

from univention.testing.strings import random_name
from univention.ldap_cache.cache import get_cache


def test_cache_user_add_remove_from_group(udm, group1, user1, user2):
	"""
	Create new users and groups and check if the cache is updated.
	"""
	udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert data_uids[group1.lower()] == [explode_dn(user1, 1)[0]]
	assert data_members[group1.lower()] == [user1]

	udm.modify_object('groups/group', dn=group1, users=[user2], wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert len(data_uids[group1.lower()]) == 2
	assert len(data_members[group1.lower()]) == 2

	udm.modify_object('groups/group', dn=group1, remove={'users': [user1]}, wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert data_uids[group1.lower()] == [explode_dn(user2, 1)[0]]
	assert data_members[group1.lower()] == [user2]

	udm.modify_object('groups/group', dn=group1, remove={'users': [user2]}, wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert group1 not in data_uids
	assert group1 not in data_members


def test_cache_group_rename(udm, group1, user1):
	cache = get_cache()
	udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=True)
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert data_uids[group1.lower()] == [explode_dn(user1, 1)[0]]
	assert data_members[group1.lower()] == [user1]
	new_group_dn = udm.modify_object('groups/group', dn=group1, name=random_name(), wait_for_replication=True)

	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert group1 not in data_uids
	assert group1 not in data_members
	assert data_uids[new_group_dn.lower()] == [explode_dn(user1, 1)[0]]
	assert data_members[new_group_dn.lower()] == [user1]


def test_cache_user_rename(udm, group1, user1):
	udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=False)
	new_user_dn = udm.modify_object('users/user', dn=user1, set={'username': '%scopy' % ("other_" + random_name())}, wait_for_replication=True)

	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	# old user not in cache
	assert all(user1 not in members for members in data_members.values())
	assert all(explode_dn(user1, 1)[0] not in members for members in data_uids.values())
	# new user in cache
	assert data_uids[group1.lower()] == [explode_dn(new_user_dn, 1)[0]]
	assert data_members[group1.lower()] == [new_user_dn]


def test_cache_group_remove(udm, group1, user1):
	udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=True)
	udm.remove_object('groups/group', dn=group1, wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert group1.lower() not in data_uids
	assert group1.lower() not in data_members
