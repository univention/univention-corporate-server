#!/bin/sh
#
# Univention Installer
#  helper script: configuring network interface
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

echo -n "Setting up network: "
ip_cmdline=`cat /proc/cmdline | grep "ip="`

if [ -n "$ip_cmdline" ]; then
	_ip=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $1}'`
	_netmask=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $4}'`
	_gateway=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $3}'`

	echo -n " lo "
	ifconfig lo 127.0.0.1 up
	if [ -x /sbin/portmap ]; then
		/sbin/portmap
	fi
	echo -n " eth0 "
	ifconfig eth0 $_ip netmask $_netmask
	route add default gw $_gateway
fi

echo ""
