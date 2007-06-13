# -*- coding: utf-8 -*-
#
# Univention DHCP
#  listener module
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
description='Update new DHCP subnets'
filter='(objectClass=univentionDhcpSubnet)'
attributes=[]

import listener, univention_baseconfig
import univention.debug

baseConfig = univention_baseconfig.baseConfig()

def handler(dn, new, old):
	pass

def postrun():
	if baseConfig.has_key("dhcpd/enable") and ( baseConfig["dhcpd/enable"] in ["yes", "true", '1']):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DHCP: Restarting server')
		try:
			listener.run('/usr/bin/sv', ['sv', 'down', 'univention-dhcp'], uid=0)
			listener.run('/usr/bin/sv', ['sv', 'up', 'univention-dhcp'], uid=0)
		except Exception, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'Restart DHCP server failed: %s' % str(e))
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'UNIVENTION-DHCP: dhcpd disabled in baseconfig - not started.')

