#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS test connections to remote UMC Servers
#
# Copyright 2016-2019 Univention GmbH
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
# <https://www.gnu.org/licenses/>.

from __future__ import print_function
import sys
import pprint

from univention.lib.umc import Client as _Client
from univention.config_registry import ConfigRegistry


class Client(_Client):

	print_response = True
	print_request_data = True

	@classmethod
	def get_test_connection(cls, hostname=None, *args, **kwargs):
		ucr = ConfigRegistry()
		ucr.load()
		username = ucr.get('tests/domainadmin/account')
		username = username.split(',')[0][len('uid='):]
		password = ucr.get('tests/domainadmin/pwd')
		return cls(hostname, username, password, *args, **kwargs)

	def umc_command(self, *args, **kwargs):
		self.print_request_data = kwargs.pop('print_request_data', True)
		self.print_response = kwargs.pop('print_response', True)
		try:
			return super(Client, self).umc_command(*args, **kwargs)
		finally:
			self.print_request_data = True
			self.print_response = True

	def request(self, method, path, data=None, headers=None):
		print('')
		print('*** UMC request: "%s %s" %s' % (method, path, '(%s)' % (data.get('flavor'),) if isinstance(data, dict) else ''))
		if self.print_request_data:
			print('UMC request payload: \n%s' % (pprint.pformat(data), ))
		try:
			response = super(Client, self).request(method, path, data, headers)
		except:
			print('UMC request failed: %s' % (sys.exc_info()[1],))
			print('')
			raise
		if self.print_response:
			print('*** UMC response: \n%s\n***' % (pprint.pformat(response.data),))
		else:
			print('*** UMC response received')
		print('')
		return response
