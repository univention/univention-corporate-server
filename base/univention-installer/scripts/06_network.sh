#!/bin/sh
#
# Univention Installer
#  network configuration
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

. /tmp/installation_profile

ifconfig lo 127.0.0.1 up

set | egrep "^eth.*_type=" | while read line; do
	network_device=`echo $line | sed -e 's|_type.*||'`
	if [ -z "$network_device" ]; then
		continue
	fi
	dynamic=`echo $line | sed -e 's|.*=||'`
	if [ -n "$dynamic" ] && [ "$dynamic" = "dynamic" -o "$dynamic" = "dhcp" ]; then
		python2.4 /sbin/univention-baseconfig set interfaces/$network_device/type=dhcp
	fi
	network_device=`echo $network_device | sed -e 's|_|:|g'`

	ifconfig $network_device up
done
set | egrep "^eth.*_ip=" | while read line; do

	network_device=`echo $line | sed -e 's|_ip.*||'`

	if [ -z "$network_device" ]; then
		continue
	fi

	address=`echo $line | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g"`
	netmask=`set | egrep "^${network_device}_netmask=" | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g"`
	broadcast=`set | egrep "^${network_device}_broadcast=" | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g"`
	network=`set | egrep "^${network_device}_network=" | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g"`

	if [ -z "$address" ] || [ -z "$netmask" ] || [ -z "$broadcast" ] || [ -z "$network" ]; then
		continue
	fi

	python2.4 /sbin/univention-baseconfig set interfaces/$network_device/address=$address
	python2.4 /sbin/univention-baseconfig set interfaces/$network_device/netmask=$netmask
	python2.4 /sbin/univention-baseconfig set interfaces/$network_device/broadcast=$broadcast
	python2.4 /sbin/univention-baseconfig set interfaces/$network_device/network=$network

	network_device=`echo $network_device | sed -e 's|_|:|g'`

	ifconfig $network_device $address netmask $netmask broadcast $broadcast up

done

if [ -n "$gateway" ]; then
	python2.4 /sbin/univention-baseconfig set gateway=$gateway
	route add default gw $gateway
fi


if [ -n "$nameserver_1" ]; then
	echo "nameserver $nameserver_1" >>/etc/resolv.conf
	python2.4 /sbin/univention-baseconfig set nameserver1=$nameserver_1
fi

if [ -n "$nameserver_2" ]; then
	echo "nameserver $nameserver_2" >>/etc/resolv.conf
	python2.4 /sbin/univention-baseconfig set nameserver2=$nameserver_2
fi

if [ -n "$nameserver_3" ]; then
	echo "nameserver $nameserver_3" >>/etc/resolv.conf
	python2.4 /sbin/univention-baseconfig set nameserver3=$nameserver_3
fi

if [ -n "$proxy_http" ]; then
	python2.4 /sbin/univention-baseconfig set proxy/http=$proxy_http
	python2.4 /sbin/univention-baseconfig set proxy/ftp=$proxy_http
fi
