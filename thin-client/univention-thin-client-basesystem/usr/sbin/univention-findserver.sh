#!/bin/bash
#
# Univention Client Basesystem
#  helper script finding the best desktop server for a thin client
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

eval `/usr/sbin/univention-baseconfig shell ldap/mydn`
min_load=999999
for server in `univention_policy_result -s $ldap_mydn | grep univentionDesktopServer | sed -e 's/univentionDesktopServer=//g' | sed -e 's|"||g'`; do
    this_load=`lynx -dump -nolist $server/cgi-bin/univention-showload.cgi 2>/dev/null | grep "LOAD:" | sed -e 's/LOAD://g'`
    test "$this_load" -lt "$min_load" 2>/dev/null && {
	min_load=$this_load
	use_server=$server
    }
done

echo $use_server
