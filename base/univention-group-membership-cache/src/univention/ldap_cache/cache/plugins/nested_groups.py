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

from univention.ldap_cache.cache import LowerValuesShard


class UsersInGroup(LowerValuesShard):
	ldap_filter = '(univentionObjectType=groups/group)'
	value = 'uniqueMember'
	attributes = ['memberUid']

	def get_values(self, obj):
		values = super(UsersInGroup, self).get_values(obj)
		uids = set([uid.lower() for uid in obj[1].get('memberUid', [])])
		return [value for value in values if explode_dn(value, 1)[0] in uids]


class GroupsInGroup(UsersInGroup):
	def get_values(self, obj):
		ret = []
		values = super(UsersInGroup, self).get_values(obj)
		uids = set([uid.lower() for uid in obj[1].get('memberUid', [])])
		for value in values:
			rdn = explode_dn(value, 1)[0]
			if rdn in uids:
				continue
			if '%s$' % rdn in uids:
				continue
			ret.append(value)
		return ret
