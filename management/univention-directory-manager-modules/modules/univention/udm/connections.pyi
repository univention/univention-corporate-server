# -*- coding: utf-8 -*-
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

from __future__ import absolute_import, unicode_literals
import univention.config_registry
from .modules.generic import OriUdmHandlerTV
from typing import Any, Callable, Dict, Optional, Text, Tuple


class LDAP_connection(object):
	_ucr = None  # type: univention.config_registry.ConfigRegistry
	_connection_admin = None  # type: OriUdmHandlerTV
	_connection_account = {}  # type: Dict[Tuple[Text, Text, Text, int, Text], OriUdmHandlerTV]

	@classmethod
	def _wrap_connection(cls, func, **kwargs):  # type: (Callable[[Any], Any], **Any) -> Any
		...

	@classmethod
	def get_admin_connection(cls):  # type: () -> OriUdmHandlerTV
		...

	@classmethod
	def get_machine_connection(cls):  # type: () -> OriUdmHandlerTV
		...

	@classmethod
	def get_credentials_connection(
		cls,
		identity,  # type: str
		password,  # type: str
		base=None,  # type: Optional[str]
		server=None,  # type: Optional[str]
		port=None,  # type: Optional[int]
	):
		# type: (...) -> OriUdmHandlerTV
		...
