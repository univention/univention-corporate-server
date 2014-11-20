#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
#
# Copyright 2006-2014 Univention GmbH
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

"""This module provides a class for an UMC module server. it is based on
the UMC server class
:class:`~univention.management.console.protocol.server.Server`.
"""

from .server import Server
from .message import Response, Message, IncompleteMessageError, ParseError, UnknownCommandError
from .definitions import (
	BAD_REQUEST_NOT_FOUND, BAD_REQUEST_INVALID_OPTS,
	MODULE_ERR_INIT_FAILED, SUCCESS, RECV_BUFFER_SIZE, status_description
)

from univention.management.console.acl import ACLs
from univention.management.console.module import Module
from univention.management.console.log import MODULE, PROTOCOL

from univention.lib.i18n import Locale, Translation

_ = Translation('univention.management.console').translate

import errno
import sys
import traceback
import socket
import locale
import notifier


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
		self.__init_error_message = None
		self.__handler = None
		self._load_module()
		Server.__init__(self, ssl=False, unix=socket, magic=False, load_ressources=False)
		self.signal_connect('session_new', self._client)

	def _load_module(self):
		modname = self.__module
		try:
			file_ = 'univention.management.console.modules.%s' % (modname,)
			self.__module = __import__(file_, [], [], modname)
			self.__handler = self.__module.Instance()
		except Exception as exc:
			error = _('Failed to load module %s: %s\n%s') % (modname, exc, traceback.format_exc())
			MODULE.error(error)
			if isinstance(exc, ImportError) and str(exc).startswith('No module named %s' % (modname,)):
				error = '\n'.join((_('The requested module %r does not exists.') % (modname,),
					_('The module may have been removed recently.'),
					_('Please relogin to the Univention Management Console to see if the error persists.'),
					_('Further information can be found in the logfile %s.') % ('/var/log/univention/management-console-module-%s.log' % (modname,),),
				))
			self.__init_error_message = error
		else:
			self.__handler.signal_connect('success', notifier.Callback(self._reply, True))
			self.__handler.signal_connect('failure', notifier.Callback(self._reply, True))

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
		try:
			while self.__buffer:
				msg = Message()
				self.__buffer = msg.parse(self.__buffer)
				MODULE.info("Received request %s" % msg.id)
				self.handle(msg)
		except IncompleteMessageError as e:
			MODULE.info('Failed to parse incomplete message')
		except (ParseError, UnknownCommandError) as e:
			MODULE.error('Failed to parse message: %s' % str(e))
			res = Response(msg)
			res.id = -1
			res.status = e.args[0]
			self.response(res)

		return True

	def handle(self, msg):
		"""Handles incoming UMCP requests. This function is called only
		when it is a valid UMCP request.

		:param Request msg: the received UMCP request

		The following commands are handled directly and are not passed
		to the custom module code:

		* SET (acls|username|credentials)
		* EXIT
		"""
		self.__time_remaining = self.__timeout
		PROTOCOL.info('Received UMCP %s REQUEST %s' % (msg.command, msg.id))
		if msg.command == 'EXIT':
			shutdown_timeout = 100
			MODULE.info("EXIT: module shutdown in %dms" % shutdown_timeout)
			# shutdown module after one second
			resp = Response(msg)
			resp.body = {'status': 'module %s will shutdown in %dms' % (str(msg.arguments[0]), shutdown_timeout)}
			resp.status = SUCCESS
			self.response(resp)
			notifier.timer_add(shutdown_timeout, self._timed_out)
			return

		if not self.__handler:
			resp = Response(msg)
			resp.status = MODULE_ERR_INIT_FAILED
			resp.message = self.__init_error_message
			self.response(resp)
			notifier.timer_add(10000, self._timed_out)
			return

		if msg.command == 'SET':
			resp = Response(msg)
			resp.status = SUCCESS
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
				elif key == 'credentials':
					self.__username = value['username']
					self.__user_dn = value['user_dn']
					self.__password = value['password']
					self.__handler.username = self.__username
					self.__handler.user_dn = self.__user_dn
					self.__handler.password = self.__password
				elif key == 'locale' and value is not None:
					self.__locale = value
					try:
						locale_obj = Locale(value)
						locale.setlocale(locale.LC_MESSAGES, str(locale_obj))
						MODULE.info("Setting specified locale (%s)" % str(locale_obj))
					except locale.Error:
						MODULE.warn("Specified locale is not available (%s)" % str(locale_obj))
						MODULE.warn("Falling back to C")
						# specified locale is not available -> falling back to C
						locale.setlocale(locale.LC_MESSAGES, 'C')
						self.__locale = 'C'
					self.__handler.set_language(self.__locale)
				else:
					resp.status = BAD_REQUEST_INVALID_OPTS
					break

			# if SET command contains 'acls', commands' and
			# 'credentials' it is the initialization of the module
			# process
			if 'acls' in msg.options and 'commands' in msg.options and 'credentials' in msg.options:
				try:
					self.__handler.init()
				except BaseException as exc:
					self.__handler = None
					error = _('The initialization of the module failed: %s') % (exc,)
					trace = traceback.format_exc()

					MODULE.error('The init function of the module failed\n%s: %s' % (exc, trace,))
					resp.status = MODULE_ERR_INIT_FAILED

					from ..modules import UMC_Error
					if not isinstance(exc, UMC_Error):
						error = trace

					self.__init_error_message = error
					resp.message = error

			self.response(resp)
			return

		if msg.arguments:
			cmd = msg.arguments[0]
			cmd_obj = self.command_get(cmd)
			if cmd_obj and (not self.__check_acls or self.__acls.is_command_allowed(cmd, options=msg.options, flavor=msg.flavor)):
				self.__active_requests += 1
				self.__handler.execute(cmd_obj.method, msg)
				return
			else:
				resp = Response(msg)
				# status 415 (command not allowed) should be checked by the server
				resp.status = BAD_REQUEST_NOT_FOUND
				resp.message = status_description(resp.status)
				self.response(resp)

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
