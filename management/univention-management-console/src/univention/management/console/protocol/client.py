# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP client implementation
#
# Copyright 2006-2019 Univention GmbH
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

"""Provides a class :class:`.Client` that implements an UMCP client"""
from __future__ import print_function

import errno
import os
import socket
import fcntl

from univention.lib.i18n import Translation

from .message import Request, Response, IncompleteMessageError, ParseError
from .definitions import RECV_BUFFER_SIZE, BAD_REQUEST_AUTH_FAILED, SUCCESS, status_description
from ..log import CORE, PROTOCOL
from ..config import ucr
from OpenSSL import SSL

import notifier
import notifier.signals as signals


class UnknownRequestError(Exception):
	pass


class NoSocketError(Exception):
	pass


class ConnectionError(Exception):
	pass


'''
General client class for connecting to a UMC server.
Provides basic functionality for session-handling, authentication and
request handling.
'''


class Client(signals.Provider, Translation):

	"""Implements an UMCP client

	:param str servername: hostname of the UMC server to connect to
	:param int port: port number of the UMC server
	:param str unix: filename of the UNIX socket to connect to
	:param bool ssl: if True the connection is encrypted
	:param bool auth: if False no authentication is required for the connection
	"""

	def __verify_cert_cb(self, conn, cert, errnum, depth, ok):
		CORE.info('__verify_cert_cb: Got certificate subject: %s' % cert.get_subject())
		CORE.info('__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer())
		CORE.info('__verify_cert_cb: errnum=%d depth=%d ok=%d' % (errnum, depth, ok))
		if depth == 0 and ok == 0:
			response = Response()
			response.status = BAD_REQUEST_AUTH_FAILED
			response.message = 'SSL verification error'
			self.signal_emit('authenticated', False, response)
		return ok

	def __init__(self, servername='localhost', port=6670, unix=None, ssl=True):
		'''Initialize a socket-connection to the server.'''
		signals.Provider.__init__(self)
		self.__authenticated = False
		self.__auth_ids = []
		self.__ssl = ssl
		self.__unix = unix
		if self.__ssl and not self.__unix:
			self.__crypto_context = SSL.Context(SSL.TLSv1_METHOD)
			self.__crypto_context.set_cipher_list(ucr.get('umc/server/ssl/ciphers', 'DEFAULT'))
			self.__crypto_context.set_options(SSL.OP_NO_SSLv2)
			self.__crypto_context.set_options(SSL.OP_NO_SSLv3)
			self.__crypto_context.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.__verify_cert_cb)
			try:
				self.__crypto_context.load_verify_locations(os.path.join('/etc/univention/ssl/ucsCA', 'CAcert.pem'))
			except SSL.Error as exc:
				# SSL is not possible
				CORE.process('Client: Setting up SSL configuration failed: %s' % (exc,))
				CORE.process('Client: Communication will not be encrypted!')
				self.__crypto_context = None
				self.__ssl = False
		self.__port = port
		self.__server = servername
		self.__resend_queue = {}

		self.__realsocket = self.__socket = None
		self._init_socket()

		self.__buffer = ''
		self.__unfinishedRequests = {}
		self.signal_new('response')
		self.signal_new('authenticated')
		self.signal_new('error')
		self.signal_new('closed')
		self.signal_connect('closed', self.__closed)

	@property
	def openRequests(self):
		"""Returns a list of open UMCP requests"""
		return self.__unfinishedRequests.keys()

	def __nonzero__(self):
		if self.__ssl and not self.__crypto_context:
			return False
		return True

	def _init_socket(self):
		if self.__unix:
			self.__realsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		else:
			self.__realsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__realsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		fcntl.fcntl(self.__realsocket.fileno(), fcntl.F_SETFD, 1)

		if self.__ssl and not self.__unix:
			self.__socket = SSL.Connection(self.__crypto_context, self.__realsocket)
		else:
			if self.__socket:
				notifier.socket_remove(self.__socket)
				self.__socket.close()
			self.__socket = None

	def disconnect(self, force=True):
		"""Shutdown the connection. If there are still open requests and
		*force* is False the connection is kept."""
		if not force and self.__unfinishedRequests:
			return False
		self.signal_emit('closed')
		return True

	def connect(self):
		"""Connects to the UMC server"""
		if not self.__realsocket and not self.__socket:
			self._init_socket()
		try:
			if self.__ssl and not self.__unix:
				self.__socket.connect((self.__server, self.__port))
				self.__socket.setblocking(0)
				try:
					self.__socket.set_connect_state()
					notifier.socket_add(self.__socket, self._recv)
					CORE.info('Client.connect: SSL connection established')
				except SSL.Error as exc:
					CORE.process('Client: Setting up SSL configuration failed: %s' % (exc,))
					self.__realsocket.shutdown(socket.SHUT_RDWR)
					self.__realsocket.close()
					self.__reconnect_without_ssl()
					notifier.socket_add(self.__realsocket, self._recv)
			else:
				if self.__unix:
					self.__realsocket.connect(self.__unix)
				else:
					self.__realsocket.connect((self.__server, self.__port))
				self.__realsocket.setblocking(0)
				notifier.socket_add(self.__realsocket, self._recv)
		except socket.error as exc:
			# ENOENT: file not found, ECONNREFUSED: connection refused
			if exc.errno in (errno.ENOENT, errno.ECONNREFUSED):
				raise NoSocketError()
			raise

	def _resend(self, sock):
		while self.__resend_queue.get(sock):
			data = str(self.__resend_queue[sock][0])
			try:
				bytessent = sock.send(data)
				if bytessent < len(data):
					# only sent part of message
					self.__resend_queue[sock][0] = data[bytessent:]
					return True
				else:
					del self.__resend_queue[sock][0]
			except socket.error as exc:
				if exc.errno in (errno.ECONNABORTED, errno.EISCONN, errno.ENOEXEC, errno.EBADF, errno.EPIPE, errno.ECONNRESET):
					# Error may happen if module process died and server tries to send request at the same time
					# ECONNABORTED: connection reset by peer
					# EISCONN: socket not connected
					# ENOEXEC: bad file descriptor (?)
					# EBADF: bad file descriptor
					# EPIPE: broken pipe
					# ECONNRESET: Connection reset by peer
					CORE.info('Client: _resend: socket is damaged: %s' % str(exc))
					self.signal_emit('closed')
					return False
				if exc.errno in (errno.ENOTCONN, errno.EAGAIN):
					# EAGAIN: Resource temporarily unavailable
					# ENOTCONN: socket not connected
					return True
				raise
			except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
				return True
			except SSL.Error as sslexc:
				CORE.process('Client: Sending via SSL connection failed: %s' % (sslexc,))

				save = self.__resend_queue.pop(self.__socket, None)
				try:
					if self.__realsocket:
						self.__realsocket.shutdown(socket.SHUT_RDWR)
						self.__realsocket.close()
				except socket.error as exc:
					CORE.process('Client: could not shutdown socket (not yet connected): %s' % (exc,))

				try:
					self.__reconnect_without_ssl()
				except socket.error as exc:
					CORE.info('Client: reconnecting failed: %s' % (exc,))  # [Errno 111] Connection refused
					if exc.errno in (errno.ENOENT, errno.ECONNREFUSED):
						self.signal_emit('closed')
						return False
					raise

				if save is not None:
					self.__resend_queue[self.__realsocket] = save

				notifier.socket_add(self.__realsocket, self._recv)
				notifier.socket_add(self.__realsocket, self._resend, notifier.IO_WRITE)
				return False

		if sock in self.__resend_queue and not self.__resend_queue[sock]:
			del self.__resend_queue[sock]
		return False

	def __reconnect_without_ssl(self):
		CORE.process('Client: Communication will not be encrypted!')
		self.__ssl = False
		self._init_socket()
		self.__realsocket.connect((self.__server, self.__port))
		self.__realsocket.setblocking(0)
		CORE.info('Client.connect: connection established')

	def request(self, msg):
		"""Sends an UMCP request to the UMC server

		:param Request msg: the UMCP request to send
		"""
		PROTOCOL.info('Sending UMCP %s REQUEST %s' % (msg.command, msg.id))
		if self.__ssl and not self.__unix:
			sock = self.__socket
		else:
			sock = self.__realsocket

		if msg.command == 'AUTH':
			self.__auth_ids.append(msg.id)
		self.__resend_queue.setdefault(sock, []).append(str(msg))

		if self._resend(sock):
			notifier.socket_add(sock, self._resend, notifier.IO_WRITE)

		self.__unfinishedRequests[msg.id] = msg

	def invalidate_all_requests(self, status=500, message=None):
		"""Checks for open UMCP requests and invalidates these by faking
		a response with the given status code"""

		if self.__unfinishedRequests:
			CORE.warn('Invalidating all pending requests %s' % ', '.join(self.__unfinishedRequests.keys()))
		else:
			CORE.info('No pending requests found')
		for req in self.__unfinishedRequests.values():
			response = Response(req)
			response.status = status
			response.message = message
			self.signal_emit('response', response)
		self.__unfinishedRequests = {}

	def _recv(self, sock):
		try:
			recv = ''
			while True:
				recv += sock.recv(RECV_BUFFER_SIZE)
				if self.__ssl and not self.__unix:
					if not sock.pending():
						break
				else:
					break
		except socket.error as exc:
			CORE.warn('Client: _recv: error on socket: %s' % (exc,))
			recv = None
		except SSL.SysCallError:
			# lost connection or any other unfixable error
			recv = None
		except SSL.Error:
			error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
			# lost connection: UMC daemon died probably
			if error == errno.EPIPE:
				recv = None
			else:
				return True

		if not recv:
			self.signal_emit('closed')
			try:
				sock.close()
			except:
				pass
			notifier.socket_remove(sock)
			return False

		if self.__buffer:
			recv = self.__buffer + recv
			self.__buffer = ''
		try:
			while recv:
				response = Response()
				recv = response.parse(recv)
				self._handle(response)
		except IncompleteMessageError:
			self.__buffer = recv
			# waiting for the rest
		except ParseError as exc:
			CORE.warn('Client: _recv: error parsing message: %s' % (exc,))
			self.signal_emit('error', exc)

		return True

	def _handle(self, response):
		PROTOCOL.info('Received UMCP RESPONSE %s' % response.id)
		if response.command == 'AUTH' and response.id in self.__auth_ids:
			self.__authenticated = response.status == SUCCESS
			self.__unfinishedRequests.pop(response.id)
			if not self.__authenticated:
				response.message = response.message or status_description(response.status)
			self.signal_emit('authenticated', self.__authenticated, response)
		elif response.id in self.__unfinishedRequests:
			self.signal_emit('response', response)
			self.__unfinishedRequests.pop(response.id)
		else:
			CORE.warn('Client: _handle: received an unknown response: %s' % (response.id,))
			self.signal_emit('error', UnknownRequestError(500, 'Received an unknown response.'))

	def authenticate(self, msg):
		"""Authenticate against the UMC server"""
		if msg.command != 'AUTH':
			raise TypeError('Must be AUTH command!')
		self.request(msg)

	def __closed(self):
		for socket_ in (self.__realsocket, self.__socket):
			if socket_:
				notifier.socket_remove(socket_)
				try:
					socket_.close()
				except IOError:
					pass
		self.__realsocket = None
		self.__socket = None


if __name__ == '__main__':
	from getpass import getpass

	notifier.init(notifier.GENERIC)

	def auth(success, response):
		print('authentication', success, response.status, response.message)

	client = Client()
	client.signal_connect('authenticated', auth)
	client.connect()

	authRequest = Request('AUTH')
	authRequest.body['username'] = raw_input('Username: ')
	authRequest.body['password'] = getpass()
	client.authenticate(authRequest)

	notifier.loop()
