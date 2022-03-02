#!/usr/bin/python3
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

import pytest
from univentionunittests import import_module

import sys


# @pytest.fixture
# def mock_lmbd(mocker):
# 	mock = mocker.patch("lmdb").return_value = mocker.Mock()
# 	return mock

@pytest.fixture
def db_module(mocker):
	sys.modules['gdbm'] = mocker.Mock()
	return sys.modules['gdbm']


@pytest.fixture
def ldap_cache():
	module = import_module("univention.ldap_cache.cache", "src/", "univention.ldap_cache.cache", use_installed=False)
	return module


@pytest.fixture
def mocked_os(mocker):
	mocked_os = mocker.patch('univention.ldap_cache.cache.os.chown')
	return mocked_os


@pytest.fixture
def lmdb_caches(ldap_cache, mocked_os):
	lmdb_caches = ldap_cache.LmdbCaches()
	return lmdb_caches


def test__init__and_permissions(db_module, lmdb_caches, mocked_os):
	"""
	Test the __init__ method of the ldap_cache.cache.LmdbCaches class.
	"""

	assert lmdb_caches._caches == {}
	db_module.open.assert_called_once_with('/usr/share/univention-group-membership-cache', 4294967295, max_dbs=128)
	assert mocked_os.call_count == 2


def test_add_cache(db_module, ldap_cache, lmdb_caches):
	"""
	Test the add_cache_class method of the ldap_cache.cache.LmdbCaches class.
	"""
	new_cache = lmdb_caches.add_cache_class(ldap_cache.EntryUUID)
	assert lmdb_caches._caches == {ldap_cache.EntryUUID.__name__: new_cache}


def test_add_full_shard(db_module, ldap_cache, lmdb_caches):
	"""
	Test the add_full_shard method of the ldap_cache.cache.LmdbCaches class.
	"""
	cache0 = lmdb_caches.add_full_shard(ldap_cache.UsersInGroup)
	assert lmdb_caches._caches == {'UsersInGroup': cache0}
	assert len(cache0.shards) == 1
	assert isinstance(cache0.shards[0], ldap_cache.UsersInGroup)
	cache1 = lmdb_caches.add_full_shard(ldap_cache.GroupsInGroup)
	assert lmdb_caches._caches == {'UsersInGroup': cache0, 'GroupsInGroup': cache1}
	assert len(cache1.shards) == 1
	assert isinstance(cache1.shards[0], ldap_cache.GroupsInGroup)


def test_recreate(ldap_cache, lmdb_caches, db_module, mocker):
	"""
	Test the recreate method of the ldap_cache.cache.LmdbCaches class.
	"""
	the_env = mocker.Mock()
	the_env.__enter__.return_value = mocker.Mock()
	context_object = mocker.Mock()
	context_object.__enter__ = mocker.Mock()
	context_object.__exit__ = None
	the_env.begin = mocker.Mock(return_value=context_object)
	db_module.open.return_value = the_env
	cache0 = lmdb_caches.add_full_shard(ldap_cache.UsersInGroup)
	cache1 = lmdb_caches.add_full_shard(ldap_cache.GroupsInGroup)
	print(cache0.env)
	print(cache1.env)
	lmdb_caches.recreate()
	# lmbd_caches = ldap_cache.LmbdCaches()

#
# def test_query_objects(ldap_cache):
# 	"""
# 	Test the query_objects method of the ldap_cache.cache.LmdbCaches class.
# 	"""
# 	lmbd_caches = ldap_cache.LmbdCaches()
#
#
#
# def test_get_cache(ldap_cache):
# 	"""
# 	Test the get_cache method of the ldap_cache.cache.LmdbCaches class.
# 	"""
# 	lmbd_caches = ldap_cache.LmbdCaches()
#
#
#
# def test_get_caches_for_query(ldap_cache):
# 	"""
# 	Test the get_caches_for_query method of the ldap_cache.cache.LmdbCaches class.
# 	"""
# 	lmbd_caches = ldap_cache.LmbdCaches()
#
