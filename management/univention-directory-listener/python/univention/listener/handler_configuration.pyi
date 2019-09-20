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
import logging
from typing import Any, Dict, List, Tuple, Type
from univention.listener.handler import ListenerModuleHandler


class ListenerModuleConfiguration(object):
	name = ''  # type: str
	description = ''  # type: str
	ldap_filter = ''  # type: str
	listener_module_class = None  # type: Type[ListenerModuleHandler]
	attributes = []  # type: List[str]
	_mandatory_attributes = ('name', 'description', 'ldap_filter', 'listener_module_class')  # type: Tuple[str, ...]

	def __init__(self, *args: Tuple[str], **kwargs: Dict[str, str]) -> None:
		self.logger = logging.Logger('')  # type: logging.Logger
	def __repr__(self) -> str:
		...
	def _run_checks(self) -> None:
		...
	def get_configuration(self) -> dict:
		...
	@classmethod
	def get_configuration_keys(cls) -> list:
		...
	def get_name(self) -> str:
		...
	def get_description(self) -> str:
		...
	def get_ldap_filter(self) -> str:
		...
	def get_attributes(self) -> list:
		...
	def get_listener_module_instance(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> ListenerModuleHandler:
		...
	def get_listener_module_class(self) -> type:
		...
	def get_active(self) -> bool:
		...
