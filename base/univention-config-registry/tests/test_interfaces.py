#!/usr/bin/python3
"""Unit test for univention.config_registry.interfaces."""
# pylint: disable-msg=C0103,E0611,R0904

from os.path import devnull

import pytest
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface

import univention.config_registry.interfaces as ucri
from univention.config_registry.interfaces import _Iface, Interfaces, forgiving, cmp_alnum  # noqa E402


@pytest.fixture(autouse=True)
def tmpucr(monkeypatch):
	"""
	Setup UCR instance using `dev/null` for all tests.
	"""
	monkeypatch.setenv('UNIVENTION_BASECONF', devnull)


def test_VengefulConfigRegistry():
	ucr = ucri.VengefulConfigRegistry(ucri.ConfigRegistry())
	with pytest.raises(KeyError):
		ucr["key"]

	ucr["key"] = "value"
	assert ucr["key"] == "value"


class Test_Iface(object):

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
		assert 'NAME' == i.name
		assert 42 == i.order
		assert 'static' == i.type
		assert i.start
		assert IPv4Address(u'1.2.3.0') == i.network
		assert IPv4Address(u'1.2.3.255') == i.broadcast
		assert IPv4Interface(u'1.2.3.4/24') == i.ipv4_address()
		assert i.ipv6_address() is None
		assert ['1', '2'] == list(i.options)
		assert ['net 192.168.0.0 netmask 255.255.255.128', 'host 192.168.0.240'] == list(i.routes)

	def test_incomplete_addr(self):
		"""Test incomplete interface with address."""
		i = _Iface({
			'address': '2.3.4.5',
			'ipv6/default/address': '1:2:3:4:5:6:7:8',
		})
		assert i.ipv4_address() is None
		assert i.ipv6_address() is None

	def test_incomplete_net(self):
		"""Test incomplete interface with netmask/prefix."""
		i = _Iface({
			'netmask': '255.255.255.0',
			'ipv6/default/prefix': '64',
		})
		assert i.ipv4_address() is None
		assert i.ipv6_address() is None

	def test_invalid(self):
		"""Test invalid interface address."""
		i = _Iface({
			'address': '2.3.4.5',
			'netmask': '42',
			'ipv6/default/address': '1:2:3:4:5:6:7:8',
			'ipv6/default/prefix': '4711',
		})
		assert not i.ipv4_address()
		assert not i.ipv6_address()

	def test_ipv6(self):
		"""Test IPv6 functions."""
		i = _Iface({
			'name': 'NAME',
			'ipv6/default/address': '1:2:3:4:5:6:7:8',
			'ipv6/default/prefix': '64',
			'ipv6/other/address': '2:3:4:5:6:7:8:9',
			'ipv6/other/prefix': '80',
		})
		assert 'NAME' == i.name
		assert i.ipv4_address() is None
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == i.ipv6_address()
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == i.ipv6_address('default')
		assert IPv6Interface(u'2:3:4:5:6:7:8:9/80') == i.ipv6_address('other')


class TestInterfaces(object):

	"""Test implementation."""

	def test_empty(self):
		"""Test no interface."""
		t = Interfaces()
		assert 'eth0' == t.primary
		assert t.ipv4_gateway is None
		assert t.ipv6_gateway is None
		assert t.ipv6_gateway_zone_index is None
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert t.get_default_ip_address() is None
		assert t.get_default_ipv4_address() is None
		assert t.get_default_ipv6_address() is None

	def test_ipv4_only(self):
		"""Test IPv4 only interface."""
		t = Interfaces(ucr={
			'interfaces/eth0/address': '1.2.3.4',
			'interfaces/eth0/netmask': '255.255.255.0',
		})
		assert ['eth0'] == [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ip_address()
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ipv4_address()
		assert t.get_default_ipv6_address() is None

	def test_incomplete_addr(self):
		"""Test incomplete interface with address."""
		t = Interfaces(ucr={
			'interfaces/eth0/address': '2.3.4.5',
			'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
		})
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert t.get_default_ip_address() is None
		assert t.get_default_ipv4_address() is None
		assert t.get_default_ipv6_address() is None

	def test_incomplete_net(self):
		"""Test incomplete interface with netmask/prefix."""
		t = Interfaces(ucr={
			'interfaces/eth0/netmask': '255.255.255.0',
			'interfaces/eth0/ipv6/default/prefix': '64',
		})
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert t.get_default_ip_address() is None
		assert t.get_default_ipv4_address() is None
		assert t.get_default_ipv6_address() is None

	def test_invalid(self):
		"""Test invalid gateways."""
		t = Interfaces(ucr={
			"gateway": "invalid",
			"ipv6/gateway": "invalid",
		})
		assert t.ipv4_gateway is False
		assert t.ipv6_gateway is False
		assert t.ipv6_gateway_zone_index is None

	@pytest.mark.parametrize("value", [None, ""])
	def test_non_values(self, value):
		assert Interfaces(ucr={"key": value})

	def test_ipv4_multi(self):
		"""Test multiple IPv4 interfaces."""
		t = Interfaces(ucr={
			'interfaces/eth0/address': '1.2.3.4',
			'interfaces/eth0/netmask': '255.255.255.0',
			'interfaces/eth1/address': '2.3.4.5',
			'interfaces/eth1/netmask': '255.255.255.0',
		})
		assert ['eth0' == 'eth1'], [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ip_address()
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ipv4_address()
		assert t.get_default_ipv6_address() is None

	def test_ipv6_multi(self):
		"""Test multiple IPv6 interfaces."""
		t = Interfaces(ucr={
			'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
			'interfaces/eth0/ipv6/default/prefix': '64',
			'interfaces/eth1/ipv6/default/address': '2:3:4:5:6:7:8:9',
			'interfaces/eth1/ipv6/default/prefix': '64',
		})
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert ['eth0', 'eth1'] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ip_address()
		assert t.get_default_ipv4_address() is None
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ipv6_address()

	def test_dual(self):
		"""Test dual stack interface."""
		t = Interfaces(ucr={
			'interfaces/eth0/ipv6/default/address': '1:2:3:4:5:6:7:8',
			'interfaces/eth0/ipv6/default/prefix': '64',
			'interfaces/eth0/address': '2.3.4.5',
			'interfaces/eth0/netmask': '255.255.255.0',
		})
		assert ['eth0'] == [s.name for _n, s in t.ipv4_interfaces]
		assert ['eth0'] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv4Interface(u'2.3.4.5/24') == t.get_default_ip_address()
		assert IPv4Interface(u'2.3.4.5/24') == t.get_default_ipv4_address()
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ipv6_address()

	def test_ipv6_disjunct(self):
		"""Test disjunct IPv4 IPv6 interfaces."""
		t = Interfaces(ucr={
			'interfaces/eth0/address': '2.3.4.5',
			'interfaces/eth0/netmask': '255.255.255.0',
			'interfaces/eth1/ipv6/default/address': '1:2:3:4:5:6:7:8',
			'interfaces/eth1/ipv6/default/prefix': '64',
		})
		assert ['eth0'] == [s.name for _n, s in t.ipv4_interfaces]
		assert ['eth1'] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv4Interface(u'2.3.4.5/24') == t.get_default_ip_address()
		assert IPv4Interface(u'2.3.4.5/24') == t.get_default_ipv4_address()
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ipv6_address()

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
		assert ['eth2', 'eth0', 'eth1'] == [s.name for _n, s in t.ipv4_interfaces]
		assert [] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ip_address()
		assert IPv4Interface(u'1.2.3.4/24') == t.get_default_ipv4_address()
		assert t.get_default_ipv6_address() is None

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
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert ['eth2', 'eth0', 'eth1'] == [s.name for s, _n in t.ipv6_interfaces]
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ip_address()
		assert t.get_default_ipv4_address() is None
		assert IPv6Interface(u'1:2:3:4:5:6:7:8/64') == t.get_default_ipv6_address()

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
		assert [] == [s.name for _n, s in t.ipv4_interfaces]
		assert [
			('eth2', 'default'),
			('eth2', 'z'),
			('eth1', 'default'),
			('eth1', 'a'),
			('eth0', 'foo')] == \
			[(s.name, n) for s, n in t.ipv6_interfaces]
		assert IPv6Interface(u'2:3:4:5:6:7:8:9/72') == t.get_default_ip_address()
		assert t.get_default_ipv4_address() is None
		assert IPv6Interface(u'2:3:4:5:6:7:8:9/72') == t.get_default_ipv6_address()

	def test_order_mixed(self):
		"""Test multiple IPv6 ordering."""
		t = Interfaces(ucr={
			'interfaces/br0/order': 'br0',
			'interfaces/br1/order': '1',
		})
		assert ['br1', 'br0'] == [n for n, _s in t.all_interfaces]

	def test_basis(self):
		"""Test basic configuration."""
		t = Interfaces(ucr={
			'gateway': '1.2.3.4',
			'ipv6/gateway': '1:2:3:4:5:6:7:8',
			'interfaces/primary': 'br0',
		})
		assert 'br0' == t.primary
		assert IPv4Address(u'1.2.3.4') == t.ipv4_gateway
		assert IPv6Address(u'1:2:3:4:5:6:7:8') == t.ipv6_gateway
		assert t.ipv6_gateway_zone_index is None

	def test_v6llgw(self):
		"""Test IPv6 link-local gateway."""
		t = Interfaces(ucr={
			'ipv6/gateway': 'fe80::1%eth0',
		})
		assert IPv6Address(u'fe80::1') == t.ipv6_gateway
		assert 'eth0' == t.ipv6_gateway_zone_index

	def test_non_vengeful(self):
		"""Test ConfigRegistry not raining KeyError."""
		try:
			Interfaces(None)
		except AttributeError:
			self.fail('Failed to create Interfaces(None)')


class TestDecorator(object):

	"""Test forgiving decorator."""
	@forgiving()
	def value_through(self):
		"""Value through"""
		return 42

	def test_value_through(self):
		"""Test pass through decorator."""
		assert 'value_through' == self.value_through.__name__
		assert 'Value through' == self.value_through.__doc__
		assert 42 == self.value_through()

	@forgiving()
	def error_through(self):
		"""Error through"""
		raise KeyError(42)

	def test_error_through(self):
		"""Test exception decorator."""
		assert 'error_through' == self.error_through.__name__
		assert 'Error through' == self.error_through.__doc__
		with pytest.raises(KeyError):
			self.error_through()

	@forgiving({KeyError: 42})
	def error_translate(self):
		"""Error translate"""
		raise KeyError(42)

	def test_error_translate(self):
		"""Test translation decorator."""
		assert 'error_translate' == self.error_translate.__name__
		assert 'Error translate' == self.error_translate.__doc__
		assert 42 == self.error_translate()

	@forgiving({LookupError: 42})
	def error_super(self):
		"""Error super"""
		raise KeyError(42)

	def test_error_super(self):
		"""Test translation super-class decorator."""
		assert 'error_super' == self.error_super.__name__
		assert 'Error super' == self.error_super.__doc__
		assert 42 == self.error_super()

	@forgiving({LookupError: 0, KeyError: 42})
	def error_multi(self):
		"""Error multi"""
		raise KeyError(42)

	def test_error_multi(self):
		"""Test translation multi-class decorator."""
		assert 'error_multi' == self.error_multi.__name__
		assert 'Error multi' == self.error_multi.__doc__
		assert 42 == self.error_multi()


class TestSort(object):

	"""Rest alphanumeric sorting."""

	def test_all_num(self):
		"""Test all plain numeric."""
		data = [0, 1]
		assert data == sorted(data, key=cmp_alnum)

	def test_all_num_str(self):
		"""Test all string numeric."""
		data = ['0', '1']
		assert data == sorted(data, key=cmp_alnum)

	def test_all_str(self):
		"""Test all string."""
		data = ['a', 'b']
		assert data == sorted(data, key=cmp_alnum)

	def test_str_num_str(self):
		"""Test all string numeric."""
		data = ['0', 'b']
		assert data == sorted(data, key=cmp_alnum)

	def test_num_str(self):
		"""Test all string numeric."""
		data = [0, 'b']
		assert data == sorted(data, key=cmp_alnum)

	def test_mixed(self):
		"""Test mixed strings."""
		data = ['eth2', 'eth10']
		assert data == sorted(data, key=cmp_alnum)
