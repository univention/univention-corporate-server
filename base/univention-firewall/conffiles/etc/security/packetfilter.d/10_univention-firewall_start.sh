#!/bin/sh
@%@UCRWARNING=# @%@
#
# Copyright 2004-2022 Univention GmbH
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

# shellcheck source=../../../../iptables.sh
. /usr/share/univention-firewall/iptables.sh

# initialise IPv4
iptables --wait -F
iptables --wait -F -t nat
iptables --wait -F -t mangle

# accept IPv4 connections from localhost
iptables --wait -A INPUT -i lo -j ACCEPT
iptables --wait -A OUTPUT -o lo -j ACCEPT

# accept established IPv4 connections
iptables --wait -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# accept all ICMP messages
iptables --wait -A INPUT -p icmp -j ACCEPT

# initialise IPv6
ip6tables --wait -F
ip6tables --wait -F -t mangle

# accept IPv6 connections from localhost
ip6tables --wait -A INPUT -i lo -j ACCEPT
ip6tables --wait -A OUTPUT -o lo -j ACCEPT

# accept established IPv6 connections
ip6tables --wait -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# accept all ICMPv6 messages
ip6tables --wait -A INPUT -p icmpv6 -j ACCEPT


@!@
def print_packetfilter(proto, port, dst, action):  # type: (str, str, str, str) -> None
	args = [
		"--wait",
		"-A", "INPUT",
		"-p", proto,
		"--dport", port,
		"-j", action,
	]

	if dst == 'all':
		ipv4 = ipv6 = args
	elif dst == 'ipv4':
		ipv4, ipv6 = args, []
	elif dst == 'ipv6':
		ipv4, ipv6 = [], args
	elif ':' in dst:
		ipv4, ipv6 = [], args + ["-d", dst]
	else:
		ipv4, ipv6 = args + ["-d", dst], []

	if ipv4:
		print("iptables %s" % " ".join(ipv4))

	if ipv6:
		print("ip6tables %s" % " ".join(ipv6))


import re
RE = re.compile(
	r'''
	^security/packetfilter/
	(?:package / (?P<pkg> [^/]+)/)?
	(?P<proto> tcp|udp) /
	(?P<port> \d+ (?:[:]\d+)? ) /
	(?P<dst> [^/]+)
	(?:/ (?P<lang> [^/]+))?
	$''',
	re.VERBOSE)

filterlist = {}  # type: Dict[Tuple[str, str, str], Dict[str, Dict[str, str]]]
skip_package = not configRegistry.is_true('security/packetfilter/use_packages', True)
for key, value in configRegistry.items():
	m = RE.match(key)
	if not m:
		continue

	pkg, proto, port, dst, lang = m.groups()
	if skip_package and pkg:
		continue

	filterlist.setdefault((proto, port, dst), {}).setdefault(pkg or "", {})[lang or ""] = value

for (proto, port, dst), pkgs in sorted(filterlist.items()):
	pkg, settings = min(pkgs.items())
	action = settings.pop("")
	print('')
	for lang, desc in settings.items():
		print('# %s[%s]: %s' % (pkg, lang, desc))
	print_packetfilter(proto, port, dst, action)
@!@
