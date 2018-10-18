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

from __future__ import absolute_import, unicode_literals
import sys
import ldap
from ldap.filter import filter_format
import univention.admin.uldap
import univention.config_registry
import univention.admin.uldap
import univention.config_registry
from .exceptions import ConnectionError


class LDAP_connection(object):
	"""Caching LDAP connection factory."""

	_ucr = None
	_connection_admin = None
	_connection_machine = None
	_connection_account = {}

	@classmethod
	def get_admin_connection(cls):
		if not cls._connection_admin:
			try:
				cls._connection_admin, po = univention.admin.uldap.getAdminConnection()
			except IOError:
				raise ConnectionError, ConnectionError('Could not read secret file'), sys.exc_info()[2]
			except ldap.INVALID_CREDENTIALS:
				raise ConnectionError, ConnectionError('Credentials invalid'), sys.exc_info()[2]
			except ldap.CONNECT_ERROR:
				raise ConnectionError, ConnectionError('Connection refused'), sys.exc_info()[2]
			except ldap.SERVER_DOWN:
				raise ConnectionError, ConnectionError('The LDAP Server is not running'), sys.exc_info()[2]
		return cls._connection_admin

	@classmethod
	def get_machine_connection(cls):
		if not cls._connection_machine:
			try:
				cls._connection_machine, po = univention.admin.uldap.getMachineConnection()
			except IOError:
				raise ConnectionError, ConnectionError('Could not read secret file'), sys.exc_info()[2]
			except ldap.INVALID_CREDENTIALS:
				raise ConnectionError, ConnectionError('Credentials invalid'), sys.exc_info()[2]
			except ldap.CONNECT_ERROR:
				raise ConnectionError, ConnectionError('Connection refused'), sys.exc_info()[2]
			except ldap.SERVER_DOWN:
				raise ConnectionError, ConnectionError('The LDAP Server is not running'), sys.exc_info()[2]
		return cls._connection_machine

	@classmethod
	def get_credentials_connection(
		cls,
		identity,
		password,
		base=None,
		server=None,
		port=None,
	):
		if not cls._ucr:
			cls._ucr = univention.config_registry.ConfigRegistry()
			cls._ucr.load()

		if '=' not in identity:
			lo = cls.get_machine_connection()
			dns = lo.searchDn(filter_format('uid=%s', (identity,)))
			try:
				identity = dns[0]
			except IndexError:
				raise ConnectionError, ConnectionError('Cannot get DN for username.'), sys.exc_info()[2]
		access_kwargs = {'binddn': identity, 'bindpw': password, 'base': base or cls._ucr['ldap/base']}
		if server:
			access_kwargs['server'] = server
		if port:
			access_kwargs['port'] = port
		key = (identity, password, server, port, base)
		if key not in cls._connection_account:
			try:
				cls._connection_account[key] = univention.admin.uldap.access(**access_kwargs)
			except ldap.INVALID_CREDENTIALS:
				raise ConnectionError, ConnectionError('Credentials invalid'), sys.exc_info()[2]
			except ldap.CONNECT_ERROR:
				raise ConnectionError, ConnectionError('Connection refused'), sys.exc_info()[2]
			except ldap.SERVER_DOWN:
				raise ConnectionError, ConnectionError('The LDAP Server is not running'), sys.exc_info()[2]
		return cls._connection_account[key]
