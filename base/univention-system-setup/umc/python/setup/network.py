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
from functools import reduce

import ipaddr

from univention.lib.i18n import Translation
from univention.config_registry import ConfigRegistry

ucr = ConfigRegistry()
ucr.load()

_ = Translation('univention-management-console-module-setup').translate

RE_INTERFACE = re.compile(r'^interfaces/([^/_]+)(_[^/]+)?/')
RE_IPV6_ID = re.compile(r'^[a-zA-Z0-9]+\z')

class DeviceError(ValueError):
	def __init__(self, msg, device=None):
		if device is not None:
			msg = '%s: %s' % (device, msg)
		self.device = device
		ValueError.__init__(self, msg)

class IP4Set(set):
	def add(self, ip):
		set.add(self, ipaddr.IPv4Address(ip))
	def __contains__(self, ip):
		return set.__contains__(self, ipaddr.IPv4Address(ip))

class IP6Set(set):
	def add(self, ip):
		set.add(self, ipaddr.IPv6Address(ip))
	def __contains__(self, ip):
		return set.__contains__(self, ipaddr.IPv6Address(ip))

class Interfaces(dict):
	""""""

	def __init__(self, *args, **kwargs):
		super(Interfaces, self).__init__(*args, **kwargs)

	def check_consistency(self):
		"""checks and partly enforces the consistency of all network interfaces"""

		devices_in_use = {}
		all_ip4s, all_ip6s = IP4Set(), IP6Set()
		for device in self.values():
			# validate IP addresses, netmasks, etc.
			device.validate()

			device.order = None
			device.start = True

			if isinstance(device, (Bridge, Bond)):
				if isinstance(device, Bond):
					subdevs = set([self[name] for name in device.bond_slaves if name in self])
				else:
					subdevs = set([self[name] for name in device.bridge_ports if name in self])

				for idevice in subdevs:
					# make sure that used interfaces does not have any IPv4 or IPv6 address
					idevice.ip4 = []
					idevice.ip6 = []
					idevice.ip4dynamic = False
					idevice.ip6dynamic = False

					idevice.type = 'manual'

					# make sure that used interfaces can not be used by other interfaces, too
					if idevice.name in devices_in_use:
						raise DeviceError(_('Device %r is already in use by %r') % (idevice.name, devices_in_use[idevice.name])), device.name)
					devices_in_use[idevice.name] = device.name

			if not device.ip4dynamic:
				for address, netmask in device.ip4:
					# check for duplicated IP's
					if address in all_ip4s:
						raise DeviceError(_('Duplicated IP address %r') % (address), device.name)
					all_ip4s.add(address)

			if not device.ip6dynamic:
				for address, prefix, identifier in device.ip6:
					# check for duplicated IP's
					if address in all_ip6s:
						raise DeviceError(_('Duplicated IP address %r') % (address), device.name)
					all_ip6s.add(address)

			if isinstance(device, Bond):
				# at least one interface must exists in a bonding
				if not device.bond_slaves or not device.bond_primary:
					raise DeviceError(_('Missing interface for bond interface'), device.name)

				for name in set(device.bond_slaves + device.bond_primary):
					# no self dependencies
					if name == device.name:
						raise DeviceError(_('Self-dependency not allowed'), name)

					# all interfaces must exists
					if name not in self:
						raise DeviceError(_('Missing interface %r') % (name), device.name)

					# all interfaces must be physical
					if not isinstance(self[name], Ethernet):
						raise DeviceError(_('Interfaces used in a bonding must be physical: %s is not') % (name), device.name)

					# all used interfaces in a bonding must be unconfigured
					interface = self[name]
					if interface.ip4 or interface.ip6:
						raise DeviceError(_('Cannot use configured interface %s') % (name), device.name)

				# all bond-primaries must exists as bond-slaves
				if not set(device.bond_primary).issubset(set(device.bond_slaves)):
					raise DeviceError('')

			elif isinstance(device, Bridge):
				for name in device.bridge_ports:
					# no self dependencies
					if name == device.name:
						raise DeviceError(_('Self-dependency not allowed'), name)

					# all interfaces must exists
					if name not in self:
						raise DeviceError(_('Missing interface %r') % (name), device.name)

					# interface can't be a Bridge
					if isinstance(self[name], Bridge):
						raise DeviceError(_('Interface cannot use Bridge %r as bridge-port') % (name), device.name)

			elif isinstance(device, VLAN):
				# parent interface must exists
				if device.parent_device not in self:
					raise DeviceError(_('Missing interface %r') % (name), device.name)

				if isinstance(self[device.parent_device], VLAN):
					# unsupported
					raise DeviceError('', device.name)

		# make sure at least one interface is configured with an IPv4 or IPv6 address
		if not self or not any(device.ip4 or device.ip6 for device in self.values()):
			raise DeviceError(_('There is no interface configured.'))

		if not any(isinstance(device, (VLAN, Bridge, Bond)) for device in self.values()):
			# no VLAN, Bridge or Bond devices
			# we don't need to set the device order
			return
			
		devices = {}
		for device in self.values():
			if isinstance(device, Bridge):
				devices[device] = set([self[name] for name in device.bridge_ports])
			elif isinstance(device, Bond):
				devices[device] = set([self[name] for name in device.bond_slaves])
			elif isinstance(device, VLAN):
				devices[device] = set([self[device.parent_device]])
			else:
				devices[device] = set()

		i = 1
		while True:
			stack = set(device for device, subdevs in devices.iteritems() if not subdevs)
			if not stack:
				if devices:
					# cyclic dependency
					raise DeviceError("Cyclic dependency detected: %s" % '; '.join('%s -> %s' % (dev, ', '.join([s.name for s in sd])) for dev, sd in devices.iteritems()))
				break
			for device in stack:
				# set device order
				device.order = i
				i += 1
			devices = dict((device, (subdevs - stack)) for device, subdevs in devices.iteritems() if device not in stack)

	def persist(self):
		self.check_consistency()
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
	def from_ucr(cls, ucrv=ucr):
		ucr.load()

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

	def __new__(cls, *args, **kwargs):
		# make it abstract ;)
		if cls is Device and args:
			device = Ethernet(*args, **kwargs)
			device.parse_ucr()
			# detect type of interface
			cls = Ethernet
			if device.options:
				if any(opt.startswith('bridge_ports') for opt in device.options):
					cls = Bridge
				elif any(opt.startswith('bond-primary') for opt in device.options):
					cls = Bond
		return object.__new__(cls, *args, **kwargs)

	@property
	def primary_ip4(self):
		if self.ip4:
			return self.ip4[0]
		return (None, None)

	def __init__(self, name):
		# the interface name, e.g. wlan0, eth0, br0, eth0.2, bond0
		self.name = name

		# set initial values
		self.clear()

	def clear(self):
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

		# 
		self.order = None

		# additional options for this interface
		self.options = []

		# unknown UCR variables
		self._leftover = []

		# TODO: MAC address ?

	def validate(self):
		# validate IPv4
		if not self.ip4dynamic:
			for address, netmask in self.ip4:
				# validate IP address
				try:
					iaddress = int(ipaddr.IPv4Address(address))
				except (ValueError, ipaddr.AddressValueError):
					raise DeviceError(_('Invalid IPv4 address %r') % (address), self.name)

				# validate netmask
				try:
					ipaddr.IPv4Network('%s/%s' % (address, netmask))
				except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
					raise DeviceError(_('Invalid IPv4 netmask %r') % (netmask), self.name)

		# validate IPv6
		if not self.ip6dynamic:
			for address, prefix, identifier in self.ip6:
				# validate IP address
				try:
					iaddress = int(ipaddr.IPv6Address(address))
				except ipaddr.AddressValueError:
					raise DeviceError(_('Invalid IPv6 address %r') % (address), self.name)

				# validate IPv6 netmask
				try:
					ipaddr.IPv6Network('%s/%s' % (address, netmask))
				except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
					raise DeviceError(_('Invalid IPv6 netmask %r') % (netmask), self.name)

				# validate IPv6 identifier
				if not RE_IPV6_ID.match(identifier):
					raise DeviceError(_('Invalid IPv6 identifier %r') % (identifier), self.name)

			# There must be a 'default' identifier
			if self.ip6 and not any(identifier == 'default' for address, prefix, identifier in self.ip6):
				raise DeviceError(_('Missing IPv6 default identifier'), self.name)

	def parse_ucr(self, ucrv=ucr):
		name = self.name
		ucr.load()
		self.clear()

		pattern = re.compile(r'^interfaces/%s(?:_[0-9]+)?/' % re.escape(name))
		vals = dict((key, ucrv[key]) for key in ucrv if pattern.match(key))

		self.primary = ucrv.get('interfaces/primary') == name

		self.start = ucr.is_true(value=vals.pop('interfaces/%s/start' % (name), None))

		type_ = vals.pop('interfaces/%s/type' % (name), None)
		if type_ is not None:
			self.type = type_

		order = vals.pop('interfaces/%s/order' % (name), "")
		if order.isdigit():
			self.order = int(order)

		self.ip4dynamic = 'dhcp' == self.type
		self.ip6dynamic = ucr.is_true(value=vals.pop('interfaces/%s/ipv6/acceptRA' % (name), None))

		address, netmask = vals.pop('interfaces/%s/address' % (name), ''), vals.pop('interfaces/%s/netmask' % (name), '24')
		if address:
			self.ip4.append((address, netmask))

		for key in vals.copy():
			if re.match('^interfaces/%s/options/[0-9]+$' % re.escape(name), key):
				self.options.append(vals.pop(key))
				continue

			match = re.match('^interfaces/%s/ipv6/([^/]+)/address' % re.escape(name), key)
			if match:
				identifier = match.group(1)
				self.ip6.append((vals.pop(key), vals.pop('interfaces/%s/ipv6/%s/prefix' % (name, identifier), ''), identifier))
				continue

			match = re.match('^interfaces/(%s_[0-9]+)/address' % re.escape(name), key)
			if match:
				self.ip4.append((vals.pop(key), vals.pop('interfaces/%s/netmask' % match.group(), '24')))
				continue

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

		pattern = re.compile('^interfaces/%s(?:_[0-9]+)?/.*' % re.escape(name))
		vals = dict((key, None) for key in ucr if pattern.match(key))

		for key, val in self._leftover:
			vals[key] = val

		if self.primary:
			vals['interfaces/primary'] = name

		if self.start is not None:
			vals['interfaces/%s/start' % (name)] = str(bool(self.start)).lower()

		if self.type in ('static', 'manual', 'dhcp'):
			vals['interfaces/%s/type' % (name)] = self.type

		if isinstance(self.order, int):
			vals['interfaces/%s/order' % (name)] = str(self.order)

		if not self.ip4dynamic:
			if self.ip4:
				address, netmask = self.ip4[0]
				vals['interfaces/%s/address' % (name)] = address
				vals['interfaces/%s/netmask' % (name)] = netmask

			for i, (address, netmask) in enumerate(self.ip4[1:]):
				vals['interfaces/%s_%s/address' % (name, i)] = address
				vals['interfaces/%s_%s/netmask' % (name, i)] = netmask

		if not self.ip6dynamic:
			for address, prefix, identifier in self.ip6:
				vals['interfaces/%s/ipv6/%s/address' % (name, identifier)] = address
				vals['interfaces/%s/ipv6/%s/prefix' % (name, identifier)] = prefix

		vals['interfaces/%s/ipv6/acceptRA' % (name)] = str(bool(self.ip6dynamic)).lower()

		for i, option in enumerate(self.options):
			vals['interfaces/%s/options/%d' % (name, i)] = option

		return vals

	def __repr__(self):
		return '<%s %r>' % (self.__class__.__name__, self.name)

	def __str__(self):
		return str(self.name)

	def __hash__(self):
		return hash(self.name)

	@property
	def dict(self):
		d = dict(self.__dict__)
		d.update(dict(
			interfaceType=self.__class__.__name__,
		))
		return d

	@staticmethod
	def from_dict(device):
		DeviceType = {
			'Ethernet': Ethernet,
			'VLAN': VLAN,
			'Bridge': Bridge,
			'Bond': Bond
		}[device['interfaceType']]
		interface = DeviceType(device['name'])
		interface.parse_ucr()
		interface.__dict__.update(dict((k, device[k]) for k in set(interface.dict.keys()) if k in device))
		return interface

class Ethernet(Device):
	pass

class VLAN(Device):
	@property
	def vlan_id(self):
		if '.' in self.name:
			return int(self.name.rsplit('.', 1)[1])

	@vlan_id.setter
	def vlan_id(self, vlan_id):
		self.name = '%s.%d' % (self.parent_device, vlan_id)

	@property
	def parent_device(self):
		return self.name.rsplit('.', 1)[0]

	@parent_device.setter
	def parent_device(self, parent_device):
		self.name = '%s.%d' % (parent_device, self.vlan_id)

	def validate(self):
		super(VLAN, self).validate()
		if len(self.ip4) > 1:
			# UCR can't support multiple IPv4 addresses on VLAN, Bridge and Bond interfaces; Bug #31767
			raise DeviceError(_('Multiple IPv4 addresses are not supported on this interface.'), self.name)

	@property
	def dict(self):
		d = super(VLAN, self).dict
		d.update(dict(
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
	modes_r = dict(v,k for k,v in modes.iteritems())

	def clear(self):
		super(Bond, self).clear()
		self.miimon = None
		self.bond_primary = []
		self.bond_slaves = []
		self.bond_mode = 0

		# TODO: arp_interval arp_ip_target downdelay lacp_rate max_bonds primary updelay use_carrier xmit_hash_policy 

	def validate(self):
		super(Bond, self).validate()
		if len(self.ip4) > 1:
			# UCR can't support multiple IPv4 addresses on VLAN, Bridge and Bond interfaces; Bug #31767
			raise DeviceError(_('Multiple IPv4 addresses are not supported on this interface.'), self.name)

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
		if self.miimon is not None:
			vals['interfaces/%s/options/%d' % (self.name, i+3)] = 'miimon %s' % (self.miimon)
		return vals

class Bridge(Device):
	def clear(self):
		super(Bridge, self).clear()
		self.bridge_ports = []
		self.bridge_fd = 0

		# TODO: bridge_ageing bridge_bridgeprio bridge_gcint bridge_hello bridge_hw bridge_maxage bridge_maxwait bridge_pathcost bridge_portprio bridge_stp bridge_waitport

	def validate(self):
		super(Bridge, self).validate()
		if len(self.ip4) > 1:
			# UCR can't support multiple IPv4 addresses on VLAN, Bridge and Bond interfaces; Bug #31767
			raise DeviceError(_('Multiple IPv4 addresses are not supported on this interface.'), self.name)

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
