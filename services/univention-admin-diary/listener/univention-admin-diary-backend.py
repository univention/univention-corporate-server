# -*- coding: utf-8 -*-
#
# Univention Admin Diary
# Listener module to set up Admin Diary configuration
#
# Copyright 2018-2019 Univention GmbH
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
import subprocess

from univention.config_registry import ConfigRegistry, handler_set

name = 'univention-admin-diary-backend'
description = 'Manage admin/diary/backend variable'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']
service_name = "Admin Diary Backend"


def handler(dn, new, old):
	listener.setuid(0)
	try:
		change = False
		new_has_service = service_name in new.get('univentionService', [])
		old_has_service = service_name in old.get('univentionService', [])
		if new_has_service and not old_has_service:
			try:
				fqdn = '%s.%s' % (new['cn'][0], new['associatedDomain'][0])
			except (KeyError, IndexError):
				return

			ucr = ConfigRegistry()
			ucr.load()
			old_ucr_value = ucr.get('admin/diary/backend', '')
			fqdn_set = set(old_ucr_value.split())
			fqdn_set.add(fqdn)
			new_ucr_value = ' '.join(fqdn_set)
			handler_set(['admin/diary/backend=%s' % (new_ucr_value,)])
			change = True
		elif old_has_service:
			try:
				fqdn = '%s.%s' % (old['cn'][0], old['associatedDomain'][0])
			except (KeyError, IndexError):
				return

			ucr = ConfigRegistry()
			ucr.load()
			old_ucr_value = ucr.get('admin/diary/backend', '')
			fqdn_set = set(old_ucr_value.split())
			fqdn_set.discard(fqdn)
			new_ucr_value = ' '.join(fqdn_set)
			handler_set(['admin/diary/backend=%s' % (new_ucr_value,)])
			change = True

		if change:
			subprocess.call(['invoke-rc.d', 'rsyslog', 'try-restart'])
	finally:
		listener.unsetuid()
