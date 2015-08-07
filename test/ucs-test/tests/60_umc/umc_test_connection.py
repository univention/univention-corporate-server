#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#  Connections to remote UMC Servers
#
# Copyright 2015 Univention GmbH
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
# <http://www.gnu.org/licenses/>.


# stdlib
import httplib


# univention
from univention.lib.umc_connection import UMCConnection
from univention.config_registry import ConfigRegistry


class UMCTestConnection(UMCConnection):
	def __init__(self, host=None, username=None, password=None, error_handler=None):
		"""
		All credentials are initialised with ucr values.
		The the parameters can be used to overwrite them.
		The super constructor will do the authentification.
		"""
		self.ucr = ConfigRegistry()
		self.ucr.load()
		self.hostname = self.ucr.get('hostname')
		self.username = self.ucr.get('tests/domainadmin/account')
		self.username = self.username.split(',')[0][len('uid='):]
		self.password = self.ucr.get('tests/domainadmin/pwd')
		
		if host:
			self.hostname = host
		
		if username:
			self.username = username
		
		if password:
			self.password = password
		
		super(UMCTestConnection, self).__init__(self.hostname, self.username, self.password, error_handler)

	def get_custom_connection(self, url=None, data=None, flavor=None, command='command', timeout=10):
		if data is None:
			data = {}
		data = self.build_data(data, flavor)
		connection = self.get_connection()
		umcp_command = '/umcp/%s' % command
		if url:
			umcp_command = '%s/%s' % (umcp_command, url)
		connection = httplib.HTTPSConnection(self._host, timeout=timeout)
		connection.request('POST', umcp_command, data, headers=self._headers)
		return connection
