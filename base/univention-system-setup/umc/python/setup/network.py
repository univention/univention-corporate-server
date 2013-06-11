#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# TODO: add description
# 
#
# Copyright 2013 Univention GmbH
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

import re

import ipaddr

from univention.config_registry import ConfigRegistry

ucr = ConfigRegistry()
ucr.load()

RE_INTERFACE = re.compile(r'^interfaces/([^/_]+)(_[^/]+)?/')

class Interfaces(dict):

	def __init__(self, *args, **kwargs):
		super(Interfaces, self).__init__(*args, **kwargs)
		self.physical_interfaces = [] # TODO: detect

	def prepare(self):
		pass

	def check_consistence(self):
		self.prepare()

		all_ip4s, all_ip6s = set(), set()
		for device in self.values():
			if not device.ip4dynamic:
				for ip4 in device.ip4:
					# check for duplicated IP's
					if ip4[0] in all_ip4s:
						raise ValueError('%s: Duplicated IP address %r' % (device.name, ip4[0]))
					try:
						if ip4[0]:
							# validate IP address
							ipaddr.IPv4Address(ip4[0])

							# TODO: check netmask
					except ipaddr.AddressValueError:
						raise ValueError('%s: Invalid IPv4 address %r' % (device.name, ip4[0]))
					all_ip4s.add(ip4[0])
			if not device.ip6dynamic:
				for ip6 in device.ip6:
					# check for duplicated IP's
					if ip6[0] in all_ip6s:
						raise ValueError('%s: Duplicated IP address %r' % (device.name, ip6[0]))
					try:
						if ip6[0]:
							# validate IP address
							ipaddr.IPv6Address(ip6[0])
					except ipaddr.AddressValueError:
						raise ValueError('%s: Invalid IPv6 address %r' % (device.name, ip6[0])
					all_ip6s.add(ip6[0])

			if isinstance(device, Bond):
				# at least one interface must exists in a bonding
				if not device.bond_slaves or not device.bond_primary:
					raise ValueError('%s: Missing interface for bond interface' % (device.name))
				for name in set(device.bond_slaves + device.bond_primary):
					# all interfaces must exists
					if name not in self:
						raise ValueError('%s: Missing interface %r' % (device.name, name))

					# all interfaces must be physical
					if name not in self.physical_interfaces:
						raise ValueError('%s: Bond only allows physical interfaces %s' % (device.name, name))

					# all used interfaces in a bonding must be unconfigured
					interface = self[name]
					if interface.ip4 or interface.ip6:
						raise ValueError('%s: Cannot use configured interface %s' % (device.name, name))

			elif isinstance(device, Bridge):
				for name in device.bridge_ports:
					# all interfaces must exists
					if name not in self:
						raise ValueError('%s: Missing interface %r' % (device.name, name))

	def persist(self):
		self.check_consistence()
		ucr.load()
		for device in self.values():
			for key, value in device.to_ucr().iteritems():
				if value is None:
					if key in ucr:
						del ucr[key]
				else:
					ucr[key] = value
		ucr.save()

	@classmethod
	def from_ucr(cls, ucrv=None):
		if ucrv is None:
			ucr.load()
			ucrv = ucr

		names = {}
		# get all available interfaces
		for key in ucrv:
			match = RE_INTERFACE.match(key)
			if match:
				name = match.group(1)
				if name not in names:
					names[name] = Device(name)

		self = cls()
		for device in names.values():
			device.parse_ucr(ucrv)
			if device.options:
				# detect type of interface
				if any(opt.startswith('bridge_ports') for opt in device.options):
					device = Bridge(device.name)
					device.parse_ucr(ucrv)
				elif any(opt.startswith('bond-primary') for opt in device.options):
					device = Bond(device.name)
					device.parse_ucr(ucrv)
			self[device.name] = device

		return self

class Device(object):
	u"""A network interface"""

	@property
	def vlan_id(self):
		u"""If this is a virtual interface return the virtual number otherwise None"""
		if '.' in self.name:
			return int(self.name.split('.')[1])
	
	@property
	def primary_ip4(self):
		if self.ip4:
			return self.ip4[0]
		return (None, None)

	def __init__(self, name=None):
		# the interface name, e.g. wlan0, eth0, br0, eth0.2, bond0
		self.name = name

		# array of IP4 addresses and netmask assigned to this interface
		# e.g. [('1.2.3.4', '255.255.255.0'), ('1.2.3.5', '24')]
		self.ip4 = []

		# array of IPv6 addresses, prefix and identifier
		# e.g. [('::1', '64', 'default'), ('::2', '64', 'foobar')]
		self.ip6 = []

		# flags whether this interface gets its IP addresses via DHCP or SLAAC
		self.ip4dynamic = False
		self.ip6dynamic = False

		# flag indicating that this interface is the primary network interface of the system
		self.primary = False

		# flag indicating that this interface should automatically start at system startup
		self.start = None

		# type of network for this interface e.g. static, manual, dhcp
		self.type = None

		# additional options for this interface
		self.options = []

		# unknown UCR variables
		self._leftover = []

		# TODO: MAC address ?

	def parse_ucr(self, ucrv=None):
		if ucrv is None:
			ucr.load()
			ucrv = ucr
		name = self.name

		vals = {}
		for key in ucrv:
			if re.match(r'^interfaces/%s(?:/|_[0-9]+/)' % re.escape(name), key):
				vals[key] = ucrv[key]

		self.primary = ucrv.get('interfaces/primary') == name

		self.start = ucr.is_true(value=vals.pop('interfaces/%s/start' % (name), None))

		type_ = vals.pop('interfaces/%s/type' % (name), None)
		if type_ is not None:
			self.type = type_

		self.ip4dynamic = 'dhcp' == self.type
		self.ip6dynamic = ucr.is_true(value=vals.pop('interfaces/%s/ipv6/acceptRA' % (name), None))

		self.ip4.append((vals.pop('interfaces/%s/address' % (name), ''), vals.pop('interfaces/%s/netmask' % (name), '')))

		for key in vals.copy():
			if re.match('^interfaces/%s/options/[0-9]+$' % re.escape(name), key):
				self.options.append(vals.pop(key))

			match = re.match('^interfaces/%s/ipv6/([^/]+)/address' % re.escape(name), key)
			if match:
				identifier = match.group(1)
				self.ip6.append((vals.pop(key), vals.pop('interfaces/%s/ipv6/%s/prefix' % (name, identifier), ''), identifier))

			if key in vals:
				self._leftover.append((key, vals.pop(key)))

		self.options.sort()
		self._leftover.sort()

	def to_ucr(self):
		u"""Return a dict of UCR variables to set or unset.
			Values which are None should be unset.
		"""
		ucr.load()
		name = self.name
		vals = {}
		for key in ucr:
			if key.startswith('interfaces/%s/' % (name)):
				vals[key] = None

		for key, val in self._leftover:
			vals[key] = val

		if self.primary:
			vals['interfaces/primary'] = name

		if self.start is not None:
			vals['interfaces/%s/start' % (name)] = str(bool(self.start)).lower()

		if self.type in ('static', 'manual', 'dhcp'): # TODO: support 'dynamic'
			vals['interfaces/%s/type' % (name)] = self.type

		if self.ip4:
			vals['interfaces/%s/address' % (name)] = self.ip4[0][0]
			vals['interfaces/%s/netmask' % (name)] = self.ip4[0][1]

		for i, ip4 in enumerate(self.ip4[1:]):
			vals['interfaces/%s_%s/address' % (name, i)] = ip4[0]
			vals['interfaces/%s_%s/netmask' % (name, i)] = ip4[1]

		for ip6 in self.ip6:
			vals['interfaces/%s/ipv6/%s/address' % (name, ip6[2])] = ip6[0]
			vals['interfaces/%s/ipv6/%s/prefix' % (name, ip6[2])] = ip6[1]

		vals['interfaces/%s/ipv6/acceptRA' % (name)] = str(bool(self.ip6dynamic)).lower()

		for i, option in enumerate(self.options):
			vals['interfaces/%s/options/%d' % (name, i)] = option

		return vals

	def __repr__(self):
		return '<%s %r>' % (self.__class__.__name__, self.name)

	@property
	def __dict__(self):
		d = super(Device, self).__dict__
		d.update(dict(
			interfaceType=self.__class__.__name__,
			vlan_id=self.vlan_id
		))
		return d

class Bond(Device):

	modes = {
		'balance-rr': 0,
		'active-backup': 1,
		'balance-xor': 2,
		'broadcast': 3,
		'802.3ad': 4,
		'balance-tlb': 5,
		'balance-alb': 6
	}

	def __init__(self):
		super(Bond, self).__init__()
		self.miimon = None
		self.bond_primary = []
		self.bond_slaves = []
		self.bond_mode = 0

		# TODO: arp_interval arp_ip_target downdelay lacp_rate max_bonds primary updelay use_carrier xmit_hash_policy 

	def parse_ucr(self):
		super(Bond, self).parse_ucr()
		options = []
		for option in self.options:
			try:
				name, value = option.split(None, 1)
			except ValueError:
				name, value = option, ''

			if name == 'bond-primary':
				self.bond_primary = value.split()
			elif name == 'bond-slaves':
				self.bond_slaves = value.split()
			elif name == 'bond-mode':
				try:
					self.bond_mode = int(value)
				except ValueError:
					try:
						self.bond_mode = self.modes[value.strip()]
					except KeyError:
						pass # invalid mode
			elif name == 'miimon':
				try:
					self.miimon = int(value)
				except ValueError:
					pass
			else:
				options.append(option)

	def to_ucr(self):
		vals = super(Bond, self).to_ucr()
		i = len(self.options)
		vals['interfaces/%s/options/%d' % (self.name, i)] = 'bond-primary %s' % (' '.join(self.bond_primary))
		vals['interfaces/%s/options/%d' % (self.name, i+1)] = 'bond-slaves %s' % (' '.join(self.bond_slaves))
		vals['interfaces/%s/options/%d' % (self.name, i+2)] = 'bond-mode %s' % (self.bond_mode)
		vals['interfaces/%s/options/%d' % (self.name, i+3)] = 'miimon %s' % (self.miimon)
		return vals

class Bridge(Device):
	def __init__(self):
		super(Bridge, self).__init__()
		self.bridge_ports = []
		self.bridge_fd = 0

		# TODO: bridge_ageing bridge_bridgeprio bridge_gcint bridge_hello bridge_hw bridge_maxage bridge_maxwait bridge_pathcost bridge_portprio bridge_stp bridge_waitport

	def parse_ucr(self):
		super(Bridge, self).parse_ucr()
		options = []
		for option in self.options:
			try:
				name, value = option.split(None, 1)
			except ValueError:
				name, value = option, ''

			if name == 'bridge_ports':
				self.bridge_ports = value.split()
			elif name == 'bridge_fd':
				try:
					self.bridge_fd = int(value)
				except ValueError:
					# invalid value
					pass
			else:
				options.append(option)
		self.options = options

	def to_ucr(self):
		vals = super(Bridge, self).to_ucr()
		i = len(self.options)
		vals['interfaces/%s/options/%d' % (self.name, i)] = 'bridge_ports %s' % (' '.join(self.bridge_ports) or 'none')
		vals['interfaces/%s/options/%d' % (self.name, i+1)] = 'bridge_fd %d' % (self.bridge_fd)
		return vals
