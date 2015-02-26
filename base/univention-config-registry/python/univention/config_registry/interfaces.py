#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
"""Handle UCR network configuration."""
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

# pylint: disable-msg=W0142,C0103,R0201,R0904

from backend import ConfigRegistry
from ipaddr import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from sys import maxint
import re

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
	"""Decorator to translate exceptions into return values."""
	if translation is None:
		translation = {}

	def decorator(func):
		"""Wrap function and translate exceptions."""
		def inner(self, *args, **kwargs):
			"""Run function and translate exceptions."""
			try:
				return func(self, *args, **kwargs)
			except Exception, ex:
				best = None
				for cls, _value in translation.items():
					if isinstance(ex, cls):
						if best is None or issubclass(cls, best):
							best = cls
				if best:
					return translation[best]
				raise
		inner.__name__ = func.__name__  # pylint: disable-msg=W0621,W0622
		inner.__doc__ = func.__doc__  # pylint: disable-msg=W0621,W0622
		inner.__dict__.update(func.__dict__)
		return inner

	return decorator


forgiving_addr = forgiving({ValueError: False, KeyError: None})


def cmp_alnum(value):
	"""Sort value split by digits / non-digits."""
	value = str(value)
	key = []
	for num, text in cmp_alnum.RE.findall(value):  # pylint: disable-msg=E1101
		key.append(int(num or maxint))
		key.append(text)
	return tuple(key)
cmp_alnum.RE = re.compile(r'([0-9]+)|([^0-9]+)')  # pylint: disable-msg=W0612


class _Iface(dict):
	"""Single network interface."""
	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.ipv6_names = set()

	@property
	def name(self):
		"""Return interface name."""
		return self['name'].replace('_', ':')

	@property
	@forgiving({KeyError: maxint, ValueError: maxint})
	def order(self):
		"""Return interface order."""
		return int(self['order'])

	@property
	def type(self):
		"""Return interface handler."""
		return self.get('type', '')

	@property
	def start(self):
		"""Return automatic interface start."""
		return ConfigRegistry().is_true(value=self.get('start', '1'))

	@property
	@forgiving_addr
	def network(self):
		"""Return network address."""
		return IPv4Address('%(network)s' % self)

	@property
	@forgiving_addr
	def broadcast(self):
		"""Return broadcast address."""
		return IPv4Address('%(broadcast)s' % self)

	@forgiving_addr
	def ipv4_address(self):
		"""Return IPv4 address."""
		return IPv4Network('%(address)s/%(netmask)s' % self)

	@forgiving_addr
	def ipv6_address(self, name='default'):
		"""Return IPv6 address."""
		key = '%%(ipv6/%s/address)s/%%(ipv6/%s/prefix)s' % (name, name)
		return IPv6Network(key % self)

	@property
	def routes(self):
		"""Return interface routes."""
		for k, v in sorted(self.items()):
			if not k.startswith('route/'):
				continue
			if v.startswith('host ') or v.startswith('net '):
				yield v

	@property
	def options(self):
		"""Return interface options."""
		for k, v in sorted(self.items()):
			if not k.startswith('options/'):
				continue
			yield v


class VengefulConfigRegistry(ConfigRegistry):
	"""Instance wrapper for Config Registry throwing exceptions.

	<https://forge.univention.org/bugzilla/show_bug.cgi?id=28276>
	<http://stackoverflow.com/questions/1443129/>
	"""
	def __init__(self, base_object):
		self.__class__ = type(base_object.__class__.__name__,
				(self.__class__, base_object.__class__),
				{})
		self.__dict__ = base_object.__dict__

	def __getitem__(self, key):
		"""Return registry value."""
		for reg in (ConfigRegistry.FORCED,
				ConfigRegistry.SCHEDULE,
				ConfigRegistry.LDAP,
				ConfigRegistry.NORMAL,
				ConfigRegistry.CUSTOM):
			try:
				registry = self._registry[reg]
				# BUG: _ConfigRegistry[key] does not raise a KeyError for unset
				# keys, but returns ''
				if key not in registry:
					raise KeyError(key)
				value = registry[key]
				return value
			except KeyError:
				continue
		raise KeyError(key)


class Interfaces(object):
	"""Handle network interfaces configured by UCR."""

	def __init__(self, ucr=None):
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		elif isinstance(ucr, ConfigRegistry):
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
			self.ipv6_gateway = IPv6Address(ucr['ipv6/gateway'])
		except KeyError:
			self.ipv6_gateway = None
		except ValueError:
			self.ipv6_gateway = False

		self._all_interfaces = {}
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
		"""Compare interfaces by order."""
		return (cmp_alnum(iface.order),
				cmp_alnum(iface.name))

	def _cmp_primary(self, iface):
		"""Compare interfaces by primary."""
		try:
			primary = self.primary.index(iface.name)
		except ValueError:
			primary = maxint
		return (primary,
				cmp_alnum(iface.order),
				cmp_alnum(iface.name),
				)

	def _cmp_name(self, iname):
		"""Compare IPv6 sub-interfaces by name."""
		return None if iname == 'default' else iname

	@property
	def all_interfaces(self):
		"""Yield IPv4 interfaces."""
		for name_settings in sorted(self._all_interfaces.items(),
				key=lambda (name, iface): self._cmp_order(iface)):
			yield name_settings

	@property
	def ipv4_interfaces(self):
		"""Yield IPv4 interfaces."""
		for name, iface in sorted(self._all_interfaces.items(),
				key=lambda (_name, iface): self._cmp_order(iface)):
			if iface.ipv4_address() is not None:
				yield (name, iface)

	@property
	def ipv6_interfaces(self):
		"""Yield names of IPv6 interfaces."""
		for iface in sorted(self._all_interfaces.values(),
				key=self._cmp_order):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				if iface.ipv6_address(name):
					yield (iface, name)

	def get_default_ip_address(self):
		"""returns the default IP address."""
		for iface in sorted(self._all_interfaces.values(),
				key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

	def get_default_ipv4_address(self):
		"""returns the default IPv4 address."""
		for iface in sorted(self._all_interfaces.values(),
				key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr

	def get_default_ipv6_address(self):
		"""returns the default IPv6 address."""
		for iface in sorted(self._all_interfaces.values(),
				key=self._cmp_primary):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

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
			self.assertEqual(['net 192.168.0.0 netmask 255.255.255.128',
				'host 192.168.0.240'], list(i.routes))

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
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					i.ipv6_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					i.ipv6_address('default'))
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/80'),
					i.ipv6_address('other'))

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
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None,
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

		def test_ipv4_only(self):
			"""Test IPv4 only interface."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '1.2.3.4',
				'interfaces/eth0/netmask': '255.255.255.0',
				})
			self.assertEqual(['eth0'],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

		def test_incomplete_addr(self):
			"""Test incomplete interface with address."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				})
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None,
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

		def test_incomplete_net(self):
			"""Test incomplete interface with netmask/prefix."""
			t = Interfaces(ucr={
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth0/ipv6/default/prefix': '64',
				})
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(None,
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

		def test_ipv4_multi(self):
			"""Test multiple IPv4 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '1.2.3.4',
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth1/address': '2.3.4.5',
				'interfaces/eth1/netmask': '255.255.255.0',
				})
			self.assertEqual(['eth0', 'eth1'],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

		def test_ipv6_multi(self):
			"""Test multiple IPv6 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/default/prefix': '64',
				'interfaces/eth1/ipv6/default/address': '2:3:4:5:6:7:8:9',
				'interfaces/eth1/ipv6/default/prefix': '64',
				})
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth0', 'eth1'],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ipv6_address())

		def test_dual(self):
			"""Test dual stack interface."""
			t = Interfaces(ucr={
				'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth0/ipv6/default/prefix': '64',
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/netmask': '255.255.255.0',
				})
			self.assertEqual(['eth0'],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth0'],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('2.3.4.5/24'),
					t.get_default_ip_address())
			self.assertEqual(IPv4Network('2.3.4.5/24'),
					t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ipv6_address())

		def test_ipv6_disjunct(self):
			"""Test disjunct IPv4 IPv6 interfaces."""
			t = Interfaces(ucr={
				'interfaces/eth0/address': '2.3.4.5',
				'interfaces/eth0/netmask': '255.255.255.0',
				'interfaces/eth1/ipv6/default/address': '1:2:3:4:5:6:7:8',
				'interfaces/eth1/ipv6/default/prefix': '64',
				})
			self.assertEqual(['eth0'],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth1'],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('2.3.4.5/24'),
					t.get_default_ip_address())
			self.assertEqual(IPv4Network('2.3.4.5/24'),
					t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ipv6_address())

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
			self.assertEqual(['eth2', 'eth0', 'eth1'],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ip_address())
			self.assertEqual(IPv4Network('1.2.3.4/24'),
					t.get_default_ipv4_address())
			self.assertEqual(None,
					t.get_default_ipv6_address())

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
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual(['eth2', 'eth0', 'eth1'],
					[s.name for s, _n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('1:2:3:4:5:6:7:8/64'),
					t.get_default_ipv6_address())

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
			self.assertEqual([],
					[s.name for _n, s in t.ipv4_interfaces])
			self.assertEqual([
				('eth2', 'default'),
				('eth2', 'z'),
				('eth1', 'default'),
				('eth1', 'a'),
				('eth0', 'foo')],
				[(s.name, n) for s, n in t.ipv6_interfaces])
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/72'),
					t.get_default_ip_address())
			self.assertEqual(None,
					t.get_default_ipv4_address())
			self.assertEqual(IPv6Network('2:3:4:5:6:7:8:9/72'),
					t.get_default_ipv6_address())

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
		"""Rest alpha-numeric sorting."""
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
