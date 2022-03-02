#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention nss updater
#  Univention Listener Module
#
# Copyright 2012-2022 Univention GmbH
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

import listener
import univention.config_registry

name = 'nss'
description = 'Invalidate the nss group cache whenever a group membership has been modified.'
filter = '(objectClass=univentionGroup)'
attributes = ['uniqueMember', 'cn']


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	pass


def postrun():
	# type: () -> None
	ucr = univention.config_registry.ConfigRegistry()  # TODO: why not listener.configRegistry?
	ucr.load()

	if ucr.is_true('nss/group/cachefile', False) and ucr.is_true('nss/group/cachefile/invalidate_on_changes', True):
		listener.setuid(0)
		try:
			param = ['ldap-group-to-file.py']
			if ucr.is_true('nss/group/cachefile/check_member', False):
				param.append('--check_member')
			listener.run('/usr/lib/univention-pam/ldap-group-to-file.py', param, uid=0)
		finally:
			listener.unsetuid()
