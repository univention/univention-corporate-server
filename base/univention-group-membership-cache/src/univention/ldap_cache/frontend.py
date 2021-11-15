#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
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


from ldap import explode_dn

from univention.ldap_cache.cache import get_cache


def groups_for_user(user_dn, consider_nested_groups=True, cache=None):
	user_dn = user_dn.lower()
	_cache = get_cache()
	if cache is None:
		cache = _cache.get_sub_cache('uniqueMembers').load()
		cache = dict((key, set(values)) for key, values in cache.items())
	search_for_dns = [user_dn]
	found = set()
	while search_for_dns:
		search_for = search_for_dns.pop().lower()
		for member, dns in cache.items():
			if search_for in dns:
				if member not in found:
					found.add(member)
					search_for_dns.append(member)
		if not consider_nested_groups:
			break
	return sorted(found)


def users_in_group(group_dn, consider_nested_groups=True, readers=(None, None)):
	group_dn = group_dn.lower()
	cache = get_cache()
	member_uid_cache, unique_member_cache = [cache.get_sub_cache(name) for name in ['memberUids', 'uniqueMembers']]
	with member_uid_cache.reading(readers[0]) as member_uid_reader, unique_member_cache.reading(readers[1]) as unique_member_reader:
		ret = []
		uids = member_uid_cache.get(group_dn, member_uid_reader) or []
		uids = set([uid.lower() for uid in uids])
		members = unique_member_cache.get(group_dn, unique_member_reader)
		if not members:
			return []
		for member in members:
			rdn = explode_dn(member, 1)[0].lower()
			if rdn in uids:
				ret.append(member)
			elif '%s$' % rdn in uids:
				continue
			else:
				if consider_nested_groups:
					ret.extend(users_in_group(member, consider_nested_groups, readers=(member_uid_reader, unique_member_reader)))
		return ret
