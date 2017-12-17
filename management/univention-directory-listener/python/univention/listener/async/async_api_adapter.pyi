# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
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
import logging
import pylibmc
from typing import Dict, List, Union
from univention.listener import ListenerModuleAdapter
from univention.listener.async.memcached import TasksQueue
from univention.listener import ListenerModuleConfiguration


class AsyncListenerModuleAdapter(ListenerModuleAdapter):
	def __init__(self, module_configuration: ListenerModuleConfiguration, *args: str, **kwargs: str) -> None:
		self.lm_name = ''  # type: str
		self.logger = logging.Logger('')  # type: logging.Logger
		self.lm_path = ''  # type: str
		self._listener_ldap_cred = dict()  # type: Dict[str, Dict[str, str]]
		self._memcache = pylibmc.client.Client([''])  # type: pylibmc.client.Client
		self.task_queue = TasksQueue(None, '', '')  # type: TasksQueue
	def _setdata(self, key: str, value: str) -> None:
		...
	def _handler(self, dn: str, new: Dict[str, List[str]], old: Dict[str, List[str]], command: str) -> None:
		...
	def _lazy_initialize(self) -> None:
		...
	def _lazy_clean(self) -> None:
		...
	def _lazy_pre_run(self) -> None:
		...
	def _lazy_post_run(self) -> None:
		...
	def _create_listener_job(
			self,
			task_type: str,
			lm_func: str,
			entry_uuid: Union[str, None],
			prepend: bool = False,
			**kwargs: str
	) -> str:
		...
