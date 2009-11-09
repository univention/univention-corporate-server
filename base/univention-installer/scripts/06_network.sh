#!/bin/sh
#
# Univention Installer
#  network configuration
#
# Copyright (C) 2004-2009 Univention GmbH
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

echo
ifconfig -a | grep eth0
if [ "$?" -ne 0 ]; then
	echo "Warning Networking: eth0 not found"
	echo "YES" > /tmp/dummy-network-interface.txt
	modprobe dummy
	ifconfig dummy0 down
	/bin/ip link set dummy0 name eth0
	ifconfig eth0 192.168.0.2 netmask 255.255.255.0 up
	echo "Notice Networking: added virtual dummy interface as eth0"
	ifconfig eth0
fi

# setup physical interfaces during first run
# setup virtual interfaces during second run
for ifaceregex in "^eth[0-9]+_" "^eth[0-9]+_[0-9]+_" ; do
    set | egrep "${ifaceregex}type=" | while read line; do
    	ucr_network_device=`echo $line | sed -e 's|_type.*||'`
    	if [ -z "$ucr_network_device" ]; then
    		continue
    	fi
    	dynamic=`echo $line | sed -e 's|.*=||'`
    	if [ -n "$dynamic" ] && [ "$dynamic" = "dynamic" -o "$dynamic" = "dhcp" ]; then
    		python2.4 /sbin/univention-config-registry set interfaces/$ucr_network_device/type=dhcp

			address=`set | egrep "^${ucr_network_device}_ip=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
			if [ -n "$address" ]; then
				netmask=`set | egrep "^${ucr_network_device}_netmask=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				broadcast=`set | egrep "^${ucr_network_device}_broadcast=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				network=`set | egrep "^${ucr_network_device}_network=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				if [ -n "$netmask" ] || [ -n "$broadcast" ] || [ -n "$network" ]; then
					# for serverroles with ${ucr_network_device}_type='dynamic' or 'dhcp' the installer module 20_net also outputs
					# the data that was determined by dhclient at configuration time,
					# these values are recorded here to reflect the status that is written in the directory
					python2.4 /sbin/univention-config-registry set \
						interfaces/$ucr_network_device/fallback/address=$address \
						interfaces/$ucr_network_device/fallback/netmask=$netmask \
						interfaces/$ucr_network_device/fallback/broadcast=$broadcast \
						interfaces/$ucr_network_device/fallback/network=$network
				fi
			fi
    	fi

    	network_device=`echo $ucr_network_device | sed -e 's|_|:|g'`

		# try to bring up interface
		ifconfig $network_device up
		mkdir -p /var/lib/dhcp3/
		dhclient $network_device
    done
    set | egrep "${ifaceregex}ip=" | while read line; do

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

		# Note: if installer saved an address then configure the device now with that address, even if type=dynamic
		python2.4 /sbin/univention-config-registry set interfaces/$network_device/address=$address
		python2.4 /sbin/univention-config-registry set interfaces/$network_device/netmask=$netmask
		python2.4 /sbin/univention-config-registry set interfaces/$network_device/broadcast=$broadcast
		python2.4 /sbin/univention-config-registry set interfaces/$network_device/network=$network

		network_device=`echo $network_device | sed -e 's|_|:|g'`

		ifconfig $network_device $address netmask $netmask broadcast $broadcast up
    done
done

if [ -n "$gateway" ]; then
	python2.4 /sbin/univention-config-registry set gateway=$gateway
	route add default gw $gateway
fi


if [ -n "$nameserver_1" ]; then
	echo "nameserver $nameserver_1" >>/etc/resolv.conf
	python2.4 /sbin/univention-config-registry set nameserver1=$nameserver_1
fi

if [ -n "$nameserver_2" ]; then
	echo "nameserver $nameserver_2" >>/etc/resolv.conf
	python2.4 /sbin/univention-config-registry set nameserver2=$nameserver_2
fi

if [ -n "$nameserver_3" ]; then
	echo "nameserver $nameserver_3" >>/etc/resolv.conf
	python2.4 /sbin/univention-config-registry set nameserver3=$nameserver_3
fi

if [ -n "$proxy_http" ]; then
	python2.4 /sbin/univention-config-registry set proxy/http=$proxy_http
	python2.4 /sbin/univention-config-registry set proxy/ftp=$proxy_http
fi
