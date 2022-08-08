#!/usr/bin/env pytest-3
# SPDX-License-Identifier: AGPL-3.0
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2022 Univention GmbH

import pytest

import univention.ipcalc as ipcalc


@pytest.mark.parametrize("ip,net,rev,ptr", [
	("170.85.204.51/0.0.0.0", "", "170", "51.204.85"),
	("170.85.204.51/128.0.0.0", "", "170", "51.204.85"),
	("170.85.204.51/255.0.0.0", "170", "170", "51.204.85"),
	("170.85.204.51/255.255.0.0", "170.85", "170.85", "51.204"),
	("170.85.204.51/255.255.255.0", "170.85.204", "170.85.204", "51"),
	("170.85.204.51/255.255.255.255", "170.85.204.51", "170.85.204", "51"),
])
class TestIPv4(object):
	def test_network(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv4_network(ipcalc.IPv4Interface(ip)) == net

	def test_reverse(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv4_reverse(ipcalc.IPv4Interface(ip)) == rev

	def test_pointer(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv4_pointer(ipcalc.IPv4Interface(ip)) == ptr


@pytest.mark.parametrize("ip,net,rev,ptr", [
	("0000:1111:2222:3333:4444:5555:6666:7777/0", "", "0", "7.7.7.7.6.6.6.6.5.5.5.5.4.4.4.4.3.3.3.3.2.2.2.2.1.1.1.1.0.0.0"),
	("0000:1111:2222:3333:4444:5555:6666:7777/1", "", "0", "7.7.7.7.6.6.6.6.5.5.5.5.4.4.4.4.3.3.3.3.2.2.2.2.1.1.1.1.0.0.0"),
	("0000:1111:2222:3333:4444:5555:6666:7777/4", "0", "0", "7.7.7.7.6.6.6.6.5.5.5.5.4.4.4.4.3.3.3.3.2.2.2.2.1.1.1.1.0.0.0"),
	("0000:1111:2222:3333:4444:5555:6666:7777/64", "0000:1111:2222:3333", "0000:1111:2222:3333", "7.7.7.7.6.6.6.6.5.5.5.5.4.4.4.4"),
	("0000:1111:2222:3333:4444:5555:6666:7777/112", "0000:1111:2222:3333:4444:5555:6666", "0000:1111:2222:3333:4444:5555:6666", "7.7.7.7"),
	("0000:1111:2222:3333:4444:5555:6666:7777/128", "0000:1111:2222:3333:4444:5555:6666:7777", "0000:1111:2222:3333:4444:5555:6666:777", "7"),
])
class TestIPv6(object):
	def test_network(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv6_network(ipcalc.IPv6Interface(ip)) == net

	def test_reverse(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv6_reverse(ipcalc.IPv6Interface(ip)) == rev

	def test_pointer(self, ip, net, rev, ptr):
		assert ipcalc.calculate_ipv6_pointer(ipcalc.IPv6Interface(ip)) == ptr
