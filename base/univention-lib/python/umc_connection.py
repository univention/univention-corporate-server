#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#  Connections to remote UMC Servers
#
# Copyright 2013 Univention GmbH
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

from httplib import HTTPSConnection, HTTPException
from simplejson import loads, dumps

class UMCConnection(object):
	def __init__(self, host, username=None, password=None, error_handler=None):
		self._host = host
		self._headers = {
			'Content-Type' : 'application/json; charset=UTF-8'
		}
		self._error_handler=error_handler
		if username is not None:
			self.auth(username, password)

	def get_connection(self):
		# once keep-alive is over, the socket closes
		#   so create a new connection on every request
		return HTTPSConnection(self._host)

	def auth(self, username, password):
		data = self.build_data({'username' : username, 'password' : password})
		con = self.get_connection()
		try:
			con.request('POST', '/umcp/auth', data)
		except Exception as e:
			# probably unreachable
			if self._error_handler:
				self._error_handler(str(e))
			error_message = '%s: Authentication failed while contacting: %s' % (self._host, e)
			raise HTTPException(error_message)
		else:
			try:
				response = con.getresponse()
				cookie = response.getheader('set-cookie')
				if cookie is None:
					raise ValueError('No cookie')
				self._headers['Cookie'] = cookie
			except Exception as e:
				if self._error_handler:
					self._error_handler(str(e))
				error_message = '%s: Authentication failed: %s' % (self._host, response.read())
				raise HTTPException(error_message)

	def build_data(self, data, flavor=None):
		data = {'options' : data}
		if flavor:
			data['flavor'] = flavor
		return dumps(data)

	def request(self, url, data=None, flavor=None):
		if data is None:
			data = {}
		data = self.build_data(data, flavor)
		con = self.get_connection()
		con.request('POST', '/umcp/command/%s' % url, data, headers=self._headers)
		response = con.getresponse()
		if response.status != 200:
			error_message = '%s on %s (%s): %s' % (response.status, self._host, url, response.read())
			if response.status == 403:
				# 403 is either command is unknown
				#   or command is known but forbidden
				if self._error_handler:
					self._error_handler(error_message)
				raise NotImplementedError
			raise HTTPException(error_message)
		content = response.read()
		return loads(content)['result']

