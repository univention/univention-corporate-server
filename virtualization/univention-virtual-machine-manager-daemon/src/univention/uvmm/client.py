# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  UVMM client
#
# Copyright 2010-2015 Univention GmbH
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
"""UVMM client using a unix-socket."""

import socket
import protocol
from helpers import TranslatableException, FQDN, N_ as _
from OpenSSL import SSL
import PAM
import univention.config_registry as ucr

__all__ = [
		'ClientError',
		'UVMM_ClientSocket',
		'UVMM_ClientUnixSocket',
		'UVMM_ClientAuthenticatedSocket',
		'UVMM_ClientTCPSocket',
		'UVMM_ClientSSLSocket',
		'UVMM_ClientAuthSSLSocket',
		'uvmm_connect',
		'uvmm_cmd',
		]

class ClientError(TranslatableException):
	"""Error during communication with UVMM daemon."""
	pass

class UVMM_ClientSocket(object):
	"""UVMM client."""

	def send(self, req):
		"""Send request, wait for and return answer."""
		packet = req.pack()
		try:
			self.sock.send(packet)
			return self.receive()
		except socket.timeout, msg:
			raise ClientError(_('Timed out while sending data.'))
		except socket.error, (errno, msg):
			raise ClientError(_("Could not send request: %(errno)d"), errno=errno)

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
					continue # waiting

				(length, res) = packet
				buffer = buffer[length:]

				if not isinstance(res, protocol.Response):
					raise ClientError(_('Not a UVMM_Response.'))
				else:
					return res
		except protocol.PacketError, (translatable_text, dict):
			raise ClientError(translatable_text, **dict)
		except socket.timeout, msg:
			raise ClientError(_('Timed out while receiving data.'))
		except socket.error, (errno, msg):
			raise ClientError(_('Error while waiting for answer: %(errno)d'), errno=errno)
		except EOFError:
			raise ClientError(_('EOS while waiting for answer.'))

	def close(self):
		"""Close socket."""
		try:
			self.sock.close()
			self.sock = None
		except socket.timeout, msg:
			raise ClientError(_('Timed out while closing socket.'))
		except socket.error, (errno, msg):
			raise ClientError(_('Error while closing socket: %(errno)d'), errno=errno)

class UVMM_ClientUnixSocket(UVMM_ClientSocket):
	"""UVMM client Unix socket."""

	def __init__(self, socket_path, timeout=0):
		"""Open new UNIX socket to socket_path."""
		try:
			self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			if timeout > 0:
				self.sock.settimeout(timeout)
			self.sock.connect(socket_path)
		except socket.timeout, msg:
			raise ClientError(_('Timed out while opening local socket "%(path)s".'), path=socket_path)
		except socket.error, (errno, msg):
			raise ClientError(_('Could not open socket "%(path)s": %(errno)d'), path=socket_path, errno=errno)

	def __str__(self):
		return "UNIX Socket %s" % (self.sock.getpeername(),)

class UVMM_ClientAuthenticatedSocket(UVMM_ClientSocket):
	"""Mixin-class to handle client connection requiring authentication.

	class Auth(UVMM_ClientSSLSocket, UVMM_ClientAuthenticatedSocket): pass
	c = Auth('xen1.opendvdi.local', 2106)
	c.set_auth_data('Administrator', 'univention')
	res = c.send(...)
	"""

	def set_auth_data(self, username, password):
		"""Register username and password for authentication."""
		self.username = username
		self.password = password

	def send(self, req):
		"""Send request, wait for and return answer."""
		response = super(UVMM_ClientAuthenticatedSocket, self).send(req)
		while isinstance(response, protocol.Response_AUTHENTICATION):
			resp = []
			for query, type in response.challenge:
				if type == PAM.PAM_PROMPT_ECHO_ON:
					resp.append((self.username, PAM.PAM_SUCCESS))
				elif type == PAM.PAM_PROMPT_ECHO_OFF:
					resp.append((self.password, PAM.PAM_SUCCESS))
				elif type == PAM.PAM_PROMPT_ERROR_MSG:
					raise ClientError(_("PAM error: %(msg)s"), msg=query)
				elif type == PAM.PAM_PROMPT_TEXT_INFO:
					raise ClientError(_("PAM info: %(msg)s"), msg=query)
				else:
					raise ClientError(_("Unknown PAM type: %(type)s"), type=type)
			request = protocol.Request_AUTHENTICATION(response=resp)
			response = super(UVMM_ClientAuthenticatedSocket, self).send(request)
			if isinstance(response, protocol.Response_OK):
				# repeat original request
				return self.send(req)
		return response

class UVMM_ClientTCPSocket(UVMM_ClientSocket):
	"""UVMM client TCP socket to (str(host), int(port))."""
	def __init__(self, host, port=2105, timeout=0):
		"""Open new TCP socket to host:port."""
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if timeout > 0:
				self.sock.settimeout(timeout)
			self.sock.connect((host, port))
		except socket.timeout, msg:
			raise ClientError(_('Timed out while connecting to "%(host)s:%(port)d".'), host=host, port=port)
		except socket.error, (errno, msg):
			raise ClientError(_('Could not connect to "%(host)s:%(port)d": %(errno)d'), host=host, port=port, errno=errno)

	def __str__(self):
		return "TCP Socket %s:%d -> %s:%d" % (self.sock.getsockname() + self.sock.getpeername())

class UVMM_ClientSSLSocket(UVMM_ClientSocket):
	"""UVMM client SSL enctrypted TCP socket to (str(host), int(port))."""
	privatekey = '/etc/univention/ssl/%s/private.key' % FQDN
	certificate = '/etc/univention/ssl/%s/cert.pem' % FQDN
	cas = '/etc/univention/ssl/ucsCA/CAcert.pem'

	def __init__(self, host, port=2106, ssl_timeout=0, tcp_timeout=0):
		"""Open new SSL encrypted TCP socket to host:port."""
		try:
			ctx = SSL.Context(SSL.SSLv23_METHOD)
			ctx.set_options(SSL.OP_NO_SSLv2)
			#ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
			ctx.use_privatekey_file(UVMM_ClientSSLSocket.privatekey)
			ctx.use_certificate_file(UVMM_ClientSSLSocket.certificate)
			ctx.load_verify_locations(UVMM_ClientSSLSocket.cas)

			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if tcp_timeout > 0:
				sock.settimeout(tcp_timeout)
			self.sock = SSL.Connection(ctx, sock)
			self.sock.connect((host, port))

			if ssl_timeout > 0:
				import struct
				self.sock.setblocking(1)
				tv = struct.pack('ii', int(ssl_timeout), int(0))
				self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, tv)

		except socket.timeout, msg:
			raise ClientError(_('Timed out while connecting to "%(host)s:%(port)d".'), host=host, port=port)
		except socket.error, (errno, msg):
			raise ClientError(_('Could not connect to "%(host)s:%(port)d": %(errno)d'), host=host, port=port, errno=errno)

	def __str__(self):
		return "TCP-SSL Socket %s:%d -> %s:%d" % (self.sock.getsockname() + self.sock.getpeername())

class UVMM_ClientAuthSSLSocket(UVMM_ClientSSLSocket, UVMM_ClientAuthenticatedSocket):
	"""SSL-socket plus authentication."""
	pass

__ucr = ucr.ConfigRegistry()
__ucr.load()

def __auth_machine():
	"""Get machine connection."""
	username = "%s$" % __ucr['hostname']
	f = open('/etc/machine.secret', 'r')
	try:
		password = f.readline().rstrip()
	finally:
		f.close()
	return (username, password)

def __debug(msg):
	"""Output debugging messages."""
	try:
		if int(__ucr['dvs/uvmm/debug']) > 0:
			import sys
			print >>sys.stderr, msg
	except:
		pass

def uvmm_connect(managers=None, cred=None):
	"""Get connection to UVMM.
	managers: space separated list of hosts or iteratable.
	cred: tupel of (username, password), defaults to machine credential."""
	if managers is None:
		managers = __ucr.get('uvmm/managers', '')
	if isinstance(managers, basestring):
		managers = managers.split(' ')
	try:
		for uvmmd in managers:
			try:
				__debug("Opening connection to UVMMd %s ..." % uvmmd)
				uvmm = UVMM_ClientAuthSSLSocket(uvmmd)
				if not cred:
					cred = __auth_machine()
				uvmm.set_auth_data(*cred)
				break
			except Exception, e:
				__debug("Failed: %s" % e)
				pass
		else:
			__debug("Opening connection to local UVVMd...")
			uvmm = UVMM_ClientUnixSocket('/var/run/uvmm.socket')
	except ClientError, e:
		raise ClientError('Can not open connection to UVMM daemon: %s' % e)
	return uvmm

__uvmm = None
def uvmm_cmd(request, managers=None, cred=None):
	"""Send request to UVMM.
	cred: tupel of (username, password), defaults to machine credential."""
	global __uvmm
	if __uvmm is None:
		__uvmm = uvmm_connect(managers=managers, cred=cred)
	assert __uvmm is not None, "No connection to UVMM daemon."

	response = __uvmm.send(request)
	if response is None:
		raise ClientError("UVMM daemon did not answer.")
	if isinstance(response, protocol.Response_ERROR):
		raise ClientError(response.msg)
	return response

import os.path
def uvmm_local_uri(local=False):
	"""Return libvirt-URI for local host.
	If local=True, use UNIX-socket instead of TCP-socket.
	Raises ClientError() if neither KVM nor XEN is currently available.

	> uvmm_local_uri() #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
	'qemu://.../system'
	'xen://.../'
	Traceback (most recent call last):
	ClientError: ...

	> uvmm_local_uri(local=True) #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
	'qemu:///system'
	'xen+unix:///'
	Traceback (most recent call last):
	ClientError: ...
	"""
	if os.path.exists('/dev/kvm'):
		return local and 'qemu:///system' or 'qemu://%s/system' % FQDN
	elif os.path.exists('/proc/xen/privcmd'):
		return local and 'xen+unix:///' or 'xen://%s/' % FQDN
	else:
		raise ClientError('Host does not support required virtualization technology.')

if __name__ == '__main__':
	import doctest
	doctest.testmod()
