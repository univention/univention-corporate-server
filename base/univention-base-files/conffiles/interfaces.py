# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
"""config registry module for the network interfaces."""
#
# Copyright 2004-2019 Univention GmbH
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

import re
from subprocess import call

RE_IFACE = re.compile(r'^interfaces/([^/]+)/((?:ipv6/([^/]+)/)?.*)$')
SKIP = set(('interfaces/restart/auto',))
PRIMARY = 'interfaces/primary'
GATEWAYS = set(('gateway', 'ipv6/gateway'))


def _common(ucr, changes, command):
	"""Run command on changed interfaces."""
	if not ucr.is_true('interfaces/restart/auto', True):
		return
	interfaces = set()
	if GATEWAYS & set(changes):
		# Restart all interfaces on gateway change
		interfaces.add('-a')
	else:
		# Restart both old and new primary interfaces
		if PRIMARY in changes:
			interfaces |= set((_ for _ in changes[PRIMARY] if _))
		# Collect changed interfaces
		for key, old_new in changes.items():
			if key in SKIP:
				continue
			match = RE_IFACE.match(key)
			if not match:
				continue
			iface, _subkey, _ipv6_name = match.groups()
			interfaces.add(iface.replace('_', ':'))
	# Shutdown changed interfaces
	for iface in interfaces:
		call((command, iface))


def preinst(ucr, changes):
	"""Pre run handler to shutdown changed interfaces."""
	_common(ucr, changes, 'ifdown')


def postinst(ucr, changes):
	"""Post run handler to start changed interfaces."""
	_common(ucr, changes, 'ifup')

# vim:set sw=4 ts=4 noet:
