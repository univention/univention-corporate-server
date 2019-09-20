# -*- coding: utf-8 -*-
#
# Univention DHCP
#  listener module
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

__package__ = ''  # workaround for PEP 366
import listener
from univention.config_registry import ConfigRegistry
import univention.debug as ud


def handler(dn, new, old):
	pass


def postrun():
	ucr = ConfigRegistry()
	ucr.load()

	if ucr.is_true("dhcpd/autostart", False):
		if ucr.is_true('dhcpd/restart/listener', False):
			ud.debug(ud.LISTENER, ud.INFO, 'DHCP: Restarting server')
			try:
				listener.run('/etc/init.d/univention-dhcp', ['univention-dhcp', 'restart'], uid=0)
			except Exception as e:
				ud.debug(ud.ADMIN, ud.WARN, 'The restart of the DHCP server failed: %s' % str(e))
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'DHCP: the automatic restart of the dhcp server by the listener is disabled. Set dhcpd/restart/listener to true to enable this option.')
	else:
		ud.debug(ud.LISTENER, ud.INFO, 'DHCP: dcpd disabled in config_registry - not started.')
