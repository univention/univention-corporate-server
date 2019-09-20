#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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

from __future__ import absolute_import

import subprocess
import json

from ldap.dn import explode_dn

from univention.listener import ListenerModuleHandler, ListenerModuleConfiguration

name = 'portal_groups'

GROUP_CACHE = '/var/cache/univention-portal/groups.json'


class PortalGroups(ListenerModuleHandler):

	def initialize(self):
		self._save({})

	def create(self, dn, new):
		groups = self._load()
		groups[dn] = {
			'usernames': [username.lower() for username in new.get('memberUid', []) if not username.endswith('$')],
			'groups': [member.lower() for member in new.get('uniqueMember', []) if member.startswith('cn=') and not ('%s$' % explode_dn(member, True)[0]) in new.get('memberUid', [])],
		}
		self._save(groups)
		self._refresh_cache()

	def modify(self, dn, old, new, old_dn):
		groups = self._load()
		groups.pop(old_dn, None)
		groups[dn] = {
			'usernames': [username.lower() for username in new.get('memberUid', []) if not username.endswith('$')],
			'groups': [member.lower() for member in new.get('uniqueMember', []) if member.startswith('cn=') and not ('%s$' % explode_dn(member, True)[0]) in new.get('memberUid', [])],
		}
		self._save(groups)
		self._refresh_cache()

	def remove(self, dn, old):
		groups = self._load()
		groups.pop(dn, None)
		self._save(groups)
		self._refresh_cache()

	def post_run(self):
		with self.as_root():
			subprocess.call(['service', 'univention-portal-server', 'reload'])

	def _load(self):
		with self.as_root():
			with open(GROUP_CACHE) as fd:
				return json.load(fd)

	def _save(self, groups):
		with self.as_root():
			with open(GROUP_CACHE, 'wb') as fd:
				json.dump(groups, fd)

	def _refresh_cache(self):
		with self.as_root():
			with open('/var/cache/univention-portal/refresh_groups', 'w'):
				pass

	class Configuration(ListenerModuleConfiguration):
		name = name
		description = 'Maintain groups cache for Univention Portal'
		ldap_filter = '(univentionObjectType=groups/group)'
