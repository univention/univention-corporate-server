#!/usr/share/ucs-test/runner pytest
## desc: Create a group with users and look at the LDAP cache
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-group-membership-cache


import re

import pytest
from ldap import explode_dn

from univention.testing.utils import stop_listener, start_listener, verify_ldap_object
from univention.ldap_cache.cache import get_cache


def test_cache_creation(udm, group1, group2, user1, user2):
	"""
	Create new users and groups and check if the cache is updated.
	1) create user1
	2) create user2
	3) add user1 and user2 to group
	4) check if user1 and user2 are in the changed group
	"""
	udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert data_uids[group1] == [explode_dn(user1, 1)[0]]
	assert data_members[group1] == [user1]

	udm.modify_object('groups/group', dn=group1, users=[user2], wait_for_replication=True)
	cache = get_cache()
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert len(data_uids[group1]) == 2
	assert len(data_members[group1]) == 2

	udm.modify_object('groups/group', dn=group1, remove={'users': [user1]}, wait_for_replication=True)
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert data_uids[group1] == [explode_dn(user2, 1)[0]]
	assert data_members[group1] == [user2]

	udm.modify_object('groups/group', dn=group1, remove={'users': [user2]}, wait_for_replication=True)
	data_uids = cache.get_sub_cache('memberUids').load()
	data_members = cache.get_sub_cache('uniqueMembers').load()
	assert group1 not in data_uids
	assert group1 not in data_members
