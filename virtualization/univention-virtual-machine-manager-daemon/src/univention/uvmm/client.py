#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  UVMM client
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
"""UVMM client using a unix-socket."""

import socket
from univention.uvmm import protocol
from OpenSSL import SSL

class ClientError(Exception):
	"""Error during communication with UVMM daemon."""
	pass

class UVMM_ClientSocket:
	"""UVMM client."""

	def send(self, req):
		"""Send request, wait for and return answer."""
		packet = req.pack()
		try:
			self.sock.send(packet)
			return self.receive()
		except socket.error, (errno, msg):
			raise ClientError("Could not send request: %d" % (errno,))

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
				if packet == None:
					continue # waiting

				(length, res) = packet
				buffer = buffer[length:]

				if not isinstance(res, protocol.Response):
					raise ClientError('Not a UVMM_Response.')
				else:
					return res
		except protocol.PacketError, (msg,):
			raise ClientError("Invalid packet received: %s" % (msg,))
		except socket.error, (errno, msg):
			raise ClientError("Error while waiting for answer: %d" % (errno,))
		except EOFError:
			raise ClientError("EOF while waiting for answer.")

	def close(self):
		"""Close socket."""
		try:
			self.sock.close()
			self.sock = None
		except socket.error, (errno, msg):
			raise ClientError("Error while closing socket: %d" % (errno,))

class UVMM_ClientUnixSocket(UVMM_ClientSocket):
	"""UVMM client Unix socket."""

	def __init__(self, socket_path):
		"""Open new UNIX socket to socket_path."""
		try:
			self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.sock.connect(socket_path)
		except socket.error, (errno, msg):
			raise ClientError("Could not open socket '%s': %d" % (socket_path, errno))

	def __str__(self):
		return "UNIX Socket %s" % (self.sock.getpeername(),)

class UVMM_ClientTCPSocket(UVMM_ClientSocket):
	"""UVMM client TCP socket to (str(host), int(port))."""
	def __init__(self, host, port=2105):
		"""Open new TCP socket to host:port."""
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((host, port))
		except socket.error, (errno, msg):
			raise ClientError("Could not connect to '%s:%d': %d" % (host, port, errno))

	def __str__(self):
		return "TCP Socket %s:%d -> %s:%d" % (self.sock.getsockname() + self.sock.getpeername())

class UVMM_ClientSSLSocket(UVMM_ClientSocket):
	"""UVMM client SSL enctrypted TCP socket to (str(host), int(port))."""
	privatekey = '/etc/univention/ssl/%s/private.key' % socket.getfqdn()
	certificate = '/etc/univention/ssl/%s/cert.pem' % socket.getfqdn()
	cas = '/etc/univention/ssl/ucsCA/CAcert.pem'

	def __init__(self, host, port=2106):
		"""Open new SSL encrypted TCP socket to host:port."""
		try:
			ctx = SSL.Context(SSL.SSLv23_METHOD)
			ctx.set_options(SSL.OP_NO_SSLv2)
			#ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
			ctx.use_privatekey_file(UVMM_ClientSSLSocket.privatekey)
			ctx.use_certificate_file(UVMM_ClientSSLSocket.certificate)
			ctx.load_verify_locations(UVMM_ClientSSLSocket.cas)

			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock = SSL.Connection(ctx, sock)
			self.sock.connect((host, port))
		except socket.error, (errno, msg):
			raise ClientError("Could not connect to '%s:%d': %d" % (host, port, errno))

	def __str__(self):
		return "TCP-SSL Socket %s:%d -> %s:%d" % (self.sock.getsockname() + self.sock.getpeername())
