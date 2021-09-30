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
	def __init__(self, username, display_name, groups, headers):
		self.username = username
		self.display_name = display_name
		self.groups = [group.lower() for group in groups]
		self.headers = headers

	def is_admin(self):
		if self.is_anonymous():
			return False
		admin_groups = config.fetch("admin_groups")
		return any(self.is_member_of(group) for group in admin_groups)

	def is_anonymous(self):
		return self.username is None

	def is_member_of(self, group):
		return group.lower() in self.groups
