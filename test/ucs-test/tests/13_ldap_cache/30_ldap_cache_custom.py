#!/usr/share/ucs-test/runner pytest
## desc: Create custom caches apart from group-membership
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-group-membership-cache

from univention.udm import UDM

from univention.testing.strings import random_name


def test_custom_cache(udm, get_cache, add_cache, user1, user2):
	"""
	Test a simple cache dn => lastname
	"""
	_udm = UDM.machine().version(1)
	user1 = _udm.get('users/user').get(user1)
	user2 = _udm.get('users/user').get(user2)
	add_cache('testcache', 'dn', 'sn', '(univentionObjectType=users/user)', '--single-value')
	cache = get_cache()
	testcache = cache.get_sub_cache('testcache')
	assert testcache.get(user1.dn) == user1.props.lastname
	assert testcache.get(user2.dn) == user2.props.lastname
	new_lastname = random_name()
	udm.modify_object('users/user', dn=user1.dn, lastname=new_lastname, wait_for_replication=False)
	udm.modify_object('users/user', dn=user2.dn, lastname=new_lastname, wait_for_replication=True)
	assert testcache.get(user1.dn) == new_lastname
	assert testcache.get(user2.dn) == new_lastname


def test_reverse_cache(udm, get_cache, add_cache, user1, user2):
	"""
	Test a reverse cache lastname => [dn]
	"""
	_udm = UDM.machine().version(1)
	user1 = _udm.get('users/user').get(user1)
	user2 = _udm.get('users/user').get(user2)
	add_cache('testcache', 'dn', 'sn', '(univentionObjectType=users/user)', '--reverse')
	cache = get_cache()
	testcache = cache.get_sub_cache('testcache')
	assert testcache.get(user1.props.lastname) == [user1.dn]
	assert testcache.get(user2.props.lastname) == [user2.dn]
	new_lastname = random_name()
	udm.modify_object('users/user', dn=user1.dn, lastname=new_lastname, wait_for_replication=False)
	udm.modify_object('users/user', dn=user2.dn, lastname=new_lastname, wait_for_replication=True)
	assert testcache.get(user1.props.lastname) == []
	assert testcache.get(user2.props.lastname) == []
	assert sorted(testcache.get(new_lastname)) == sorted([user1.dn, user2.dn])


def test_double_cache(udm, get_cache, add_cache, group1, user1):
	"""
	Create two configs for same cache. users' dn => [uid] and groups' dn => [cn]
	"""
	_udm = UDM.machine().version(1)
	group1 = _udm.get('groups/group').get(group1)
	user1 = _udm.get('users/user').get(user1)
	add_cache('testcache', 'dn', 'uid', '(univentionObjectType=users/user)')
	add_cache('testcache', 'dn', 'cn', '(univentionObjectType=groups/group)')
	cache = get_cache()
	testcache = cache.get_sub_cache('testcache')
	assert testcache.get(group1.dn) == [group1.props.name]
	assert testcache.get(user1.dn) == [user1.props.username]
	new_name = random_name()
	new_dn = udm.modify_object('users/user', dn=user1.dn, username=new_name, wait_for_replication=False)
	udm.remove_object('groups/group', dn=group1.dn, wait_for_replication=True)
	assert testcache.get(group1.dn) is None
	assert testcache.get(user1.dn) is None
	assert testcache.get(new_dn) == [new_name]
