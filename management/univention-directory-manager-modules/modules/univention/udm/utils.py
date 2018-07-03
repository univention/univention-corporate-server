# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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

from __future__ import unicode_literals
from ldap.filter import filter_format
import univention.admin.uldap
import univention.config_registry
import univention.debug

try:
	from typing import Dict, Optional, Text, Tuple
except ImportError:
	pass


class UDebug(object):
	target = univention.debug.ADMIN

	@classmethod
	def all(cls, msg):
		"""Write a debug message with level ALL (as in DEBUG)"""
		cls._log(univention.debug.ALL, msg)

	debug = all

	@classmethod
	def error(cls, msg):
		"""Write a debug message with level ERROR"""
		cls._log(univention.debug.ERROR, msg)

	@classmethod
	def info(cls, msg):
		"""Write a debug message with level INFO"""
		cls._log(univention.debug.INFO, msg)

	@classmethod
	def process(cls, msg):
		"""Write a debug message with level PROCESS"""
		cls._log(univention.debug.PROCESS, msg)

	@classmethod
	def warn(cls, msg):
		"""Write a debug message with level WARN"""
		cls._log(univention.debug.WARN, msg)

	warning = warn

	@classmethod
	def _log(cls, level, msg):
		univention.debug.debug(cls.target, level, msg)


class LDAP_connection(object):
	"""Caching LDAP connection factory."""

	_ucr = None  # type: univention.config_registry.ConfigRegistry
	_connection_admin = None  # type: univention.admin.uldap.access
	_connection_machine = None  # type: univention.admin.uldap.access
	_connection_account = {}  # type: Dict[Tuple[Text, int, Text, Text], univention.admin.uldap.access]

	@classmethod
	def get_admin_connection(cls):  # type: () -> univention.admin.uldap.access
		if not cls._connection_admin:
			cls._connection_admin, po = univention.admin.uldap.getAdminConnection()
		return cls._connection_admin

	@classmethod
	def get_machine_connection(cls):  # type: () -> univention.admin.uldap.access
		if not cls._connection_machine:
			cls._connection_machine, po = univention.admin.uldap.getMachineConnection()
		return cls._connection_machine

	@classmethod
	def get_credentials_connection(
			cls,
			password,  # type: str
			username=None,  # type: Optional[str]
			dn=None,  # type: Optional[str]
			base=None,  # type: Optional[str]
			server=None,  # type: Optional[str]
			port=None  # type: Optional[int]
		):
		# type: (...) -> univention.admin.uldap.access
		assert (username or dn) and password, 'Either username and password or dn and password are required.'

		if not cls._ucr:
			cls._ucr = univention.config_registry.ConfigRegistry()
			cls._ucr.load()

		if not dn:
			if not cls._connection_machine:
				try:
					cls._connection_machine, po = univention.admin.uldap.getMachineConnection()
				except Exception as exc:
					# TODO: catch specific permission
					# TODO: raise specific permission
					raise RuntimeError('Cannot get DN for username.')
			dns = cls._connection_machine.searchDn(filter_format('uid=%s', (username,)))
			try:
				dn = dns[0]
			except IndexError:
				# TODO: raise specific permission
				raise RuntimeError('Cannot get DN for username.')

		server = server or cls._ucr['ldap/server/name']
		base = base or cls._ucr['ldap/base']
		key = (server, port, base, dn)
		if key not in cls._connection_account:
			cls._connection_account[key] = univention.admin.uldap.access(
				host=server,
				port=port,
				base=base,
				binddn=dn,
				bindpw=password
			)
		return cls._connection_account[key]
