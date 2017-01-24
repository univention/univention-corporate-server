#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#  Connections to remote UMC Servers
#
# Copyright 2013-2017 Univention GmbH
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

import warnings

from univention.lib.umc import Client, ConnectionError, HTTPError, Forbidden
from httplib import HTTPException

from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()

warnings.warn(
	'univention.lib.umc_connection is deprecated, use univention.lib.umc instead!\n'
	'- UMCConnection(host, username, password).request("udm/query", {}, flavor)\n'
	'+ Client(hostname, username, password).umc_command("udm/query", {}, flavor).result\n'
)


class UMCConnection(object):

	def __init__(self, host, username=None, password=None, error_handler=None):
		self.client = Client(host, username, password)
		self._error_handler = error_handler
		self.build_data = self.client._Client__build_data

	@property
	def _headers(self):
		return self._client._headers

	@property
	def _host(self):
		return self.client.hostname

	def get_connection(self):
		return self._client._get_connection()

	@classmethod
	def get_machine_connection(cls, error_handler=None):
		'''Creates a connection with the credentials of the local host
		to the DC Master'''
		try:
			connection = cls(ucr.get('ldap/master'))
			connection.client.authenticate_with_machine_account()
			return connection
		except ConnectionError as exc:
			if error_handler:
				error_handler('Could not connect to UMC on %s: %s' % (ucr.get('ldap/master'), exc.reason))

	def auth(self, username, password, auth_type=None):
		'''Tries to authenticate against the host and preserves the
		cookie. Has to be done only once (but keep in mind that the
		session probably expires after 10 minutes of inactivity)'''
		try:
			self.client.umc_auth(username, password, auth_type=auth_type)
		except HTTPError as exc:
			raise HTTPException(str(exc))

	def request(self, url, data=None, flavor=None, command='command'):
		'''Sends a request and returns the data from the response. url
		as in the XML file of that UMC module.
		command may be anything that UMCP understands, especially:
		* command (default)
		* get (and url could be 'ucr' then)
		* set (and url would be '' and data could be {'locale':'de_DE'})
		* upload (url could be 'udm/license/import')
		'''
		if data is None:
			data = {}
		try:
			if command in ('command', 'upload'):
				response = self.client.umc_command(url, data, flavor)
			elif command == 'get':
				response = self.client.umc_get(url)
			elif command == 'set':
				response = self.client.umc_set(data)
		except Forbidden:
			raise NotImplementedError('command forbidden: %s' % url)
		except HTTPError as exc:
			if self._error_handler:
				self._error_handler(str(exc))
			raise HTTPException(str(exc))
		return response.result
