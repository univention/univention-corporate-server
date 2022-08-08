#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#
import sys

import pytest
from univentionunittests import import_module


@pytest.fixture
def db_module(mocker):
	sys.modules['gdbm'] = mocker.Mock()
	return sys.modules['gdbm']


@pytest.fixture
def backend(db_module):
	module = import_module("univention.ldap_cache.cache.backend", "src/", "univention.ldap_cache.cache.backend", use_installed=False)
	return module


@pytest.fixture
def mocked_getMachineConnection(mocker):
	mocked_getMachineConnection = mocker.patch('univention.ldap_cache.cache.backend.getMachineConnection')
	return mocked_getMachineConnection


@pytest.fixture()
def caches(backend):
	caches = backend.Caches()
	return caches


@pytest.fixture
def cache(mocker):
	cache = mocker.Mock()
	cache.ldap_filter = "ldap_filter"
	cache.value = "the_value"
	cache.db_name = "db_name"
	return cache


def test__init__(backend, caches):
	"""
	Test __init__ method.
	"""
	assert caches._directory == backend.DB_DIRECTORY
	assert caches._caches == {}


def test_get_shards_for_query(caches, cache, mocker):
	"""
	test get_shards_for_query method.
	"""
	# get unexisting query
	result = caches.get_shards_for_query("a")
	assert result == []

	# get existing query but No
	shard = mocker.Mock()
	shard.ldap_filter = "ldap_filter for query"
	shard.db_name = "db_name for query"
	cache.shards = [shard]
	with pytest.raises(NotImplementedError):
		caches.add(cache)

	caches._caches[cache.db_name] = cache
	result = caches.get_shards_for_query("ldap_filter for query")
	assert result == [shard]


def test_get_queries(caches, cache, mocker):
	"""
	Test if the queries are returned correctly.
	"""
	result = caches.get_queries("a")
	assert result == {}

	shard = mocker.Mock()
	shard.ldap_filter = "ldap_filter for query"
	shard.db_name = "db_name for query"
	shard.key = "shard_key"
	shard.value = "shard_value"
	shard.attributes = {"attr1": "value1", "attr2": "value2"}
	cache.shards = [shard]
	caches._caches[cache.db_name] = cache

	attributes = set([shard.key, shard.value])
	attributes.update(shard.attributes)
	# test cache_names None
	result = caches.get_queries()
	assert result == {shard.ldap_filter: ([shard], attributes)}

	# test cache_names not None and existing
	result = caches.get_queries([cache.db_name])
	assert result == {shard.ldap_filter: ([shard], attributes)}

	# test cache_names not None and not existing
	result = caches.get_queries(["non_existing_name"])
	assert result == {}


def test_rebuild(caches, mocker):
	"""
	Test if the rebuild method is called correctly.
	"""
	# Create a couple of mocked cache
	cache1 = mocker.Mock()
	cache1.db_name = "db_name1"
	cache1.ldap_filter = "ldap_filter1"
	cache1.value = "value1"
	cache2 = mocker.Mock()
	cache2.db_name = "db_name2"
	cache2.ldap_filter = "ldap_filter2"
	cache2.value = "value2"
	# Add them to the caches
	caches._caches[cache1.db_name] = cache1
	caches._caches[cache2.db_name] = cache2
	# Rebuild the caches
	caches.rebuild()
	# Check if the caches were rebuild
	assert cache1.clear.call_count == 1
	assert cache2.clear.call_count == 1
	assert caches.get_queries()


# TODO: need some more tests here


def test__query_objects(caches, mocked_getMachineConnection):
	"""
	Test _query_objects method.
	"""
	mocked_getMachineConnection.search.retun_value = "returned value"
	caches._query_objects("query", "attrs")
	assert mocked_getMachineConnection.search.call_count == 1
	mocked_getMachineConnection.search.assert_called_with("query", "attrs")


def test_get_sub_cache(caches, cache):
	"""
	Test if _get_sub_cache returns the correct cache.
	"""
	result = caches.get_sub_cache("a")
	assert result is None
	caches.add(cache)
	result = caches.get_sub_cache(cache.db_name)
	assert result == cache


def test_add(caches, cache, mocker):
	"""
	Test add method.
	"""

	caches.add(cache)

	assert cache.add_shard.call_count == 1
