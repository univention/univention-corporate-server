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

import re
import json
import sys
from functools import wraps
from httplib import HTTPException
from socket import error as SocketError

from univention.lib.umc_connection import UMCConnection
from univention.management.console.config import ucr

sys.stdout = sys.stderr
import cherrypy

cherrypy.config.update({
	"environment": "embedded",
	"log.access_file": "/var/log/univention/self-service-access.log",
	"log.error_file": "/var/log/univention/self-service-error.log"})

LDAP_SECRETS_FILE = "/etc/self-service-ldap.secret"


class UMCConnectionError(Exception):

	def __init__(self, msg, status):
		self.msg = msg
		self.status = status

	def __str__(self):
		return "(status {}) {}".format(self.status, self.msg)


def json_response(func):

	@wraps(func)
	def _decorated(*args, **kwargs):
		data = json.dumps(func(*args, **kwargs))
		cherrypy.response.headers['Content-Type'] = 'application/json'
		return data
	return _decorated


class Ressource(object):

	@property
	def name(self):
		return self.__class__.__name__

	def __init__(self):
		self._backend = ucr.get("self-service/backend-server", ucr.get("ldap/master"))

	def get_arguments(self, *names):
		if cherrypy.request.headers.get('Content-Type', '').startswith('application/json'):
			try:
				data = json.loads(cherrypy.request.body.read())
			except ValueError:
				raise cherrypy.HTTPError(400, 'invalid application/json document')
		else:
			raise cherrypy.HTTPError(415, 'unknown content-type, supported are application/json, ')

		if not isinstance(data, dict):
			raise cherrypy.HTTPError(422, 'not a object')

		if not names:
			return data
		try:
			args = [data[key] for key in names]
		except KeyError:
			raise cherrypy.HTTPError(422, 'Missing parameters %s' % ', '.join(map(repr, names)))
		if len(names) == 1:
			return args[0]
		return args

	def log(self, msg, traceback=False):
		cherrypy.log("{}: {}".format(self.name, msg), traceback=traceback)

	def get_umc_connection(self, username=None, password=None):
		"""
		This is UMCConnection.get_machine_connection(), but using
		LDAP_SECRETS_FILE instead of /etc/machine.secret.

		If username and password are supplied, they are used to connect.

		:return: UMCConnection or UMCConnectionError
		"""
		if not username:
			username = "{}$".format(ucr.get("hostname"))
			try:
				with open(LDAP_SECRETS_FILE) as machine_file:
					password = machine_file.readline().strip()
			except (OSError, IOError) as e:
				msg = "Could not read '{}': {}".format(LDAP_SECRETS_FILE, e)
				self.log(msg)
				raise UMCConnectionError(msg, 500)

		try:
			return UMCConnection(self._backend, username=username, password=password)
		except HTTPException as error:
			self.log(error)
			exc = sys.exc_info()
			try:  # broken lib
				result = json.loads(re.search('({.*})', str(error)).group())
			except (AttributeError, ValueError):
				raise exc[0], exc[1], exc[2]
			raise UMCConnectionError(result.get('message'), result.get('status'))
		except SocketError as e:
			msg = "Could not connect to UMC server on '{}': {}".format(self._backend, e)
			self.log(msg)
			raise UMCConnectionError(msg, 500)

	def umc_request(self, url, data, command="command", connection=None, **kwargs):
		try:
			if connection is None:
				connection = self.get_umc_connection(**kwargs)
			try:
				result = connection.request(url, data, command=command)
			except HTTPException as error:
				exc = sys.exc_info()
				try:  # broken lib API
					result = json.loads(re.search('({.*})', str(error)).group())
				except (AttributeError, ValueError):
					raise exc[0], exc[1], exc[2]

			if isinstance(result, dict) and 'status' in result:  # broken lib API
				status = int(result['status'])
				message = result.get('message')
			else:
				status = 200
				message = result
		except UMCConnectionError as ue:
			status, message = ue.status, ue.message
		except HTTPException as he:
			self.log(he)
			status, message = 500, str(he)
		except (ValueError, NotImplementedError) as e:
			self.log(e)
			raise

		return {"message": message, "status": status}
