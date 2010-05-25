#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  listener module
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
"""UVMM protocol."""
try:
	import cPickle as pickle
except ImportError:
	import pickle
import struct

VERSION = (1, 0)
MAX_MSG_SIZE = 4096

class PacketError(Exception):
	"""Packet framing error."""
	pass

class Packet:
	"""On-wire packet format."""
	def __init__(self, **kw):
		"""Create new packet."""
		self._default()
		for k, v in kw.items():
			if hasattr(self, k):
				setattr(self, k, v)
			else:
				raise AttributeError("Packet '%s' has no attribute '%s'" % (str(self.__class__)[len(self.__class__.__module__)+1:], k))
	def __str__(self):
		res = ['Packet:']
		for attr in dir(self):
			if not attr.startswith('_') and attr not in ('pack','parse'):
				res.append(' %s: %s' % (attr, str(getattr(self, attr))))
		return '\n'.join(res)
	def pack(self):
		"""Pack data for transfer."""
		data = pickle.dumps(self)
		return struct.pack('!HHI', VERSION[0], VERSION[1], len(data)) + data
	@staticmethod
	def parse(buffer, offset=0):
		"""Unpack packet from data."""
		FORMAT = '!HHI'
		SIZE = struct.calcsize(FORMAT)
		if len(buffer) < offset + SIZE:
			return None
		(v1, v2, length,) = struct.unpack(FORMAT, buffer[offset:offset + SIZE])
		if VERSION[0] != v1 or VERSION[1] > v2:
			raise PacketError('Incompatible version: %d.%d' % (v1, v2))
		if len(buffer) < offset + SIZE + length:
			return None
		(data,) = struct.unpack('%ds' % length, buffer[offset + SIZE:offset + SIZE + length])
		packet = pickle.loads(data)
		if not isinstance(packet, Packet):
			raise PacketError('not a Packet')
		else:
			return (SIZE + length, packet)

class Request(Packet):
	"""Super class of all requests to UVMM daemon."""
	def _default(self):
		self.command = None

class Request_NODE_ADD(Request):
	"""Add node to watch list."""
	def _default(self):
		self.command = 'NODE_ADD'
		self.uri = None # xen:/// xen+unix:/// xen+ssh://root@bs22.pmhahn22.qa/ qemu:///system qemu+unix:///system qemu+ssh://root@bs22.pmhahn22.qa/system
class Request_NODE_REMOVE(Request):
	"""Remove node to watch list."""
	def _default(self):
		self.command = 'NODE_REMOVE'
		self.uri = None # xen:/// xen+unix:/// xen+ssh://root@bs22.pmhahn22.qa/ qemu:///system qemu+unix:///system qemu+ssh://root@bs22.pmhahn22.qa/system
class Request_NODE_QUERY(Request):
	"""Query node on watch list."""
	def _default(self):
		self.command = 'NODE_QUERY'
		self.uri = None # xen:/// xen+unix:/// xen+ssh://root@bs22.pmhahn22.qa/ qemu:///system qemu+unix:///system qemu+ssh://root@bs22.pmhahn22.qa/system
class Request_NODE_FREQUENCY(Request):
	"""Set query frequency for nodes on watch list."""
	def _default(self):
		self.command = 'NODE_FREQUENCY'
		self.hz = None # 1/ms
		self.uri = None # xen:/// xen+unix:/// xen+ssh://root@bs22.pmhahn22.qa/ qemu:///system qemu+unix:///system qemu+ssh://root@bs22.pmhahn22.qa/system
class Request_NODE_LIST(Request):
	"""Query for list of watched nodes."""
	def _default(self):
		self.command = 'NODE_LIST'
		self.group = None
class Request_GROUP_LIST(Request):
	"""Query for list of watched nodes."""
	def _default(self):
		self.command = 'GROUP_LIST'
class Request_BYE(Request):
	"""Disconnect client."""
	def _default(self):
		self.command = 'BYE'
class Request_DOMAIN_DEFINE(Request):
	"""Define new or replace old domain."""
	def _default(self):
		self.command = 'DOMAIN_DEFINE'
		self.uri = None
		self.domain = None
class Request_DOMAIN_STATE(Request):
	"""Change running state of defined domain."""
	def _default(self):
		self.command = 'DOMAIN_STATE'
		self.uri = None
		self.domain = None
		self.state = None # RUN PAUSE SHUTDOWN RESTART
class Request_DOMAIN_SAVE(Request):
	"""Save defined domain."""
	def _default(self):
		self.command = 'DOMAIN_SAVE'
		self.uri = None
		self.domain = None
		self.statefile = None
class Request_DOMAIN_RESTORE(Request):
	"""Resume defined domain."""
	def _default(self):
		self.command = 'DOMAIN_RESTORE'
		self.uri = None
		self.statefile = None
class Request_DOMAIN_UNDEFINE(Request):
	"""Remove domain."""
	def _default(self):
		self.command = 'DOMAIN_UNDEFINE'
		self.uri = None
		self.domain = None
		self.volumes = []
class Request_DOMAIN_MIGRATE(Request):
	"""Migrate domain."""
	def _default(self):
		self.command = 'DOMAIN_MIGRATE'
		self.uri = None
		self.domain = None
		self.target_uri = None

class Response(Packet):
	"""Super class of all responses from UVMM daemon."""
	def _default(self):
		self.status = None
class Response_ERROR(Response):
	def _default(self):
		self.status = 'ERROR'
		self.msg = None
class Response_OK(Response):
	def _default(self):
		self.status = 'OK'
class Response_DUMP(Response):
	def _default(self):
		self.status = 'OK'
		self.data = {}

class Data_StoragePool(object):
	"""Container for storage pool statistics."""
	def __init__(self):
		self.uuid = None
		self.name = None
		self.capacity = None
		self.available = None
	def _json(self):
		return {
			'uuid':self.uuid,
			'name':self.name,
			'capacity':self.capacity,
			'available':self.available,
			}
class Data_Domain(object):
	"""Container for domain statistics."""
	def __init__(self):
		self.uuid = None
		self.name = None
		self.os = None
		self.kernel = None
		self.cmdline = None
		self.initrd = None
		self.state = None
		self.maxMem = None
		self.curMem = None
		self.vcpus = None
		self.cputime = [0.0, 0.0, 0.0]
		self.interfaces = []
		self.disks = []
		self.graphics = []
	def _json(self):
		return {
			'uuid':self.uuid,
			'name':self.name,
			'os':self.os,
			'kernel':self.kernel,
			'cmdline':self.cmdline,
			'initrd':self.initrd,
			'state':self.state,
			'maxMem':self.maxMem,
			'curMem':self.curMem,
			'vcpus':self.vcpus,
			'cputime':self.cputime,
			'graphics': [ str( g ) for g in self.graphics ],
			'interfaces': [ str( i ) for i in self.interfaces ],
			'disks': [ str( d ) for d in self.disks ],
			}
class Data_Node(object):
	"""Container for node statistics."""
	def __init__(self):
		self.name = None
		self.phyMem = None
		self.curMem = None
		self.maxMem = None
		self.cpus = None
		self.cores = [None, None, None, None]
		self.storages = []
		self.domains = []
		self.capabilities = {}
	def _json(self):
		return {
			'name':self.name,
			'phyMem':self.phyMem,
			'curMem':self.curMem,
			'maxMem':self.maxMem,
			'cpus':self.cpus,
			'cores':self.cores,
			'storages':[s._json() for s in self.storages],
			'domains':[d._json() for d in self.domains],
			'capabilities':[str(tmp) for tmp in self.capabilities],
			}
