# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
#
# Copyright 2017-2019 Univention GmbH
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

from __future__ import absolute_import
from typing import Any, Dict, List, Tuple
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.handler import ListenerModuleHandler


class ListenerModuleAdapter(object):
	def __init__(self, module_configuration: ListenerModuleConfiguration, *args: Tuple, **kwargs: Dict) -> None:
		self.config = module_configuration  # type: ListenerModuleConfiguration
		self._ldap_cred = dict()  # type: Dict[str, str]
		self._module_handler_obj = ListenerModuleHandler()  # type: ListenerModuleHandler
		self._saved_old = dict()  # type: Dict[str, List[str]]
		self._saved_old_dn = ''  # type: str
		self._rename = False  # type: bool
		self._renamed = False  # type: bool
	def _run_checks(self) -> None:
		...
	def get_globals(self) -> Dict[str, Any]:
		...
	def _setdata(self, key: str, value: str) -> None:
		...
	@property
	def _module_handler(self) -> ListenerModuleHandler:
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
