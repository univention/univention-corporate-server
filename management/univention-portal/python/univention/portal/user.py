# -*- coding: utf-8 -*-
#
# Copyright 2018-2021 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.


import univention.portal.config as config


class User(object):
	def __init__(self, username, display_name, groups, headers, args=None):
		self.username = username
		self.display_name = display_name
		self.groups = [group.lower() for group in groups]
		self.headers = headers
		self.args = args or {}

	def is_admin(self):
		if self.is_anonymous():
			return False
		admin_groups = config.fetch("admin_groups")
		return any(self.is_member_of(group) for group in admin_groups)

	def is_anonymous(self):
		return self.username is None

	def is_member_of(self, group):
		return group.lower() in self.groups

	def is_authorized(self, auth_info):
		levels_of_assurance = {"low": 1, "medium": 2, "high": 3}
		disallow_anonymous = auth_info.get('disallow_anonymous', False)
		allowed_roles = set(auth_info.get('roles', []))
		allowed_idps = set(auth_info.get('idps', []))
		allowed_loa = auth_info.get('loa')
		merged_args = self.args.get('linkedAccounts', self.args)
		roles = set(merged_args.get('roles', []))
		idps = set(merged_args.get('idps', []))
		loa = merged_args.get('loa', ['low'])

		def conditions():
			yield not disallow_anonymous or not self.is_anonymous()
			if allowed_roles:
				yield allowed_roles & roles
			if allowed_idps:
				yield allowed_idps & idps
			if allowed_loa:
				yield levels_of_assurance.get(loa[0], 1) >= levels_of_assurance.get(allowed_loa[0] if allowed_loa else None, 1)
		return all(conditions())
