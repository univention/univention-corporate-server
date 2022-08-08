# -*- coding: utf-8 -*-
#
# Univention DHCP
#  listener module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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

from __future__ import absolute_import

from listener import run, configRegistry as ucr
import univention.debug as ud


name = 'dhcp'
description = 'Restart the dhcp service if a dhcp subnet or a policy was changed'
filter = '''(|
	(objectClass=univentionDhcpSubnet)
	(objectClass=univentionDhcpService)
	(objectClass=univentionPolicyDhcpBoot)
	(objectClass=univentionPolicyDhcpDns)
	(objectClass=univentionPolicyDhcpDnsUpdate)
	(objectClass=univentionPolicyDhcpLeaseTime)
	(objectClass=univentionPolicyDhcpNetbios)
	(objectClass=univentionPolicyDhcpRouting)
	(objectClass=univentionPolicyDhcpScope)
	(objectClass=univentionPolicyDhcpStatements)
	(objectClass=univentionDhcpPool)
	(cn=dhcp)
	(objectClass=domain)
	)'''.replace('\n', '').replace('\t', '')
attributes = []


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	pass


def postrun():
	# type: () -> None
	if ucr.is_true("dhcpd/autostart", False):
		if ucr.is_true('dhcpd/restart/listener', False):
			ud.debug(ud.LISTENER, ud.INFO, 'DHCP: Restarting server')
			try:
				run('/bin/systemctl', ['systemctl', 'try-reload-or-restart', '--', 'isc-dhcp-server.service'], uid=0)
			except Exception as ex:
				ud.debug(ud.ADMIN, ud.WARN, 'The restart of the DHCP server failed: %s' % (ex,))
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'DHCP: the automatic restart of the dhcp server by the listener is disabled. Set dhcpd/restart/listener to true to enable this option.')
	else:
		ud.debug(ud.LISTENER, ud.INFO, 'DHCP: dcpd disabled in config_registry - not started.')
