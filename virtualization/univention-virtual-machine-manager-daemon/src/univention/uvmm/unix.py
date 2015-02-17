# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  UVMM unix socket handler
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
"""UVMM unix-socket handler."""
# http://docs.python.org/library/socketserver.html
# http://akumakun.de/norbert/index.html

import os
import errno
import sys
import SocketServer
import protocol
from commands import commands, CommandError
from node import Nodes, node_frequency
from helpers import N_ as _
import socket
import select
import logging
from OpenSSL import SSL
import traceback
import PAM
import threading

logger = logging.getLogger('uvmmd.unix')

class StreamHandler(SocketServer.StreamRequestHandler):
	"""Handle one client connection."""

	active_count = 0 # Number of active clients.
	client_count = 0 # Number of instances.

	def setup(self):
		"""Initialize connection."""
		StreamHandler.client_count += 1
		self.client_id = StreamHandler.client_count
		logger.info('[%d] New connection.' % (self.client_id,))
		#super(StreamHandler,self).setup()
		SocketServer.StreamRequestHandler.setup(self)
		if False and StreamHandler.active_count == 0:
			node_frequency(Nodes.USED_FREQUENCY)
		StreamHandler.active_count += 1

	def handle(self):
		"""Handle protocol."""
		try:
			self.eos = False
			buffer = ''
			while not self.eos:
				try:
					data = self.request.recv(1024)
				except socket.error, (err, errmsg):
					if err == errno.EINTR:
						continue
					else:
						raise
				except SSL.SysCallError, (err, errmsg):
					if err == -1: # and errmsg == 'Unexpected EOF': # Bug 20467
						self.eos = True
						break
				logger.debug('[%d] Data recveived: %d' % (self.client_id, len(data)))
				if data == '':
					self.eos = True
				else:
					buffer += data
				try:
					packet = protocol.Packet.parse(buffer)
					if packet is None:
						continue # waiting
				except protocol.PacketError, e: # (translatable_text, dict):
					logger.warning("[%d] Invalid packet received: %s" % (self.client_id, e))
					if logger.isEnabledFor(logging.DEBUG):
						logger.debug("[%d] Dump: %r" % (self.client_id, data))
					break

				logger.debug('[%d] Received packet.' % (self.client_id,))
				(length, command) = packet
				buffer = buffer[length:]

				if isinstance(command, protocol.Request):
					res = self.handle_command(command)
				else:
					logger.warning('[%d] Packet is no UVMM Request. Ignored.' % (self.client_id,))
					res = protocol.Response_ERROR()
					res.translatable_text = _('Packet is no UVMM Request: %(type)s')
					res.values = {
							'type': type(command),
							}

				logger.debug('[%d] Sending response.' % (self.client_id,))
				packet = res.pack()
				self.wfile.write(packet)
				self.wfile.flush()
				logger.debug('[%d] Done.' % (self.client_id,))
		except EOFError:
			pass
		except socket.error, (err, errmsg):
			if err != errno.ECONNRESET:
				logger.error('[%d] Exception: %s' % (self.client_id, traceback.format_exc()))
				raise
			else:
				logger.warn('[%d] NetException: %s' % (self.client_id, traceback.format_exc()))
		except Exception, e:
			logger.critical('[%d] Exception: %s' % (self.client_id, traceback.format_exc()))
			raise

	def handle_command(self, command):
		"""Handle command packet."""
		logger.info('[%d] Request "%s" received' % (self.client_id, command.command,))
		try:
			cmd = commands[command.command]
		except KeyError, e:
			logger.warning('[%d] Unknown command "%s": %s.' % (self.client_id, command.command,str(e)))
			res = protocol.Response_ERROR()
			res.translatable_text = '[%(id)d] Unknown command "%(command)s".'
			res.values = {
					'id': self.client_id,
					'command': command.command,
					}
		else:
			try:
				res = cmd(self, command)
				if res is None:
					res = protocol.Response_OK()
			except CommandError, e:
				logger.warning('[%d] Error doing command "%s": %s' % (self.client_id, command.command, e))
				res = protocol.Response_ERROR()
				res.translatable_text, res.values = e.args
			except Exception, e:
				logger.error('[%d] Exception: %s' % (self.client_id, traceback.format_exc()))
				res = protocol.Response_ERROR()
				res.translatable_text = _('Exception: %(exception)s')
				res.values = {
						'exception': str(e),
						}
		return res

	def finish(self):
		"""Perform cleanup."""
		logger.info('[%d] Connection closed.' % (self.client_id,))
		StreamHandler.active_count -= 1
		if False and StreamHandler.active_count == 0:
			node_frequency(Nodes.IDLE_FREQUENCY)
		#super(StreamHandler,self).finish()
		SocketServer.StreamRequestHandler.finish(self)

class PamAuthenticator(object):
	"""
	Handle PAM authentication asynchronously.

	>>> p = PamAuthenticator()
	>>> req = protocol.Request_GROUP_LIST()
	>>> print p.handle(req)
	Packet:
	 challenge: [('login:', 2)]
	 status: AUTHENTICATION
	>>> req = protocol.Request_AUTHENTICATION(response=[('testuser1', PAM.PAM_SUCCESS)])
	>>> print p.handle(req)
	Packet:
	 challenge: [('Password: ', 1)]
	 status: AUTHENTICATION
	>>> req = protocol.Request_AUTHENTICATION(response=[('univention', PAM.PAM_SUCCESS)])
	>>> print p.handle(req)
	None
	>>> req = protocol.Request_GROUP_LIST()
	>>> print p.handle(req)
	None
	"""
	PAM_SERVICE = 'uvmmd'
	TIMEOUT = 60.0 # s
	AUTH_INIT, AUTH_RUNNING, AUTH_OK, AUTH_FAIL = range(4)

	def __init__(self, client_address):
		"""Initialize PAM authenticator."""
		self.client_address = client_address
		self.state = PamAuthenticator.AUTH_INIT
		self.response_pending = threading.Event()
		self.challenge_pending = threading.Event()
		self.thread = threading.Thread(target=PamAuthenticator.run, args=(self,))
		self.thread.daemon = True

	@staticmethod
	def pam_conv(auth, query_list, userData):
		"""
		PAM conversation function.
		http://www.kernel.org/pub/linux/libs/pam/Linux-PAM-html/adg-interface-of-app-expected.html#adg-pam_conv
		"""
		self = userData
		if self.state != PamAuthenticator.AUTH_RUNNING:
			raise PAM.error('Authenticator not running: %d' % (self.state,))
		try:
			self.res = protocol.Response_AUTHENTICATION(challenge=query_list)
			# clear internal flag
			self.response_pending.clear()
			# signal response needed
			self.challenge_pending.set()
			logger.debug('Authentication required: %s' % (query_list,))
			# wait for response
			self.response_pending.wait(PamAuthenticator.TIMEOUT)
			if not self.response_pending.isSet():
				self.state = PamAuthenticator.AUTH_FAIL
				raise PAM.error('Timeout!')
			return self.response
		except Exception, e:
			logger.error('Error doing conversation: %s' % (e,))
			raise

	@staticmethod
	def run(self):
		"""Thread doing PAM authentication."""
		try:
			try:
				auth = PAM.pam()
				auth.start(PamAuthenticator.PAM_SERVICE)
				auth.set_item(PAM.PAM_RHOST, self.client_address)
				auth.set_item(PAM.PAM_CONV, self.pam_conv)
				auth.setUserData(self)
				auth.authenticate()
				auth.acct_mgmt()
				del auth
				# signal success
				logger.info('Authentication succeeded')
				self.state = PamAuthenticator.AUTH_OK
				self.res = None
			except Exception, e:
				logger.error('Authentication failed: %s' % e)
				self.state = PamAuthenticator.AUTH_FAIL
				self.res = protocol.Response_ERROR()
				self.res.translatable_text = _('Authentication failed')
		finally:
			self.challenge_pending.set()

	def handle(self, command):
		"""
		Handle authentication: If the connection is not yet authenticated,
		start PAM authentication and handle challenge-response through
		AUTHENTICATION packets.
		Returns None on success, Response_AUTHENTICATION on further negotiation
		and Response_ERROR on failure."""
		if self.state == PamAuthenticator.AUTH_OK:
			return None

		if self.state == PamAuthenticator.AUTH_FAIL:
			return self.res

		self.challenge_pending.clear()
		if self.state == PamAuthenticator.AUTH_INIT:
			self.state = PamAuthenticator.AUTH_RUNNING
			self.thread.start()
		else: # self.state == PamAuthenticator.AUTH_RUNNING:
			if not isinstance(command, protocol.Request_AUTHENTICATION):
				logger.warn('Authentication protocol violated: %s' % (command,))
				# terminate thread
				self.state = PamAuthenticator.AUTH_FAIL
				self.response = None
				self.response_pending.set()
				self.thread.join()
				self.res = protocol.Response_ERROR()
				self.res.translatable_text = _('Authentication protocol violated')
				return self.res
			self.response = command.response
			self.response_pending.set()

		self.challenge_pending.wait(PamAuthenticator.TIMEOUT)
		if self.res is None:
			self.thread.join()
		return self.res

class AuthenticatedStreamHandler(StreamHandler):
	"""Handle TCP client connection requiring authentication."""
	def setup(self):
		"""Authenticated connection."""
		#super(AuthenticatedStreamHandler,self).setup()
		StreamHandler.setup(self)
		self.authenticator = PamAuthenticator(self.client_address[0])

	def finish(self):
		"""Perform cleanup."""
		self.authenticator.handle(None)
		#super(AuthenticatedStreamHandler,self).finish()
		StreamHandler.finish(self)

	def handle_command(self, command):
		"""Handle command packet."""
		res = self.authenticator.handle(command)
		if res is None:
			#res = super(AuthenticatedStreamHandler,self).handle_command(command)
			res = StreamHandler.handle_command(self, command)
		return res

class SecureStreamHandler(AuthenticatedStreamHandler):
	"""Handle one TCP-SSL client connection."""
	def setup(self):
		"""SSL connection doesn't support makefile, wrap it."""
		request = self.request
		class SslConnection:
			def makefile(this, mode, size):
				return socket._fileobject(request, mode, size)
		self.request = SslConnection()
		#super(SecureStreamHandler,self).setup()
		AuthenticatedStreamHandler.setup(self)
		self.connection = self.request = request

class ThreadingSSLServer(SocketServer.ThreadingTCPServer):
	"""SSL encrypted TCP server."""
	allow_reuse_address = True
	privatekey = '/etc/univention/ssl/%s/private.key' % socket.getfqdn()
	certificate = '/etc/univention/ssl/%s/cert.pem' % socket.getfqdn()
	cas = '/etc/univention/ssl/ucsCA/CAcert.pem'

	def __init__(self, server_address, handler_class):
		SocketServer.ThreadingTCPServer.__init__(self, server_address, handler_class)

		ctx = SSL.Context(SSL.SSLv23_METHOD)
		ctx.set_options(SSL.OP_NO_SSLv2)
		#ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
		ctx.use_privatekey_file(ThreadingSSLServer.privatekey)
		ctx.use_certificate_file(ThreadingSSLServer.certificate)
		ctx.load_verify_locations(ThreadingSSLServer.cas)

		self.socket = SSL.Connection(ctx, self.socket)

def unix(options):
	"""Run UNIX SOCKET server."""
	try:
		if os.path.exists(options.socket):
			os.remove(options.socket)
	except OSError, (err, errmsg):
		logger.error("Failed to delete old socket '%s': %s" % (options.socket, errmsg))
		sys.exit(1)

	sockets = {}
	if options.socket:
		try:
			unixd = SocketServer.ThreadingUnixStreamServer(options.socket, StreamHandler)
			unixd.daemon_threads = True
			sockets[unixd.fileno()] = unixd
		except Exception, e:
			logger.error("Could not create UNIX server: %s" % (e,))
	if options.tcp:
		try:
			if ':' in options.tcp:
				host, port = options.tcp.rsplit(':', 1)
			else:
				host, port = options.tcp, 2105
			tcpd = SocketServer.ThreadingTCPServer((host, int(port)), AuthenticatedStreamHandler)
			tcpd.daemon_threads = True
			tcpd.allow_reuse_address = True
			sockets[tcpd.fileno()] = tcpd
		except Exception, e:
			logger.error("Could not create TCP server: %s" % (e,))
	if options.ssl:
		try:
			if ':' in options.ssl:
				host, port = options.ssl.rsplit(':', 1)
			else:
				host, port = options.ssl, 2106
			ssld = ThreadingSSLServer((host, int(port)), SecureStreamHandler)
			ssld.daemon_threads = True
			ssld.allow_reuse_address = True
			sockets[ssld.fileno()] = ssld
		except Exception, e:
			logger.error("Could not create SSL server: %s" % (e,))
	if not sockets:
		logger.error("Neither UNIX, TCP, nor SSL server.")
		return

	logger.info('Server is ready.')
	if hasattr(options, 'callback_ready'):
		options.callback_ready()

	keep_running = True
	while keep_running:
		try:
			rlist, wlist, xlist = select.select(sockets.keys(), [], [], None)
			for fd in rlist:
				sockets[fd].handle_request()
		except (select.error, socket.error), (err, errmsg):
			if err == errno.EINTR:
				continue
			else:
				raise
		except KeyboardInterrupt:
			keep_running = False

	logger.info('Server is terminating.')
	try:
		os.remove(options.socket)
	except OSError, (err, errmsg):
		logger.warning("Failed to delete old socket '%s': %s" % (options.socket, errmsg))

if __name__ == '__main__':
	import doctest
	doctest.testmod()
