#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 Univention GmbH
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

# choose a backend
from univention.ldap_cache.cache.backend.gdbm_cache import GdbmCaches as Caches, GdbmCache as Cache, GdbmShard as Shard  # noqa: F401
# from univention.ldap_cache.cache.backend.lmdb_cache import LmdbCaches as Caches, LmdbCache as Cache, LmdbShard as Shard

from univention.ldap_cache.log import debug
from univention.ldap_cache.cache.shard_config import shards_from_config


# Singleton pattern
def get_cache():
	if get_cache._cache is None:
		debug('Creating the Caches instance')
		caches = Caches()
		for klass in shards_from_config():
			caches.add(klass)
		get_cache._cache = caches
	return get_cache._cache


get_cache._cache = None
