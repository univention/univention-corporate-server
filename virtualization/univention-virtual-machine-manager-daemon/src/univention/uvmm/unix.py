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
import socket
import logging

logger = logging.getLogger('uvmmd.unix')

client_count = 0
def client_add():
	global client_count
	if False and client_count == 0:
		node_frequency(Nodes.USED_FREQUENCY)
	client_count += 1
def client_remove():
	global client_count
	client_count -= 1
	if False and client_count == 0:
		node_frequency(Nodes.IDLE_FREQUENCY)

class HandlerUNIX(SocketServer.StreamRequestHandler):
	"""Send collected information."""
	def setup(self):
		"""Initialize connection."""
		logger.info('New connection.')
		#super(HandlerUNIX,self).setup()
		SocketServer.StreamRequestHandler.setup(self)
		client_add()
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
				logger.debug('Data recveived: %d' % len(data))
				if data == '':
					self.eos = True
				else:
					buffer += data
				try:
					packet = protocol.Packet.parse(buffer)
					if packet == None:
						continue # waiting
				except protocol.PacketError, (msg,):
					logger.error("Invalid packet received: %s" % (msg,))
					break

				logger.debug('Received packet.')
				(length, command) = packet
				buffer = buffer[length:]

				if not isinstance(command, protocol.Request):
					logger.error('Packet is no UVMM Request. Ignored.')
				logger.info('Request "%s" received' % (command.command,))

				try:
					res = commands[command.command](self, command)
					if res == None:
						res = protocol.Response_OK()
				except KeyError:
					logger.warning('Unknown command "%s".' % (command.command,))
					res = protocol.Response_ERROR()
					res.msg = 'Unknown command "%s".' % (command.command,)
				except CommandError, (msg):
					logger.warning('Error doing command "%s": %s' % (command.command, msg))
					res = protocol.Response_ERROR()
					res.msg = msg
				except:
					import traceback
					res = protocol.Response_ERROR()
					res.msg = traceback.print_exc()

				logger.debug('Sending response.')
				packet = res.pack()
				self.wfile.write(packet)
				self.wfile.flush()
				logger.debug('Done.')
		except EOFError:
			pass
		except socket.error, (err, msg):
			if err != errno.ECONNRESET:
				raise
	def finish(self):
		"""Perform cleanup."""
		logger.info('Connection closed.')
		client_remove()
		#super(HandlerUNIX,self).finish()
		SocketServer.StreamRequestHandler.finish(self)

class ThreadedUnixStreamServer(SocketServer.ThreadingMixIn, SocketServer.UnixStreamServer):
	pass

def unix(options, server_class=ThreadedUnixStreamServer, handler_class=HandlerUNIX):
	"""Run UNIX SOCKET server."""
	try:
		if os.path.exists(options.socket):
			os.remove(options.socket)
	except OSError, (err, errmsg):
		logger.error("Failed to delete old socket '%s': %s" % (options.socket, errmsg))
		sys.exit(1)
	unixd = server_class(options.socket, handler_class)
	logger.info('Server is ready.')
	if hasattr(options, 'callback_ready'):
		options.callback_ready()

	unixd.keep_running = True
	while unixd.keep_running:
		try:
			#unixd.serve_forever()
			unixd.handle_request()
		except KeyboardInterrupt:
			unixd.keep_running = False

	logger.info('Server is terminating.')
	try:
		os.remove(options.socket)
	except OSError, (err, errmsg):
		logger.warning("Failed to delete old socket '%s': %s" % (options.socket, errmsg))
