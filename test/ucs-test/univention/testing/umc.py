#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS test connections to remote UMC Servers
#
# Copyright 2016-2017 Univention GmbH
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

import sys
import pprint
import httplib

from univention.lib.umc_connection import UMCConnection as _UMCConnection
from univention.config_registry import ConfigRegistry


class UMCConnection(_UMCConnection):

	def request(self, url, data=None, flavor=None, command='command'):
		print ''
		print '*** UMC request: "%s/%s" %s \ndata = %s' % (command, url, '(%s)' % (flavor,) if flavor else '', pprint.pformat(data))
		try:
			response = super(UMCConnection, self).request(url, data, flavor, command)
		except:
			print 'UMC request failed: %s' % (sys.exc_info()[1],)
			print ''
			raise
		print '*** UMC response: %s' % (pprint.pformat(response),)
		print ''
		return response


class UMCTestConnection(UMCConnection):

	def __init__(self, host=None, username=None, password=None, error_handler=None):
		"""
		All credentials are initialised with ucr values.
		The parameters can be used to overwrite them.
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
