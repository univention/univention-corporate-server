# -*- coding: utf-8 -*-
#
# Univention DHCP
#  listener module
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

name='dhcp'
description='Restart the dhcp service if a dhcp subnet or a policy was changed'
filter='(|(objectClass=univentionDhcpSubnet)(objectClass=univentionDhcpService)(objectClass=univentionPolicyDhcpBoot)(objectClass=univentionPolicyDhcpDns)(objectClass=univentionPolicyDhcpDnsUpdate)(objectClass=univentionPolicyDhcpLeaseTime)(objectClass=univentionPolicyDhcpNetbios)(objectClass=univentionPolicyDhcpRouting)(objectClass=univentionPolicyDhcpScope)(objectClass=univentionPolicyDhcpStatements)(cn=dhcp)(objectClass=domain))'
attributes=[]

import listener, univention_baseconfig
import univention.debug


def handler(dn, new, old):
	pass

def postrun():
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	if baseConfig.has_key("dhcpd/autostart") and ( baseConfig["dhcpd/autostart"] in ["yes", "true", '1']):
		if baseConfig.has_key('dhcpd/restart/listener') and baseConfig['dhcpd/restart/listener'] in ['yes', 'true', '1']:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DHCP: Restarting server')
			try:
				listener.run('/etc/init.d/univention-dhcp', ['univention-dhcp', 'restart'], uid=0)
			except Exception, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'The restart of the DHCP server failed: %s' % str(e))
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'DHCP: the automatic restart of the dhcp server by the listener is disabled. Set dhcpd/restart/listener to true to enable this option.')
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DHCP: dcpd disabled in baseconfig - not started.')


