#!/bin/sh
#
# Univention Installer
#  helper script: configuring network interface
#
# Copyright 2004-2012 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

echo -n "Setting up network: "
ip_cmdline=`cat /proc/cmdline | grep "ip="`

if [ -n "$ip_cmdline" ]; then
	_ip=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $1}'`
	_netmask=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $4}'`
	_gateway=`cat /proc/cmdline | sed -e 's|.*ip=||g' | awk -F ':' '{print $3}'`
	_networksleep=`cat /proc/cmdline | sed -nre 's/^.*\bnetworksleep=([^ ]+)\b.*$/\1/p'`

	echo -n " lo "
	ifconfig lo 127.0.0.1 up
	if [ -x /sbin/portmap ]; then
		/sbin/portmap
	fi
	if [ -x /sbin/rpc.statd ]; then
		/sbin/rpc.statd
	fi
	echo -n " eth0 "
	ifconfig eth0 $_ip netmask $_netmask
	if [ ! "$_gateway" = "0.0.0.0" ] ; then
		route add default gw $_gateway
	fi

	if [ -z "$_networksleep" ]; then
		_networksleep=10
	fi
	sleep $_networksleep

fi

echo ""
