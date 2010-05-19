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
"""UCS-Virt client using a unix-socket."""

import socket
from univention.uvmm import protocol

class ClientError(Exception):
	"""Error during communication with UVMM daemon."""
	pass

class UVMM_ClientSocket:
	"""UCS-Virt client socket."""
	def __init__(self, socket_path):
		"""Open new UNIX socket to socket_path."""
		try:
			self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.sock.connect(socket_path)
		except socket.error, (errno, msg):
			raise ClientError("Could not open socket '%s': %d" % (socket_path, errno))
	
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
