#!/usr/bin/python3
#
# Copyright 2020-2021 Univention GmbH
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


@pytest.fixture(scope="module")
def ldap_cache():
	module = import_module("univention.ldap_cache.cache", "src/", "univention.ldap_cache.cache", use_installed=False)
	return module


def test_init_shard(ldap_cache):
	# TODO: Finish this test
	caches = ldap_cache.LmdbCaches()
	cache0 = caches.add_cache_class(ldap_cache.EntryUUID)
	cache0.add_shard(ldap_cache.UserEntryUUIDShard)
	cache0.add_shard(ldap_cache.GroupEntryUUIDShard)
	# cache1 = caches.add_full_shard(UsersInGroup)
	# cache2 = caches.add_full_shard(GroupsInGroup)
