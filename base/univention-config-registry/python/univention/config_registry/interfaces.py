#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
"""Handle UCR network configuration."""
#
# Copyright 2010-2019 Univention GmbH
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

# pylint: disable-msg=W0142,C0103,R0201,R0904

from sys import maxsize
import re
from functools import wraps
from backend import ConfigRegistry
import six
if six.PY3:
	from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
else:
	from ipaddr import IPv4Address, IPv4Network, IPv6Address, IPv6Network
try:
	from typing import Any, Callable, Dict, Iterator, Optional, Tuple, Type  # noqa F401
	if six.PY3:
		from ipaddress import IPvddress  # noqa F401
	else:
		from ipaddr import IPAddress  # noqa F401
except ImportError:
	pass

__all__ = ['RE_IFACE', 'forgiving', 'cmp_alnum', 'Interfaces']

_SKIP = set((
	'interfaces/handler',
	'interfaces/primary',
	'interfaces/restart/auto',
))
RE_IFACE = re.compile(r'''^
		(?!(?:%s)$) # _SKIP
		interfaces/ # prefix
		([^/]+)/    # iface name
		(
			(?:ipv6/([0-9A-Za-z]+)/)? # IPv6 name
			.*)        # suffix
		$''' % ('|'.join(_SKIP)), re.VERBOSE)


def forgiving(translation=None):
	# type: (Dict[Type[Exception], Any]) -> Callable[[Callable], Callable]
	"""
	Decorator to translate exceptions into return values.

	:param translation: Mapping from Exception class to return value.
	"""
	if translation is None:
		translation = {}

	def decorator(func):
		# type: (Callable) -> Callable
		"""Wrap function and translate exceptions."""

		@wraps(func)
		def inner(self, *args, **kwargs):
			"""Run function and translate exceptions."""
			try:
				return func(self, *args, **kwargs)
			except Exception as ex:
				best = None
				for cls, _value in translation.items():
					if isinstance(ex, cls):
						if best is None or issubclass(cls, best):
							best = cls
				if best:
					return translation[best]
				raise

		return inner

	return decorator


forgiving_addr = forgiving({ValueError: False, KeyError: None})
"""Decorator to translate errors from IP address parsing to `None` instead of raising an exception."""


def cmp_alnum(value):
	# type: (str) -> Tuple
	"""
	Sort value split by digits / non-digits.

	:param value: The value to sort.
	:returns: value split into tuple.
	"""
	value = str(value)
	key = []
	for num, text in RE_ALNUM.findall(value):
		key.append(int(num or maxsize))
		key.append(text)
	return tuple(key)


RE_ALNUM = re.compile(r'([0-9]+)|([^0-9]+)')


class _Iface(dict):
	"""Single network interface."""

	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.ipv6_names = set()

	@property
	def name(self):
		# type: () -> str
		"""Return interface name."""
		return self['name'].replace('_', ':')

	@property  # type: ignore
	@forgiving({KeyError: maxsize, ValueError: maxsize})
	def order(self):
		# type: () -> int
		"""Return interface order."""
		return int(self['order'])

	@property
	def type(self):
		# type: () -> str
		"""Return interface handler."""
		return self.get('type', '')

	@property
	def start(self):
		# type: () -> bool
		"""Return automatic interface start."""
		return ConfigRegistry().is_true(value=self.get('start', '1'))

	@property  # type: ignore
	@forgiving_addr
	def network(self):
		# type: () -> IPv4Address
		"""Return network address."""
		return IPv4Address('%(network)s' % self)

	@property  # type: ignore
	@forgiving_addr
	def broadcast(self):
		# type: () -> IPv4Address
		"""Return broadcast address."""
		return IPv4Address('%(broadcast)s' % self)

	@forgiving_addr
	def ipv4_address(self):
		# type: () -> IPv4Address
		"""Return IPv4 address."""
		return IPv4Network('%(address)s/%(netmask)s' % self)

	@forgiving_addr
	def ipv6_address(self, name='default'):
		# type: (str) -> IPv6Address
		"""Return IPv6 address."""
		key = '%%(ipv6/%s/address)s/%%(ipv6/%s/prefix)s' % (name, name)
		return IPv6Network(key % self)

	@property
	def routes(self):
		# type: () -> Iterator[str]
		"""Return interface routes."""
		for k, v in sorted(self.items()):
			if not k.startswith('route/'):
				continue
			if v.startswith('host ') or v.startswith('net '):
				yield v

	@property
	def options(self):
		# type: () -> Iterator[str]
		"""Return interface options."""
		for k, v in sorted(self.items()):
			if not k.startswith('options/'):
				continue
			yield v


class VengefulConfigRegistry(ConfigRegistry):
	"""
	Instance wrapper for Config Registry throwing exceptions.

	:param base_object: UCR instance.

	<https://forge.univention.org/bugzilla/show_bug.cgi?id=28276>
	<http://stackoverflow.com/questions/1443129/>
	"""

	def __init__(self, base_object):
		self.__class__ = type(base_object.__class__.__name__, (self.__class__, base_object.__class__), {})
		self.__dict__ = base_object.__dict__

	def __getitem__(self, key):
		# type: (str) -> str
		"""
		Return registry value.

		Compared with :py:meth:`ConfigRegistry.__getitem__` this raises an exception instead of returning `None`.

		:param key: UCR variable name.
		:returns: the value.
		:raises: KeyError when the value is not found.
		"""
		for reg in ConfigRegistry.LAYER_PRIORITIES:
			try:
				registry = self._registry[reg]
				value = registry[key]
				return value
			except KeyError:
				continue
		raise KeyError(key)


class Interfaces(object):
	"""
	Handle network interfaces configured by UCR.

	:param ucr: UCR instance.
	"""

	def __init__(self, ucr=None):
		# type: (ConfigRegistry) -> None
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if isinstance(ucr, ConfigRegistry):
			ucr = VengefulConfigRegistry(ucr)

		self.handler = ucr.get('interfaces/handler', 'ifplugd')
		self.primary = ucr.get('interfaces/primary', 'eth0')
		try:
			self.ipv4_gateway = IPv4Address(ucr['gateway'])
		except KeyError:
			self.ipv4_gateway = None
		except ValueError:
			self.ipv4_gateway = False
		try:
			# <https://tools.ietf.org/html/rfc4007#section-11>
			# As a common notation to specify the scope zone, an
			# implementation SHOULD support the following format:
			# <address>%<zone_id>
			gateway, zone_index = (ucr['ipv6/gateway'].rsplit('%', 1) + [None])[:2]
			self.ipv6_gateway = IPv6Address(gateway)
			self.ipv6_gateway_zone_index = zone_index
		except KeyError:
			self.ipv6_gateway = None
			self.ipv6_gateway_zone_index = None
		except ValueError:
			self.ipv6_gateway = False
			self.ipv6_gateway_zone_index = None

		self._all_interfaces = {}  # type: Dict[str, _Iface]
		for key, value in ucr.items():
			if not value:
				continue
			match = RE_IFACE.match(key)
			if not match:
				continue
			iface, subkey, ipv6_name = match.groups()
			data = self._all_interfaces.setdefault(iface, _Iface(name=iface))
			data[subkey] = value
			if ipv6_name:
				data.ipv6_names.add(ipv6_name)

	def _cmp_order(self, iface):
		# type: (_Iface) -> Tuple[Tuple, Tuple]
		"""
		Compare interfaces by order.

		:param iface: Other interface.
		:returns: A tuple to be used as a key for sorting.
		"""
		return (
			cmp_alnum(iface.order),
			cmp_alnum(iface.name),
		)

	def _cmp_primary(self, iface):
		# type: (_Iface) -> Tuple[int, Tuple, Tuple]
		"""
		Compare interfaces by primary.

		:param iface: Other interface.
		:returns: 3-tuple to be used as a key for sorting.
		"""
		try:
			primary = self.primary.index(iface.name)
		except ValueError:
			primary = maxsize
		return (
			primary,
			cmp_alnum(iface.order),
			cmp_alnum(iface.name),
		)

	def _cmp_name(self, iname):
		# type: (str) -> Optional[str]
		"""
		Compare IPv6 sub-interfaces by name.

		:param name: Interface name.
		:returns: string used as a key for sorting.
		"""
		return None if iname == 'default' else iname

	@property
	def all_interfaces(self):
		# type: () -> Iterator[Tuple[str, _Iface]]
		"""Yield IPv4 interfaces."""
		for name_settings in sorted(self._all_interfaces.items(), key=lambda name_iface: self._cmp_order(name_iface[1])):
			yield name_settings

	@property
	def ipv4_interfaces(self):
		# type: () -> Iterator[Tuple[str, _Iface]]
		"""Yield IPv4 interfaces."""
		for name, iface in sorted(self._all_interfaces.items(), key=lambda _name_iface: self._cmp_order(_name_iface[1])):
			if iface.ipv4_address() is not None:
				yield (name, iface)

	@property
	def ipv6_interfaces(self):
		# type: () -> Iterator[Tuple[_Iface, str]]
		"""Yield names of IPv6 interfaces."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_order):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				if iface.ipv6_address(name):
					yield (iface, name)

	def get_default_ip_address(self):
		# type: () -> Optional[IPAddress]
		"""returns the default IP address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

		return None

	def get_default_ipv4_address(self):
		# type: () -> Optional[IPv4Address]
		"""returns the default IPv4 address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr

		return None

	def get_default_ipv6_address(self):
		# type: () -> Optional[IPv6Address]
		"""returns the default IPv6 address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

		return None


if __name__ == '__main__':
	import unittest

	class Test_Iface(unittest.TestCase):

		"""Test implementation."""

		def test_basic(self):
			"""Test basic functions."""
			i = _Iface({
				'name': 'NAME',
				'order': 42,
				'type': 'static',
				'start': 'yes',
				'address': '1.2.3.4',
				'netmask': '255.255.255.0',
				'network': '1.2.3.0',
				'broadcast': '1.2.3.255',
				'options/2': '2',
				'options/1': '1',
				'route/3': 'foo',
				'route/2': 'host 192.168.0.240',
				'route/1': 'net 192.168.0.0 netmask 255.255.255.128',
			})
			self.assertEqual('NAME', i.name)
			self.assertEqual(42, i.order)
			self.assertEqual('static', i.type)
			self.assertEqual(True, i.start)
			self.assertEqual(IPv4Address('1.2.3.0'), i.network)
			self.assertEqual(IPv4Address('1.2.3.255'), i.broadcast)
			self.assertEqual(IPv4Network('1.2.3.4/24'), i.ipv4_address())
			self.assertEqual(None, i.ipv6_address())
			self.assertEqual(['1', '2'], list(i.options))
			self.assertEqual(['net 192.168.0.0 netmask 255.255.255.128', 'host 192.168.0.240'], list(i.routes))

		def test_incomplete_addr(self):
			"""Test incomplete interface with address."""
			i = _Iface({
				'address': '2.3.4.5',
				'ipv6/default/address': '1:2:3:4:5:6:7:8',
			})
			self.assertEqual(None, i.ipv4_address())
			self.assertEqual(None, i.ipv6_address())

		def test_incomplete_net(self):
			"""Test incomplete interface with netmask/prefix."""
			i = _Iface({
				'netmask': '255.255.255.0',
				'ipv6/default/prefix': '64',
			})
			self.assertEqual(None, i.ipv4_address())
			self.assertEqual(None, i.ipv6_address())

		def test_invalid(self):
			"""Test invalid interface address."""
			i = _Iface({
				'address': '2.3.4.5',
				'netmask': '42',
				'ipv6/default/address': '1:2:3:4:5:6:7:8',
				'ipv6/default/prefix': '4711',
			})
			self.assertEqual(False, i.ipv4_address())
			self.assertEqual(False, i.ipv6_address())

		def test_ipv6(self):
			"""Test IPv6 functions."""
			i = _Iface({
				'name': 'NAME',
				'ipv6/default/address': '1:2:3:4:5:6:7:8',
				'ipv6/default/prefix': '64',
				'ipv6/other/address': '2:3:4:5:6:7:8:9',
				'ipv6/other/prefix': '80',
			})
			self.assertEqual('NAME', i.name)
			self.assertEqual(None, i.ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), i.ipv6_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), i.ipv6_address('default'))
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/80'), i.ipv6_address('other'))

	class TestInterfaces(unittest.TestCase):

		"""Test implementation."""

		def test_empty(self):
			"""Test no interface."""
			t = Interfaces(ucr={
			})
			self.assertEqual('ifplugd', t.handler)
			self.assertEqual('eth0', t.primary)
			self.assertEqual(None, t.ipv4_gateway)
			self.assertEqual(None, t.ipv6_gateway)
			self.assertEqual(None, t.ipv6_gateway_zone_index)
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None, t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_ipv4_only(self):
			"""Test IPv4 only interface."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '1.2.3.4',
				'interfaces/eth0/netmask': '255.255.255.0',
			})
			self.assertEqual(['eth0'], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_incomplete_addr(self):
			"""Test incomplete interface with address."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
			})
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None, t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_incomplete_net(self):
			"""Test incomplete interface with netmask/prefix."""
			t = Interfaces(ucr={
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth0/ipv6/default/prefix': '64',
			})
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None, t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_ipv4_multi(self):
			"""Test multiple IPv4 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '1.2.3.4',
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth1/address': '2.3.4.5',
				'interfaces/eth1/netmask': '255.255.255.0',
			})
			self.assertEqual(['eth0', 'eth1'], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_ipv6_multi(self):
			"""Test multiple IPv6 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/default/prefix': '64',
				'interfaces/eth1/ipv6/default/address': '2:3:4:5:6:7:8:9',
				'interfaces/eth1/ipv6/default/prefix': '64',
			})
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth0', 'eth1'], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ipv6_address())

		def test_dual(self):
			"""Test dual stack interface."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/default/prefix': '64',
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/netmask': '255.255.255.0',
			})
			self.assertEqual(['eth0'], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth0'], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('2.3.4.5/24'), t.get_default_ip_address())
			self.assertEqual(IPv4Network('2.3.4.5/24'), t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ipv6_address())

		def test_ipv6_disjunct(self):
			"""Test disjunct IPv4 IPv6 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth1/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth1/ipv6/default/prefix': '64',
			})
			self.assertEqual(['eth0'], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth1'], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('2.3.4.5/24'), t.get_default_ip_address())
			self.assertEqual(IPv4Network('2.3.4.5/24'), t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ipv6_address())

		def test_ipv4_order(self):
			"""Test IPv4 ordering."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '1.2.3.4',
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth1/address': '2.3.4.5',
				'interfaces/eth1/netmask': '255.255.0.0',
				'interfaces/eth2/order': '1',
				'interfaces/eth2/address': '3.4.5.6',
				'interfaces/eth2/netmask': '255.0.0.0',
			})
			self.assertEqual(['eth2', 'eth0', 'eth1'], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'), t.get_default_ipv4_address())
			self.assertEqual(None, t.get_default_ipv6_address())

		def test_ipv6_order(self):
			"""Test IPv6 ordering."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/default/prefix': '64',
				'interfaces/eth1/ipv6/default/address': '2:3:4:5:6:7:8:9',
				'interfaces/eth1/ipv6/default/prefix': '72',
				'interfaces/eth2/order': '1',
				'interfaces/eth2/ipv6/default/address': '3:4:5:6:7:8:9:a',
				'interfaces/eth2/ipv6/default/prefix': '80',
			})
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth2', 'eth0', 'eth1'], [s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'), t.get_default_ipv6_address())

		def test_ipv6_order_multi(self):
			"""Test multiple IPv6 ordering."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/foo/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/foo/prefix': '64',
				'interfaces/eth1/order': '2',
				'interfaces/eth1/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth1/ipv6/default/prefix': '64',
				'interfaces/eth1/ipv6/a/address': '2:3:4:5:6:7:8:9',
				'interfaces/eth1/ipv6/a/prefix': '72',
				'interfaces/eth2/order': '1',
				'interfaces/eth2/ipv6/z/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth2/ipv6/z/prefix': '64',
				'interfaces/eth2/ipv6/default/address': '2:3:4:5:6:7:8:9',
				'interfaces/eth2/ipv6/default/prefix': '72',
				'interfaces/primary': 'eth2,eth1',
			})
			self.assertEqual([], [s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([
				('eth2', 'default'),
				('eth2', 'z'),
				('eth1', 'default'),
				('eth1', 'a'),
				('eth0', 'foo')],
				[(s.name, n) for s, n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/72'), t.get_default_ip_address())
			self.assertEqual(None, t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/72'), t.get_default_ipv6_address())

		def test_order_mixed(self):
			"""Test multiple IPv6 ordering."""
			t = Interfaces(ucr={
				'interfaces/br0/order': 'br0',
				'interfaces/br1/order': '1',
			})
			self.assertEqual(['br1', 'br0'], [n for n, _s in t.all_interfaces])

		def test_basis(self):
			"""Test basic configuration."""
			t = Interfaces(ucr={
				'gateway': '1.2.3.4',
				'ipv6/gateway': '1:2:3:4:5:6:7:8',
				'interfaces/handler': 'manual',
				'interfaces/primary': 'br0',
			})
			self.assertEqual('manual', t.handler)
			self.assertEqual('br0', t.primary)
			self.assertEqual(IPv4Address('1.2.3.4'), t.ipv4_gateway)
			self.assertEqual(IPv6Address('1:2:3:4:5:6:7:8'), t.ipv6_gateway)
			self.assertEqual(None, t.ipv6_gateway_zone_index)

		def test_v6llgw(self):
			"""Test IPv6 link-local gateway."""
			t = Interfaces(ucr={
				'ipv6/gateway': 'fe80::1%eth0',
			})
			self.assertEqual(IPv6Address('fe80::1'), t.ipv6_gateway)
			self.assertEqual('eth0', t.ipv6_gateway_zone_index)

		def test_non_vengeful(self):
			"""Test ConfigRegistry not raining KeyError."""
			try:
				Interfaces(None)
			except AttributeError:
				self.fail('Failed to create Interfaces(None)')

	class TestDecorator(unittest.TestCase):

		"""Test forgiving decorator."""
		@forgiving()
		def value_through(self):
			"""Value through"""
			return 42

		def test_value_through(self):
			"""Test pass through decorator."""
			self.assertEqual('value_through', self.value_through.__name__)
			self.assertEqual('Value through', self.value_through.__doc__)
			self.assertEqual(42, self.value_through())

		@forgiving()
		def error_through(self):
			"""Error through"""
			raise KeyError(42)

		def test_error_through(self):
			"""Test exception decorator."""
			self.assertEqual('error_through', self.error_through.__name__)
			self.assertEqual('Error through', self.error_through.__doc__)
			self.assertRaises(KeyError, self.error_through)

		@forgiving({KeyError: 42})
		def error_translate(self):
			"""Error translate"""
			raise KeyError(42)

		def test_error_translate(self):
			"""Test translation decorator."""
			self.assertEqual('error_translate', self.error_translate.__name__)
			self.assertEqual('Error translate', self.error_translate.__doc__)
			self.assertEqual(42, self.error_translate())

		@forgiving({LookupError: 42})
		def error_super(self):
			"""Error super"""
			raise KeyError(42)

		def test_error_super(self):
			"""Test translation super-class decorator."""
			self.assertEqual('error_super', self.error_super.__name__)
			self.assertEqual('Error super', self.error_super.__doc__)
			self.assertEqual(42, self.error_super())

		@forgiving({LookupError: 0, KeyError: 42})
		def error_multi(self):
			"""Error multi"""
			raise KeyError(42)

		def test_error_multi(self):
			"""Test translation multi-class decorator."""
			self.assertEqual('error_multi', self.error_multi.__name__)
			self.assertEqual('Error multi', self.error_multi.__doc__)
			self.assertEqual(42, self.error_multi())

	class TestSort(unittest.TestCase):

		"""Rest alphanumeric sorting."""

		def test_all_num(self):
			"""Test all plain numeric."""
			data = [0, 1]
			self.assertEqual(data, sorted(data, key=cmp_alnum))

		def test_all_num_str(self):
			"""Test all string numeric."""
			data = ['0', '1']
			self.assertEqual(data, sorted(data, key=cmp_alnum))

		def test_all_str(self):
			"""Test all string."""
			data = ['a', 'b']
			self.assertEqual(data, sorted(data, key=cmp_alnum))

		def test_str_num_str(self):
			"""Test all string numeric."""
			data = ['0', 'b']
			self.assertEqual(data, sorted(data, key=cmp_alnum))

		def test_num_str(self):
			"""Test all string numeric."""
			data = [0, 'b']
			self.assertEqual(data, sorted(data, key=cmp_alnum))

		def test_mixed(self):
			"""Test mixed strings."""
			data = ['eth2', 'eth10']
			self.assertEqual(data, sorted(data, key=cmp_alnum))

	unittest.main()

# vim:set sw=4 ts=4 noet:
