#!/usr/share/ucs-test/runner python
## desc: Quota share cache; create and remove shares
## roles-not: [basesystem]
## exposure: careful
## packages:
##   - univention-group-membership-cache


import re
import pytest
from univention.testing.utils import wait_for_replication, stop_listener, start_listener, verify_ldap_object
from univention.ldap_cache.cache import get_cache


def test_cache_creation(udm, group1, group2, user1, user2):
	"""
	Create new users and groups and check if the cache is updated.
	1) create user1
	2) create user2
	3) add user1 and user2 to group
	4) check if user1 and user2 are in the changed group
	"""
	for cache in get_cache()._caches.values():
		cache.clear()

	udm.modify_object('groups/group', dn=group1, users=[user1, user2], wait_for_replication=False)
	wait_for_replication()
	query_result = query("UsersInGroup", group1)
	assert group1 in query_result
	assert sorted(query_result[group1]) == sorted([user1, user2])



def list_caches():
	caches = get_cache()
	for name, cache in caches._caches.items():
		if cache.single_value:
			print(name, '- stores one value per key')
		else:
			print(name, '- may store multiple values per key')
		print(' The following objects store data:')
		for shard in cache.shards:
			print('  ', shard.ldap_filter)
			print('    ', shard.key, '=>', shard.value)


def query(cache_name, pattern):
	caches = get_cache()
	cache = caches.get_sub_cache(cache_name)
	if not cache:
		print('No cache named', cache_name)
		return
	data = cache.load()
	regex = None
	if pattern:
		try:
			regex = re.compile(pattern)
		except re.error:
			print('Broken pattern')
			return
	for key in sorted(data):
		if regex is None or regex.search(key):
			print(key, '=>', data[key])
	return {key: value for key, value in data.items() if regex is None or regex.search(key)}
