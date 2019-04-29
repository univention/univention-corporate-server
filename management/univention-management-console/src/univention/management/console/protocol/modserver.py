#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
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

"""This module provides a class for an UMC module server. it is based on
the UMC server class
:class:`~univention.management.console.protocol.server.Server`.
"""

import errno
import sys
import traceback
import socket

import notifier
import six

from .server import Server
from .message import Response, Message, IncompleteMessageError, ParseError
from .definitions import MODULE_ERR_INIT_FAILED, SUCCESS, RECV_BUFFER_SIZE

from univention.management.console.acl import ACLs
from univention.management.console.module import Module
from univention.management.console.log import MODULE, PROTOCOL

from univention.lib.i18n import Translation

_ = Translation('univention.management.console').translate


class ModuleServer(Server):

	"""Implements an UMC module server

	:param str socket: UNIX socket filename
	:param str module: name of the UMC module to serve
	:param int timeout: If there are no incoming requests for *timeout* seconds the module server shuts down
	:param bool check_acls: if False the module server does not check the permissions (**dangerous!**)
	"""

	def __init__(self, socket, module, timeout=300, check_acls=True):
		self.__name = module
		self.__module = module
		self.__commands = Module()
		self.__comm = None
		self.__client = None
		self.__buffer = ''
		self.__acls = None
		self.__timeout = timeout
		self.__time_remaining = timeout
		self.__active_requests = 0
		self._timer()
		self.__check_acls = check_acls
		self.__queue = ''
		self.__username = None
		self.__user_dn = None
		self.__password = None
		self.__init_etype = None
		self.__init_exc = None
		self.__init_etraceback = None
		self.__handler = None
		self._load_module()
		Server.__init__(self, ssl=False, unix=socket, magic=False, load_ressources=False)
		MODULE.process('Module socket initialized.')
		self.signal_connect('session_new', self._client)

	def _load_module(self):
		MODULE.process('Loading python module.')
		modname = self.__module
		from ..error import UMC_Error
		try:
			try:
				file_ = 'univention.management.console.modules.%s' % (modname,)
				self.__module = __import__(file_, [], [], modname)
				MODULE.process('Imported python module.')
				self.__handler = self.__module.Instance()
				MODULE.process('Module instance created.')
			except Exception as exc:
				error = _('Failed to load module %(module)s: %(error)s\n%(traceback)s') % {'module': modname, 'error': exc, 'traceback': traceback.format_exc()}
				MODULE.error(error)
				if isinstance(exc, ImportError) and str(exc).startswith('No module named %s' % (modname,)):
					error = '\n'.join((
						_('The requested module %r does not exist.') % (modname,),
						_('The module may have been removed recently.'),
						_('Please relogin to the Univention Management Console to see if the error persists.'),
						_('Further information can be found in the logfile %s.') % ('/var/log/univention/management-console-module-%s.log' % (modname,),),
					))
				raise UMC_Error(error, status=MODULE_ERR_INIT_FAILED)
		except UMC_Error:
			try:
				exc_info = sys.exc_info()
				self.__init_etype, self.__init_exc, self.__init_etraceback = exc_info  # FIXME: do not keep a reference to traceback
			finally:
				exc_info = None
		else:
			self.__handler.signal_connect('success', notifier.Callback(self._reply, True))

	def _reply(self, msg, final):
		if final:
			self.__active_requests -= 1
		self.response(msg)

	def _timer(self):
		"""In order to avoid problems when the system time is changed (e.g.,
		via rdate), we register a timer event that counts down the session
		timeout second-wise."""
		# count down the remaining time
		if not self.__active_requests:
			self.__time_remaining -= 1

		if self.__time_remaining <= 0:
			# module has timed out
			self._timed_out()
		else:
			# count down the timer second-wise (in order to avoid problems when
			# changing the system time, e.g. via rdate)
			notifier.timer_add(1000, self._timer)

	def _timed_out(self):
		MODULE.info('Committing suicide')
		if self.__handler:
			self.__handler.destroy()
		self.exit()
		sys.exit(0)

	def _client(self, client, socket):
		self.__comm = socket
		self.__client = client
		notifier.socket_add(self.__comm, self._recv)

	def _recv(self, sock):
		try:
			data = sock.recv(RECV_BUFFER_SIZE)
		except socket.error as exc:
			MODULE.error('Failed connection: %s' % (errno.errorcode.get(exc.errno, exc.errno),))
			data = None

		# connection closed?
		if not data:
			sock.close()
			if sock == self.__comm:
				MODULE.info('UMC server connection closed. This module is no longer in use.')
				# the connection to UMC server connection has been closed/died/...
				# so from now on this module is unused. Thus it is committing suicide right now.
				self._timed_out()
			else:
				MODULE.info('Connection %r closed' % (sock,))
			# remove socket from notifier
			return False

		self.__buffer += data

		msg = None
		while self.__buffer:
			try:
				msg = Message()
				self.__buffer = msg.parse(self.__buffer)
				MODULE.info("Received request %s" % msg.id)
				self.handle(msg)
			except IncompleteMessageError:
				MODULE.info('Failed to parse incomplete message')
				return True
			except ParseError as exc:
				MODULE.error('Failed to parse message: %s' % (exc,))
				if not msg.id:
					msg.id = -1
				status, message = exc.args
				from ..error import UMC_Error
				raise UMC_Error(message, status=status)
			except (KeyboardInterrupt, SystemExit, GeneratorExit):
				raise
			except:
				self.error_handling(msg, 'init', *sys.exc_info())

		return True

	def error_handling(self, request, method, etype, exc, etraceback):
		if self.__handler:
			self.__handler._Base__requests[request.id] = (request, method)
			self.__handler._Base__error_handling(request, method, etype, exc, etraceback)
			return

		trace = ''.join(traceback.format_exception(etype, exc, etraceback))
		MODULE.error('The init function of the module failed\n%s: %s' % (exc, trace,))
		from ..error import UMC_Error
		if not isinstance(exc, UMC_Error):
			error = _('The initialization of the module failed: %s') % (trace,)
			exc = UMC_Error(error, status=MODULE_ERR_INIT_FAILED)
			etype = UMC_Error

		resp = Response(request)
		resp.status = exc.status
		resp.message = str(exc)
		resp.result = exc.result
		resp.headers = exc.headers
		self.response(resp)

	def handle(self, msg):
		"""Handles incoming UMCP requests. This function is called only
		when it is a valid UMCP request.

		:param Request msg: the received UMCP request

		The following commands are handled directly and are not passed
		to the custom module code:

		* SET (acls|username|credentials)
		* EXIT
		"""
		from ..error import UMC_Error, NotAcceptable
		self.__time_remaining = self.__timeout
		PROTOCOL.info('Received UMCP %s REQUEST %s' % (msg.command, msg.id))

		resp = Response(msg)
		resp.status = SUCCESS

		if msg.command == 'EXIT':
			shutdown_timeout = 100
			MODULE.info("EXIT: module shutdown in %dms" % shutdown_timeout)
			# shutdown module after one second
			resp.message = 'module %s will shutdown in %dms' % (msg.arguments[0], shutdown_timeout)
			self.response(resp)
			notifier.timer_add(shutdown_timeout, self._timed_out)
			return

		if self.__init_etype:
			notifier.timer_add(10000, self._timed_out)
			six.reraise(self.__init_etype, self.__init_exc, self.__init_etraceback)

		if msg.command == 'SET':
			for key, value in msg.options.items():
				if key == 'acls':
					self.__acls = ACLs(acls=value)
					self.__handler.acls = self.__acls
				elif key == 'commands':
					self.__commands.fromJSON(value['commands'])
				elif key == 'username':
					self.__username = value
					self.__handler.username = self.__username
				elif key == 'password':
					self.__password = value
					self.__handler.password = self.__password
				elif key == 'auth_type':
					self.__auth_type = value
					self.__handler.auth_type = self.__auth_type
				elif key == 'credentials':
					self.__username = value['username']
					self.__user_dn = value['user_dn']
					self.__password = value['password']
					self.__auth_type = value.get('auth_type')
					self.__handler.username = self.__username
					self.__handler.user_dn = self.__user_dn
					self.__handler.password = self.__password
					self.__handler.auth_type = self.__auth_type
				elif key == 'locale' and value is not None:
					try:
						self.__handler.update_language([value])
					except NotAcceptable:
						pass  # ignore if the locale doesn't exists, it continues with locale C
				else:
					raise UMC_Error(status=422)

			# if SET command contains 'acls', commands' and
			# 'credentials' it is the initialization of the module
			# process
			if 'acls' in msg.options and 'commands' in msg.options and 'credentials' in msg.options:
				MODULE.process('Initializing module.')
				try:
					self.__handler.init()
				except BaseException:
					try:
						exc_info = sys.exc_info()
						self.__init_etype, self.__init_exc, self.__init_etraceback = exc_info  # FIXME: do not keep a reference to traceback
						self.error_handling(msg, 'init', *exc_info)
					finally:
						exc_info = None
					return

			self.response(resp)
			return

		if msg.arguments:
			cmd = msg.arguments[0]
			cmd_obj = self.command_get(cmd)
			if cmd_obj and (not self.__check_acls or self.__acls.is_command_allowed(cmd, options=msg.options, flavor=msg.flavor)):
				self.__active_requests += 1
				self.__handler.execute(cmd_obj.method, msg)
				return
			raise UMC_Error('Not initialized.', status=403)

	def command_get(self, command_name):
		"""Returns the command object that matches the given command name"""
		for cmd in self.__commands.commands:
			if cmd.name == command_name:
				return cmd
		return None

	def command_is_known(self, command_name):
		"""Checks if a command with the given command name is known

		:rtype: bool
		"""
		for cmd in self.__commands.commands:
			if cmd.name == command_name:
				return True
		return False

	def _do_send(self, sock):
		if len(self.__queue) > 0:
			length = len(self.__queue)
			try:
				ret = self.__comm.send(self.__queue)
			except socket.error as e:
				if e[0] == errno.EWOULDBLOCK:
					return True
				if e[0] == errno.EPIPE:
					return False
				raise

			if ret < length:
				self.__queue = self.__queue[ret:]
				return True
			else:
				self.__queue = ''
				return False
		else:
			return False

	def response(self, msg):
		"""Sends an UMCP response to the client"""
		PROTOCOL.info('Sending UMCP RESPONSE %s' % msg.id)
		self.__queue += str(msg)

		if self._do_send(self.__comm):
			notifier.socket_add(self.__comm, self._do_send, notifier.IO_WRITE)
