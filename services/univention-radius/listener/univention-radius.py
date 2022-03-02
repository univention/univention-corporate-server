#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention RADIUS
#  Listener integration
#
# Copyright 2019-2022 Univention GmbH
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

from __future__ import absolute_import

import subprocess
from typing import Dict, List, Optional  # noqa F401

from univention.listener.handler import ListenerModuleHandler


# Bug #48886: udl-ctrl parses this name with sed
name = 'univention-radius'


class AppListener(ListenerModuleHandler):
	run_update = False

	class Configuration(ListenerModuleHandler.Configuration):
		name = 'univention-radius'
		description = 'Listener module for univention-radius'
		ldap_filter = '(objectClass=univentionHost)'
		attributes = []  # type: List[str]

	def create(self, dn, new):
		# type: (str, Dict[str, List[bytes]]) -> None
		if b'univentionRadiusClient' in new.get('objectClass', []):
			self.run_update = True
			self.logger.info('config update triggered')

	def modify(self, dn, old, new, old_dn):
		# type: (str, Dict[str, List[bytes]], Dict[str, List[bytes]], Optional[str]) -> None
		# only update the file, if relevant
		if old_dn:
			self.run_update = True
			self.logger.info('config update triggered (move)')
		elif b'univentionRadiusClient' in old.get('objectClass', []) or b'univentionRadiusClient' in new.get('objectClass', []):
			if (
				set(old.get('univentionRadiusClientSharedSecret', [])) != set(new.get('univentionRadiusClientSharedSecret', [])) or
				set(old.get('univentionRadiusClientType', [])) != set(new.get('univentionRadiusClientType', [])) or
				set(old.get('univentionRadiusClientVirtualServer', [])) != set(new.get('univentionRadiusClientVirtualServer', [])) or
				set(old.get('aRecord', [])) != set(new.get('aRecord', [])) or
				set(old.get('aAAARecord', [])) != set(new.get('aAAARecord', []))
			):
				self.run_update = True
				self.logger.info('config update triggered')

	def remove(self, dn, old):
		# type: (str, Dict[str, List[bytes]]) -> None
		if b'univentionRadiusClient' in old.get('objectClass', []):
			self.run_update = True
			self.logger.info('config update triggered')

	def post_run(self):
		# type: () -> None
		if self.run_update:
			self.run_update = False
			with self.as_root():
				self.logger.info('Updating clients.univention.conf')
				subprocess.call(['/usr/sbin/univention-radius-update-clients-conf'])
				self.logger.info('Restarting freeradius')
				subprocess.call(['systemctl', 'try-restart', 'freeradius'])
