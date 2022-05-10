#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  simple UMCP server implementation
#
# Copyright 2006-2022 Univention GmbH
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
import errno
import fcntl
import signal
import socket
import resource
import traceback
import multiprocessing
from types import TracebackType  # noqa: F401
from typing import Dict, List, Optional, Tuple, Type  # noqa: F401

from tornado import process
import notifier
import notifier.signals as signals
from OpenSSL import SSL
from OpenSSL.crypto import X509  # noqa: F401

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
		# type: () -> None
		self.__states = {}  # type: Dict[socket.socket, State]

	def new(self, client, sock):
		# type: (str, socket.socket) -> None
		"""Is called by the Server object to announce a new incoming
		connection.

		:param str client: IP address + port
		:param socket.socket sock: a socket object
		"""
		CORE.info('Established connection: %s' % client)
		state = State(client, sock)
		state.session.signal_connect('success', notifier.Callback(self._response, state))
		self.__states[sock] = state
		notifier.socket_add(sock, self._receive)
		self.reset_connection_timeout(state)

	def reset_connection_timeout(self, state):
		# type: (State) -> None
		state.reset_connection_timeout()
		notifier.timer_remove(state._timer)
		state._timer = notifier.timer_add(state.timeout * 1000, notifier.Callback(self._timed_out, state))

	def _timed_out(self, state):
		# type: (State) -> bool
		"""Closes the connection after a specified timeout"""
		if not state.active:
			CORE.info('Session %r timed out' % (state,))
			self._cleanup(state.socket)
		else:
			CORE.info('Session %r timed out: There are open requests. Postpone session shutdown' % (state,))
			return True
		return False

	def exit(self):
		# type: () -> None
		'''Closes all open connections.'''
		# remove all sockets
		for sock in list(self.__states.keys()):
			CORE.info('Shutting down connection %s' % sock)
			self._cleanup(sock)

	def _receive(self, sock):
		# type: (socket.socket) -> bool
		"""Signal callback: Handles incoming data. Processes SSL events
		and parses the incoming data. If a valid UMCP was found it is
		passed to _handle.

		:param socket.socket sock: socket object that reported incoming data
		"""
		data = ''

		try:
			data = sock.recv(RECV_BUFFER_SIZE)
		except SSL.WantReadError:
			# this error can be ignored (SSL need to do something)
			return True
		except (SSL.SysCallError, SSL.Error) as exc:
			if exc.args and exc.args[0] == -1:
				CRYPT.warn('The socket was closed by the client.')
			else:
				CRYPT.error('SSL error in _receive: %s.' % (exc,))
			self._cleanup(sock)
			return False
		except socket.error as exc:
			CORE.warn('Socket error in _receive: %s. Probably close (114).' % (exc,))
			self._cleanup(sock)
			return False

		if not data:
			self._cleanup(sock)
			return False

		try:
			state = self.__states[sock]
		except KeyError:
			return False
		state.buffer += data

		self.reset_connection_timeout(state)

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
				self._cleanup(sock)
				return False
			state.requests[msg.id] = msg
			state.session.execute('parse_error', msg, exc)

		return True

	def _do_send(self, sock):
		# type: (socket.socket) -> bool
		try:
			state = self.__states[sock]
		except KeyError:
			CORE.warn('The socket was already removed.')
			return False
		try:
			id, first = state.resend_queue.pop(0)
		except IndexError:
			CORE.error('The response queue for %r is empty.' % (state,))
			return False
		try:
			ret = sock.send(first)
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
			self._cleanup(sock)
			return False
		except socket.error as exc:
			CORE.warn('socket.error in _do_send: %s. Probably the socket was closed by the client.' % (exc,))
			self._cleanup(sock)
			return False

		return (len(state.resend_queue) > 0)

	def _response(self, msg, state):
		# type: (Message, State) -> None
		''' Send UMCP response to client. If the status code is 250 the
		module process is asking for exit. This method forfills the
		request.'''
		if msg.id not in state.requests and msg.id != -1:
			CORE.info('The given response is invalid or not known (%s)' % (msg.id,))
			return

		self.reset_connection_timeout(state)
		try:
			data = bytes(msg)
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
		except socket.error as exc:
			CORE.warn('socket error in _response: %s. Probably the socket was closed by the client.' % (exc,))
			self._cleanup(state.socket)
		except Exception:  # close the connection to the client. we can't do anything else
			CORE.error('FATAL ERROR: %s' % (traceback.format_exc(),))
			self._cleanup(state.socket)

	def _cleanup(self, sock):
		# type: (socket.socket) -> None
		state = self.__states.pop(sock, None)
		if state is None:
			return

		state.session.close_session()

		notifier.socket_remove(sock)
		try:
			sock.close()
		except Exception:
			pass

		state.session.signal_disconnect('success', self._response)


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

	def __init__(self, port=6670, ssl=True, unix=None, magic=True, magicClass=MagicBucket, load_ressources=True, processes=1):
		# type: (int, bool, Optional[str], bool, Type[MagicBucket], bool, int) -> None
		'''Initializes the socket to listen for requests'''
		signals.Provider.__init__(self)

		# loading resources
		if load_ressources:
			CORE.info('Loading resources ...')
			self.reload()

		self.__port = port
		self.__unix = unix
		self.__realtcpsocket = None  # type: Optional[socket.socket]
		self.__realunixsocket = None  # type: Optional[socket.socket]
		self.__ssl = ssl
		self.__processes = processes
		self._child_number = None  # type: Optional[int]
		self._children = {}  # type: Dict[int, int]
		self.__magic = magic
		self.__magicClass = magicClass
		self.__bucket = None  # type: Optional[MagicBucket]

	def __enter__(self):
		# type: () -> Server
		CORE.info('Initialising server process')
		if self.__unix:
			CORE.info('Using a UNIX socket')
			self.__realunixsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		if self.__port:
			CORE.info('Using a TCP socket')
			try:
				self.__realtcpsocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
			except Exception:
				CORE.warn('Cannot open socket with AF_INET6 (Python reports socket.has_ipv6 is %s), trying AF_INET' % socket.has_ipv6)
				self.__realtcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		for sock in (self.__realtcpsocket, self.__realunixsocket):
			if sock is None:
				continue
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.setblocking(0)
			fd = sock.fileno()
			flags = fcntl.fcntl(fd, fcntl.F_GETFD)
			fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)

		if self.__ssl and self.__port:
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
				self.crypto_context.load_verify_locations('/etc/univention/ssl/ucsCA/CAcert.pem')
			except SSL.Error as exc:
				# SSL is not possible
				CRYPT.error('Setting up SSL configuration failed: %s' % (exc,))
				CRYPT.warn('Communication will not be encrypted!')
				self.__ssl = False
				self.crypto_context = None
				self.__realtcpsocket.bind(('', self.__port))
				CRYPT.info('Server listening to unencrypted connections')
				self.__realtcpsocket.listen(SERVER_MAX_CONNECTIONS)

			if self.crypto_context:
				self.connection = SSL.Connection(self.crypto_context, self.__realtcpsocket)
				self.connection.setblocking(0)
				self.connection.bind(('', self.__port))
				self.connection.set_accept_state()
				CRYPT.info('Server listening to SSL connections')
				self.connection.listen(SERVER_MAX_CONNECTIONS)
		elif not self.__ssl and self.__port:
			self.crypto_context = None
			self.__realtcpsocket.bind(('', self.__port))
			CRYPT.info('Server listening to TCP connections')
			self.__realtcpsocket.listen(SERVER_MAX_CONNECTIONS)

		if self.__unix:
			# ensure that the UNIX socket is only accessible by root
			old_umask = os.umask(0o077)
			try:
				self.__realunixsocket.bind(self.__unix)
			except EnvironmentError:
				if os.path.exists(self.__unix):
					os.unlink(self.__unix)
			finally:
				# restore old umask
				os.umask(old_umask)
			CRYPT.info('Server listening to UNIX connections')
			self.__realunixsocket.listen(SERVER_MAX_CONNECTIONS)

		if self.__processes != 1:
			self._children = multiprocessing.Manager().dict()
			try:
				self._child_number = process.fork_processes(self.__processes, 0)
			except RuntimeError as exc:
				CORE.warn('Child process died: %s' % (exc,))
				os.kill(os.getpid(), signal.SIGTERM)
				raise SystemExit(str(exc))
			if self._child_number is not None:
				self._children[self._child_number] = os.getpid()

		if self.__magic:
			self.__bucket = self.__magicClass()
		else:
			self.signal_new('session_new')

		if self.__ssl:
			notifier.socket_add(self.connection, self._connection)
		if (not self.__ssl and self.__port):
			notifier.socket_add(self.__realtcpsocket, self._connection)
		if self.__unix:
			notifier.socket_add(self.__realunixsocket, self._connection)

		return self

	def __verify_cert_cb(self, conn, cert, errnum, depth, ok):
		# type: (SSL.Connection, X509, int, int, int) -> bool
		CORE.info('__verify_cert_cb: Got certificate: %s' % cert.get_subject())
		CORE.info('__verify_cert_cb: Got certificate issuer: %s' % cert.get_issuer())
		CORE.info('__verify_cert_cb: errnum=%d depth=%d ok=%d' % (errnum, depth, ok))
		return ok

	def _connection(self, sock):
		# type: (socket.socket) -> bool
		'''Signal callback: Invoked on incoming connections.'''
		try:
			sock, addr = sock.accept()
		except EnvironmentError as exc:
			if exc.errno == errno.EAGAIN:
				# got an EAGAIN --> try again later
				return True
			CORE.error('Cannot accept new connection: %s' % (exc,))
			if exc.errno == errno.EMFILE:
				# got an EMFILE --> Too many open files
				# If the process permanently lacks free file descriptors, incoming
				# connections waiting in the listening socket backlog will starve.
				# Therefore the limit is temporarily increased by 2 and the connection
				# waiting in the backlog is temporarily accepted and immediately
				# closed again to provoke an error message in the user's browser.
				soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
				resource.setrlimit(resource.RLIMIT_NOFILE, (soft + 2, hard + 2))
				try:
					sock, addr = sock.accept()
					sock.close()
				except EnvironmentError:
					pass
				finally:
					resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
			else:
				# unknown errno - log traceback and continue
				CORE.error(traceback.format_exc())
			return True
		fd = sock.fileno()
		flags = fcntl.fcntl(fd, fcntl.F_GETFD)
		fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
		sock.setblocking(0)
		if addr:
			client = '%s:%d' % (addr[0], addr[1])
		else:
			client = ''
		CORE.info('Incoming connection from %s' % client)
		if self.__magic:
			self.__bucket.new(client, sock)
		else:
			self.signal_emit('session_new', client, sock)
		return True

	def exit(self):
		# type: () -> None
		'''Shuts down all open connections.'''
		CORE.warn('Shutting down all open connections')

		if self.__bucket:
			self.__bucket.exit()

		if self._child_number is not None:
			self._children.pop(self._child_number, None)

		if self.__ssl and self.__port:
			notifier.socket_remove(self.connection)
			self.connection.close()
		elif not self.__ssl and self.__port and self.__realtcpsocket:
			notifier.socket_remove(self.__realtcpsocket)
			self.__realtcpsocket.close()
			self.__realtcpsocket = None
		if self.__unix:
			if self.__realunixsocket is not None:
				notifier.socket_remove(self.__realunixsocket)
				self.__realunixsocket.close()
				self.__realunixsocket = None
			if self._child_number is None and os.path.exists(self.__unix):
				os.unlink(self.__unix)
			self.__unix = None

		self.__bucket = None

	def __exit__(self, etype, exc, etraceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		self.exit()

	@staticmethod
	def reload():
		# type: () -> None
		"""Reloads resources like module and category definitions"""
		CORE.info('Reloading resources: modules, categories')
		moduleManager.load()
		categoryManager.load()
		RESOURCES.info('Reloading UCR variables')
		ucr.load()

	@staticmethod
	def analyse_memory():
		# type: () -> None
		"""Print the number of living UMC objects. Helpful when analysing memory leaks."""
		components = (
			'protocol.server.State', 'protocol.session.ModuleProcess',
			'protocol.session.Processor', 'protocol.session.SessionHandler',
			'protocol.message.Message', 'protocol.message.Request', 'protocol.message.Response',
			'auth.AuthHandler', 'pam.PamAuth', 'protocol.client.Client',
			'locales.I18N', 'locales.I18N_Manager', 'module.Command', 'module.Flavor', 'module.Module',
			'tools.JSON_List',
			# 'module.Link',
			# 'auth.AuthenticationResult',
			# 'base.Base', 'category.XML_Definition', 'error.UMC_Error',
			# 'module.XML_Definition', 'module.Manager', 'pam.AuthenticationError', 'pam.AuthenticationFailed', 'pam.AuthenticationInformationMissing',
			# 'pam.AccountExpired', 'pam.PasswordExpired', 'pam.PasswordChangeFailed',
			# 'protocol.message.ParseError', 'protocol.message.IncompleteMessageError',
			# 'protocol.modserver.ModuleServer', 'protocol.server.MagicBucket', 'protocol.server.Server',
			# 'protocol.session.ProcessorBase',
			# 'tools.JSON_Object', 'tools.JSON_Dict',
		)
		try:
			import objgraph
		except ImportError:
			return
		CORE.warn('')
		for component in components:
			CORE.warn('%s: %d' % (component, len(objgraph.by_type('univention.management.console.%s' % (component,)))))


class State(object):

	"""Holds information about the state of an active session

	:param str client: IP address + port
	:param socket.socket sock: socket object
	"""

	__slots__ = ('client', 'socket', 'buffer', 'requests', 'resend_queue', 'session', 'timeout', '_timer')

	def __init__(self, client, sock):
		# type: (str, socket.socket) -> None
		self.client = client
		self.socket = sock
		self.buffer = b''
		self.requests = {}  # type: Dict
		self.resend_queue = []  # type: List[Tuple[str, bytes]]
		self.session = SessionHandler()
		self._timer = None
		self.reset_connection_timeout()

	def reset_connection_timeout(self):
		# type: () -> None
		self.timeout = SERVER_CONNECTION_TIMEOUT

	@property
	def active(self):
		# type: () -> bool
		return bool(self.requests or self.session.has_active_module_processes())

	def __repr__(self):
		# type: () -> str
		return '<State(%s %r buffer=%d requests=%d processes=%s)>' % (self.client, self.socket, len(self.buffer), len(self.requests), self.session.has_active_module_processes())
