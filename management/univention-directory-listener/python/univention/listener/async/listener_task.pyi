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
#

from __future__ import absolute_import
import logging
import pylibmc
from typing import Any, Dict
from celery import Task
from univention.admin.uldap import access
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.async.async_handler import AsyncListenerModuleHandler
from univention.listener.async.memcached import ListenerJob


class ListenerTask(Task):
	abstract = True
	__listener_configs = None  # type: Dict[str, ListenerModuleConfiguration]
	__listener_handlers = None  # type: Dict[str, AsyncListenerModuleHandler]
	_memcache = None  # type: pylibmc.client.Client
	_is_initialized = False  # type: bool
	_loglevel = None  # type: str
	logger = None  # type: logging.Logger

	@classmethod
	def get_lm_config_instance(cls, filename: str, name: str) -> ListenerModuleConfiguration:
		...
	@classmethod
	def get_lm_instance(cls, filename: str, name: str) -> AsyncListenerModuleHandler:
		...
	@classmethod
	def _get_shared_var(cls, name: str, var_name: str) -> Dict[str, Any]:
		...
	@classmethod
	def _set_shared_var(cls, name: str, var_name: str, var_value: Any) -> None:
		...
	@classmethod
	def _get_ldap_credentials(cls, lm_config: ListenerModuleConfiguration, name: str) -> access:
		...
	@classmethod
	def _set_loglevel(cls, name: str) -> None:
		...
	def run_listener_job(self, lj: ListenerJob, lm_instance: AsyncListenerModuleHandler) -> None:
		...
