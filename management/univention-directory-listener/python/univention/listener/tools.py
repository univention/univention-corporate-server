# -*- coding: utf-8 -*-

# Copyright 2021 Univention GmbH
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

import socket
from typing import Optional

from univention.config_registry import ConfigRegistry


class NotifierCommunicationError(Exception):
	pass


class NotifierConnectionError(NotifierCommunicationError):
	def __init__(self, errno, *args):
		super(NotifierConnectionError, self).__init__(*args)
		self.errno = errno


class NotifierValueError(NotifierCommunicationError):
	pass


def get_notifier_id(host=None, cmd=None):  # type: (Optional[str], Optional[bytes]) -> int
	"""
	Retrieve current Univention Directory Notifier transaction ID.

	:param str host: FQDN / IP of host with notifier (defaults to primary directory node)
	:param bytes cmd: command to send to notifier (defaults to "GET_ID")
	:return: int
	:returns: transaction ID
	:raises NotifierConnectionError: if there was a problem communicating with the notifier.
	:raises NotifierValueError: if the value returned by the notifier could not be interpreted.
	"""
	if not host:
		ucr = ConfigRegistry()
		ucr.load()
		host = ucr["ldap/master"]
	cmd = cmd or b"GET_ID"

	try:
		sock = socket.create_connection((host, 6669), 60.0)
	except socket.error as exc:
		raise NotifierConnectionError(exc.errno, "Error connecting to notifier on host {!r}: {!s}".format(host, exc))

	try:
		sock.send(b"Version: 3\nCapabilities: \n\n")
		sock.recv(100)
		sock.send(b"MSGID: 1\n%s\n\n" % (cmd,))
		notifier_result = sock.recv(100)
	except socket.error as exc:
		raise NotifierConnectionError(exc.errno, "Error communicating with notifier on host {!r}: {!s}".format(host, exc))

	if notifier_result:
		try:
			return int(notifier_result.decode("UTF-8", "replace").splitlines()[1])
		except (IndexError, ValueError) as exc:
			raise NotifierValueError(
				"Received unknown value from notifier on host {!r} after sending command {!r}: {!r}. "
				"Error: {!s}".format(host, cmd, notifier_result, exc)
			)
	else:
		raise NotifierValueError(
			"Did not receive a response from notifier on host {!r} after sending command {!r}. ".format(host, cmd)
		)
