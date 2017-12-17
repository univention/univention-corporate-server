# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from typing import Any, Dict
from univention.listener.handler import ListenerModuleHandler
from univention.listener.async.memcached import MemcachedLock
from univention.listener.async.async_api_adapter import AsyncListenerModuleAdapter


class AsyncListenerModuleHandler(ListenerModuleHandler):
	_adapter_class = AsyncListenerModuleAdapter
	_support_async = True
	def lock(self, key: str, timeout: int = 60, sleep_duration: float = 0.05) -> MemcachedLock:
		...
	def get_shared_var(self, var_name: str) -> Any:
		...
	def set_shared_var(self, var_name: str, var_value: Any) -> None:
		...
	def _get_ldap_credentials(self) -> Dict[str, str]:
		...
