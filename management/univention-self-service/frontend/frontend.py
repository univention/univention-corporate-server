# -*- coding: utf-8 -*-
#
# Univention Password Self Service frontend base class
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

import cherrypy

from httplib import HTTPException
from socket import error as SocketError
import re
import json

from univention.lib.umc_connection import UMCConnection
from univention.management.console.config import ucr

LDAP_SECRETS_FILE = "/etc/self-service-ldap.secret"


class UniventionSelfServiceFrontend(object):
	"""
	base class
	"""
	def __init__(self):
		self.log("__init__()")

	def log(self, msg, traceback=False):
		cherrypy.log("{}: {}".format(self.name, msg), traceback=traceback)

	@property
	def name(self):
		"""
		Implement me

		:return: unique name of plugin (used for logging and overview page)
		"""
		return self.__class__.__name__

	def get_umc_connection(self, username=None, password=None):
		"""
		This is UMCConnection.get_machine_connection(), but using
		LDAP_SECRETS_FILE instead of /etc/machine.secret.

		If username and password are supplied, they are used to connect.

		:return: UMCConnection
		"""
		if not username:
			username = "{}$".format(ucr.get("hostname"))
			try:
				with open(LDAP_SECRETS_FILE) as machine_file:
					password = machine_file.readline().strip()
			except (OSError, IOError) as e:
				self.log("Could not read '{}': {}".format(LDAP_SECRETS_FILE, e))
				raise

		try:
			return UMCConnection(
				ucr.get("self-service/backend-server", ucr.get("ldap/master")),
				username=username,
				password=password)
		except (HTTPException, SocketError) as e:
			self.log("Could not connect to UMC on '{}': {}".format(ucr.get("ldap/master"), e))
			raise

	def umc_request(self, connection, url, data, command="command"):
		try:
			result = connection.request(url, data, command)
		except HTTPException as he:
			self.log(he)
			try:
				status, message = UniventionSelfServiceFrontend.work_around_broken_api(he)
				cherrypy.response.status = status
				return json.dumps({"status": status, "result": message})
			except AttributeError:
				raise he
		except (ValueError, NotImplementedError) as e:
			self.log(e)
			raise
		return json.dumps({"status": 200, "result": result})

	@staticmethod
	def work_around_broken_api(httpex):
		"""
		Try to extract status and message from a HTTPException object

		:param httperror:  HTTPException object
		:return: (status, message) or AttributeError if extraction was not possible
		"""
		return re.search('\{\"status\": (.*),\ \"message\":\ \"(.*)\"\}', str(httpex)).groups()
