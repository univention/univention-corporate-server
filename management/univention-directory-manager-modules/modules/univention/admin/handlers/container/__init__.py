# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  help tools for the containers
#
# Copyright 2004-2019 Univention GmbH
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

import time


def default_container_for_objects(lo, domain):
	ttl = 2
	cache = default_container_for_objects._cache
	key = id(lo), domain
	if key not in cache or cache[key]['expire'] < time.time():
		pathResult = lo.get('cn=directory,cn=univention,' + domain)
		default_dn = 'cn=directory,cn=univention,' + domain
		if not pathResult:
			pathResult = lo.get('cn=default containers,cn=univention,' + domain)
			default_dn = 'cn=default containers,cn=univention,' + domain
		value = {'value': (pathResult, default_dn), 'expire': time.time() + ttl}
		cache[key] = value
	return cache[key]['value']


default_container_for_objects._cache = {}

__path__ = __import__('pkgutil').extend_path(__path__, __name__)
