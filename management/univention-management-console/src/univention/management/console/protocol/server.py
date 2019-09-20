#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  simple UMCP server implementation
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

"""
Defines the basic class for an UMC server.
"""

import os
import fcntl
import socket
import resource
import traceback

import notifier
import notifier.signals as signals
from OpenSSL import SSL

from univention.lib.i18n import Translation

from .message import Message, IncompleteMessageError, ParseError
from .session import SessionHandler
from .definitions import RECV_BUFFER_SIZE

from ..resources import moduleManager, categoryManager
from ..log import CORE, CRYPT, RESOURCES
from ..config import ucr, SERVER_MAX_CONNECTIONS, SERVER_CONNECTION_TIMEOUT

_ = Translation('univention.management.console').translate


class MagicBucket(object):

	'''Manages a connection (session) to the UMC server. Therefore it
	ensures that without successful authentication no other command is
	accepted. All commands are passed to the SessionHandler. After the user
	has authenticated the commands are passed on to the Processor.'''

	def __init__(self):
		self.__states = {}

	def __del__(self):
		self.exit()

	def new(self, client, socket):
		"""Is called by the Server object to announce a new incoming
		connection.

		:param str client: IP address + port
		:param fd socket: a file descriptor or socket object
		"""
		CORE.info('Established connection: %s' % client)
		state = State(client, socket)
		state.session.signal_connect('success', notifier.Callback(self._response, state))
		self.__states[socket] = state
		notifier.socket_add(socket, self._receive)
		self._timeout_connection(state)

	def _timeout_connection(self, state):
		"""Closes the connection after a specified timeout"""
		state.time_remaining -= 1

		if state.time_remaining <= 0 and not state.requests and not state.session.has_active_module_processes():
			CORE.process('Connection timed out.')
			self._cleanup(state.socket)
		else:
			# count down the timer second-wise (in order to avoid problems when
			# changing the system time, e.g. via rdate)
			notifier.timer_add(1000, lambda: self._timeout_connection(state))

	def exit(self):
		'''Closes all open connections.'''
		# remove all sockets
		for sock in self.__states.keys():
			CORE.info('Shutting down connection %s' % sock)
			self.__states.pop(sock).session.shutdown()
			notifier.socket_remove(sock)

	def _receive(self, socket):
		"""Signal callback: Handles incoming data. Processes SSL events
		and parses the incoming data. If a valid UMCP was found it is
		passed to _handle.

		:param fd socket: file descriptor or socket object that reported incoming data
		"""
		data = ''

		try:
			data = socket.recv(RECV_BUFFER_SIZE)
		except SSL.WantReadError:
			# this error can be ignored (SSL need to do something)
			return True
		except (SSL.SysCallError, SSL.Error) as exc:
			if exc.args and exc.args[0] == -1:
				CRYPT.warn('The socket was closed by the client.')
			else:
				CRYPT.error('SSL error in _receive: %s.' % (exc,))
			self._cleanup(socket)
			return False

		if not data:
			self._cleanup(socket)
			return False

		try:
			state = self.__states[socket]
		except KeyError:
			return False
		state.buffer += data

		state.reset_connection_timeout()

		try:
			while state.buffer:
				msg = Message()
				state.buffer = msg.parse(state.buffer)
				state.requests[msg.id] = msg
				state.session.execute('handle', msg)
		except (KeyboardInterrupt, SystemExit, SyntaxError):
			raise  # let the UMC-server crash/exit
		except IncompleteMessageError as exc:
			CORE.info('MagicBucket: incomplete message: %s' % (exc,))
		except ParseError as exc:
			CORE.process('Parse error: %r' % (exc,))
			if msg.id is None:
				# close the connection in case we use could not parse the header
				self._cleanup(socket)
				return False
			state.requests[msg.id] = msg
			state.session.execute('parse_error', msg, exc)

		return True

	def _do_send(self, socket):
		try:
			state = self.__states[socket]
		except KeyError:
			CORE.warn('The socket was already removed.')
			return False
		try:
			id, first = state.resend_queue.pop(0)
		except IndexError:
			CORE.error('The response queue for %r is empty.' % (state,))
			return False
		try:
			ret = socket.send(first)
			if ret < len(first):
				state.resend_queue.insert(0, (id, first[ret:]))
			else:
				if id != -1:
					del state.requests[id]
		except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
			CRYPT.info('UMCP: SSL error during re-send')
			state.resend_queue.insert(0, (id, first))
			return True
		except (SSL.SysCallError, SSL.Error) as error:
			CRYPT.warn('SSL error in _do_send: %s. Probably the socket was closed by the client.' % str(error))
			self._cleanup(socket)
			return False

		return (len(state.resend_queue) > 0)

	def _response(self, msg, state):
		''' Send UMCP response to client. If the status code is 250 the
		module process is asking for exit. This method forfills the
		request.'''
		if msg.id not in state.requests and msg.id != -1:
			CORE.info('The given response is invalid or not known (%s)' % (msg.id,))
			return

		state.reset_connection_timeout()
		try:
			data = str(msg)
			# there is no data from another request in the send queue
			if not state.resend_queue:
				ret = state.socket.send(data)
			else:
				ret = 0
			# not all data could be send; retry later
			if ret < len(data):
				if not state.resend_queue:
					notifier.socket_add(state.socket, self._do_send, notifier.IO_WRITE)
				state.resend_queue.append((msg.id, data[ret:]))
			else:
				if msg.id != -1:
					del state.requests[msg.id]
		except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
			CRYPT.info('UMCP: SSL error need to re-send chunk')
			try:
				notifier.socket_add(state.socket, self._do_send, notifier.IO_WRITE)
				state.resend_queue.append((msg.id, data[ret:]))
			except socket.error as error:
				CRYPT.error('Socket error in _response: %s. Probably the socket was closed by the client.' % str(error))
				self._cleanup(state.socket)
		except (SSL.SysCallError, SSL.Error, socket.error) as error:
			CRYPT.warn('SSL error in _response: %s. Probably the socket was closed by the client.' % str(error))
			self._cleanup(state.socket)
		except:  # close the connection to the client. we can't do anything else
			CORE.error('FATAL ERROR: %s' % (traceback.format_exc(),))
			self._cleanup(state.socket)

	def _cleanup(self, socket):
		if socket not in self.__states:
			return

		self.__states[socket].session.shutdown()

		notifier.socket_remove(socket)
		self.__states[socket].session.__del__()
		del self.__states[socket]

		try:
			socket.close()
		except:
			pass


class Server(signals.Provider):

	"""Creates an UMC server. It handles incoming connections on UNIX or
	TCP sockets and passes the control to an external session handler
	(e.g. :class:`.MagicBucket`)

	:param int port: port to listen to
	:param bool ssl: if SSL should be used
	:param str unix: if given it must be the filename of the UNIX socket to use
	:param bool magic: if an external session handler should be used
	:param class magicClass: a reference to the class for the external session handler
	:param bool load_ressources: if the modules and categories definitions should be loaded
	"""

	def __init__(self, port=6670, ssl=True, unix=None, magic=True, magicClass=MagicBucket, load_ressources=True):
		'''Initializes the socket to listen for requests'''
		signals.Provider.__init__(self)

		# loading resources
		if load_ressources:
			CORE.info('Loading resources ...')
			self.reload()

		CORE.info('Initialising server process')
		self.__port = port
		self.__unix = unix
		self.__ssl = ssl
		if self.__unix:
			CORE.info('Using a UNIX socket')
			self.__realsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		else:
			CORE.info('Using a TCP socket')
			try:
				self.__realsocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
			except:
				CORE.warn('Cannot open socket with AF_INET6 (Python reports socket.has_ipv6 is %s), trying AF_INET' % socket.has_ipv6)
				self.__realsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.__realsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.__realsocket.setblocking(0)
		fcntl.fcntl(self.__realsocket.fileno(), fcntl.F_SETFD, 1)

		if self.__ssl and not self.__unix:
			CORE.info('Setting up SSL configuration')
			self.crypto_context = SSL.Context(SSL.TLSv1_METHOD)
			self.crypto_context.set_cipher_list(ucr.get('umc/server/ssl/ciphers', 'DEFAULT'))
			self.crypto_context.set_options(SSL.OP_NO_SSLv2)
			self.crypto_context.set_options(SSL.OP_NO_SSLv3)
			self.crypto_context.set_verify(SSL.VERIFY_PEER, self.__verify_cert_cb)
			dir = '/etc/univention/ssl/%s.%s' % (ucr['hostname'], ucr['domainname'])
			try:
				self.crypto_context.use_privatekey_file(os.path.join(dir, 'private.key'))
				self.crypto_context.use_certificate_file(os.path.join(dir, 'cert.pem'))
				self.crypto_context.load_verify_locations(os.path.join(dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem'))
			except SSL.Error as exc:
				# SSL is not possible
				CRYPT.error('Setting up SSL configuration failed: %s' % (exc,))
				CRYPT.warn('Communication will not be encrypted!')
				self.__ssl = False
				self.crypto_context = None
				self.__realsocket.bind(('', self.__port))
				CRYPT.info('Server listening to unencrypted connections')
				self.__realsocket.listen(SERVER_MAX_CONNECTIONS)

			if self.crypto_context:
				self.connection = SSL.Connection(self.crypto_context, self.__realsocket)
				self.connection.setblocking(0)
				self.connection.bind(('', self.__port))
				self.connection.set_accept_state()
				CRYPT.info('Server listening to SSL connections')
				self.connection.listen(SERVER_MAX_CONNECTIONS)
		else:
			self.crypto_context = None
			if self.__unix:
				try:
					# ensure that the UNIX socket is only accessible by root
					old_umask = os.umask(0o077)
					self.__realsocket.bind(self.__unix)
					# restore old umask
					os.umask(old_umask)
				except EnvironmentError:
					os.unlink(self.__unix)
			else:
				self.__realsocket.bind(('', self.__port))
			CRYPT.info('Server listening to connections')
			self.__realsocket.listen(SERVER_MAX_CONNECTIONS)

		self.__magic = magic
		self.__magicClass = magicClass
		self.__bucket = None
		if self.__magic:
			self.__bucket = self.__magicClass()
		else:
			self.signal_new('session_new')

		if self.__ssl and not self.__unix:
			notifier.socket_add(self.connection, self._connection)
		else:
			notifier.socket_add(self.__realsocket, self._connection)

	def __del__(self):
		if self.__bucket:
			del self.__bucket
			self.__bucket = None

	def __verify_cert_cb(self, conn, cert, errnum, depth, ok):
		CORE.info('__verify_cert_cb: Got certificate: %s' % cert.get_subject())
		CORE.info('__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer())
		CORE.info('__verify_cert_cb: errnum=%d depth=%d ok=%d' % (errnum, depth, ok))
		return ok

	def _connection(self, socket):
		'''Signal callback: Invoked on incoming connections.'''
		try:
			socket, addr = socket.accept()
		except EnvironmentError as exc:
			CORE.error('Cannot accept new connection: %s' % (exc,))
			soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
			resource.setrlimit(resource.RLIMIT_NOFILE, (soft + 2, hard + 2))
			try:
				socket, addr = socket.accept()
				socket.close()
			except EnvironmentError:
				pass
			finally:
				resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
			return True
		socket.setblocking(0)
		if addr:
			client = '%s:%d' % (addr[0], addr[1])
		else:
			client = ''
		CORE.info('Incoming connection from %s' % client)
		if self.__magic:
			self.__bucket.new(client, socket)
		else:
			self.signal_emit('session_new', client, socket)
		return True

	def exit(self):
		'''Shuts down all open connections.'''
		CORE.warn('Shutting down all open connections')
		if self.__ssl and not self.__unix:
			notifier.socket_remove(self.connection)
			self.connection.close()
		else:
			notifier.socket_remove(self.__realsocket)
			self.__realsocket.close()
		if self.__unix:
			os.unlink(self.__unix)

		if self.__magic:
			self.__bucket.exit()

	@staticmethod
	def reload():
		"""Reloads resources like module and category definitions"""
		CORE.info('Reloading resources: modules, categories')
		moduleManager.load()
		categoryManager.load()
		RESOURCES.info('Reloading UCR variables')
		ucr.load()


class State(object):

	"""Holds information about the state of an active session

	:param str client: IP address + port
	:param fd socket: file descriptor or socket object
	"""

	def __init__(self, client, socket):
		self.client = client
		self.socket = socket
		self.buffer = ''
		self.requests = {}
		self.resend_queue = []
		self.session = SessionHandler()
		self.reset_connection_timeout()

	def reset_connection_timeout(self):
		self.time_remaining = SERVER_CONNECTION_TIMEOUT

	def __repr__(self):
		return '<State(%s %r buffer=%d requests=%d time_remaining=%r)>' % (self.client, self.socket, len(self.buffer), len(self.requests), self.time_remaining)
