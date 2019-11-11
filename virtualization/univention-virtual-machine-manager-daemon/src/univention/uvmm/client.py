# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  UVMM client
#
# Copyright 2010-2019 Univention GmbH
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
"""UVMM client using a unix-socket."""

from __future__ import absolute_import
from __future__ import print_function

import socket
from . import protocol
from .helpers import TranslatableException, FQDN, N_ as _
import univention.config_registry as ucr
import os.path


__all__ = [
	'ClientError',
	'UVMM_ClientSocket',
	'UVMM_ClientUnixSocket',
	'uvmm_connect',
	'uvmm_cmd',
]


class ClientError(TranslatableException):

	"""Error during communication with UVMM daemon."""


class UVMM_ClientSocket(object):

	"""UVMM client."""

	def send(self, req):
		"""Send request, wait for and return answer."""
		packet = req.pack()
		try:
			self.sock.send(packet)
			return self.receive()
		except socket.timeout:
			raise ClientError(_('Timed out while sending data.'))
		except socket.error as ex:
			raise ClientError(_("Could not send request: %(errno)d"), errno=ex.errno)

	def receive(self):
		"""Get response."""
		try:
			eos = False
			buffer = ''
			while not eos:
				data = self.sock.recv(1024)
				if data == '':
					eos = True
				else:
					buffer += data
				packet = protocol.Packet.parse(buffer)
				if packet is None:
					continue  # waiting

				(length, res) = packet
				buffer = buffer[length:]

				if not isinstance(res, protocol.Response):
					raise ClientError(_('Not a UVMM_Response.'))
				else:
					return res
		except protocol.PacketError as ex:
			(translatable_text, dict) = ex.args
			raise ClientError(translatable_text, **dict)
		except socket.timeout:
			raise ClientError(_('Timed out while receiving data.'))
		except socket.error as ex:
			raise ClientError(_('Error while waiting for answer: %(errno)d'), errno=ex.errno)
		except EOFError:
			raise ClientError(_('EOS while waiting for answer.'))

	def close(self):
		"""Close socket."""
		try:
			self.sock.close()
			self.sock = None
		except socket.timeout:
			raise ClientError(_('Timed out while closing socket.'))
		except socket.error as ex:
			raise ClientError(_('Error while closing socket: %(errno)d'), errno=ex.errno)


class UVMM_ClientUnixSocket(UVMM_ClientSocket):

	"""UVMM client Unix socket."""

	def __init__(self, socket_path, timeout=0):
		"""Open new UNIX socket to socket_path."""
		try:
			self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			if timeout > 0:
				self.sock.settimeout(timeout)
			self.sock.connect(socket_path)
		except socket.timeout:
			raise ClientError(_('Timed out while opening local socket "%(path)s".'), path=socket_path)
		except socket.error as ex:
			raise ClientError(_('Could not open socket "%(path)s": %(errno)d'), path=socket_path, errno=ex.errno)

	def __str__(self):
		return "UNIX Socket %s" % (self.sock.getpeername(),)


__ucr = ucr.ConfigRegistry()
__ucr.load()


def __auth_machine():
	"""Get machine connection."""
	username = "%s$" % __ucr['hostname']
	with open('/etc/machine.secret', 'r') as f:
		password = f.readline().rstrip()

	return (username, password)


def __debug(msg):
	"""Output debugging messages."""
	try:
		if int(__ucr['dvs/uvmm/debug']) > 0:
			import sys
			print(msg, file=sys.stderr)
	except:
		pass


def uvmm_connect():
	"""Get connection to UVMM."""
	try:
			__debug("Opening connection to local UVVMd...")
			uvmm = UVMM_ClientUnixSocket('/var/run/uvmm.socket')
	except ClientError as ex:
		raise ClientError('Can not open connection to UVMM daemon: %s' % ex)
	return uvmm


__uvmm = None


def uvmm_cmd(request):
	"""Send request to UVMM.
	cred: tupel of (username, password), defaults to machine credential."""
	global __uvmm
	if __uvmm is None:
		__uvmm = uvmm_connect()
	assert __uvmm is not None, "No connection to UVMM daemon."

	response = __uvmm.send(request)
	if response is None:
		raise ClientError("UVMM daemon did not answer.")
	if isinstance(response, protocol.Response_ERROR):
		raise ClientError(response.msg)
	return response


def uvmm_local_uri(local=False):
	"""Return libvirt-URI for local host.
	If local=True, use UNIX-socket instead of TCP-socket.
	Raises ClientError() if KVM is currently available.

	> uvmm_local_uri() #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
	'qemu://.../system'
	Traceback (most recent call last):
	ClientError: ...

	> uvmm_local_uri(local=True) #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
	'qemu:///system'
	Traceback (most recent call last):
	ClientError: ...
	"""
	if os.path.exists('/dev/kvm'):
		return local and 'qemu:///system' or 'qemu://%s/system' % FQDN
	else:
		raise ClientError('Host does not support required virtualization technology.')


if __name__ == '__main__':
	import doctest
	doctest.testmod()
