#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  UVMM unix socket handler
#
# Copyright (C) 2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA
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
from helpers import TranslatableException, N_ as _
import socket
import select
import logging
from OpenSSL import SSL
import traceback

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
				except socket.error, (err, msg):
					if err == errno.EINTR:
						continue
					else:
						raise
				logger.debug('[%d] Data recveived: %d' % (self.client_id, len(data)))
				if data == '':
					self.eos = True
				else:
					buffer += data
				try:
					packet = protocol.Packet.parse(buffer)
					if packet == None:
						continue # waiting
				except protocol.PacketError, (msg,):
					logger.error("[%d] Invalid packet received: %s" % (self.client_id, msg,))
					break

				logger.debug('[%d] Received packet.' % (self.client_id,))
				(length, command) = packet
				buffer = buffer[length:]

				if not isinstance(command, protocol.Request):
					logger.error('[%d] Packet is no UVMM Request. Ignored.' % (self.client_id,))
				logger.info('[%d] Request "%s" received' % (self.client_id, command.command,))

				try:
					res = commands[command.command](self, command)
					if res == None:
						res = protocol.Response_OK()
				except KeyError:
					logger.warning('[%d] Unknown command "%s".' % (self.client_id, command.command,))
					res = protocol.Response_ERROR()
					res.translatable_text = '[%(id)d] Unknown command "%(command)s".'
					res.values = {
							'id': self.client_id,
							'command': command.command,
							}
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

				logger.debug('[%d] Sending response.' % (self.client_id,))
				packet = res.pack()
				self.wfile.write(packet)
				self.wfile.flush()
				logger.debug('[%d] Done.' % (self.client_id,))
		except EOFError:
			pass
		except socket.error, (err, msg):
			if err != errno.ECONNRESET:
				raise

	def finish(self):
		"""Perform cleanup."""
		logger.info('[%d] Connection closed.' % (self.client_id,))
		StreamHandler.active_count -= 1
		if False and StreamHandler.active_count == 0:
			node_frequency(Nodes.IDLE_FREQUENCY)
		#super(StreamHandler,self).finish()
		SocketServer.StreamRequestHandler.finish(self)

class SecureStreamHandler(StreamHandler):
	def setup(self):
		"""SSL connection doesn't support makefile, wrap it."""
		request = self.request
		class SslConnection:
			def makefile(this, mode, size):
				return socket._fileobject(request, mode, size)
		self.request = SslConnection()
		StreamHandler.setup(self)
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
			tcpd = SocketServer.ThreadingTCPServer((host, int(port)), StreamHandler)
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
			for socket in rlist:
				sockets[socket].handle_request()
		except KeyboardInterrupt:
			keep_running = False

	logger.info('Server is terminating.')
	try:
		os.remove(options.socket)
	except OSError, (err, errmsg):
		logger.warning("Failed to delete old socket '%s': %s" % (options.socket, errmsg))

