#!/bin/sh
#
# Univention Installer
#  network configuration
#
# Copyright 2004-2011 Univention GmbH
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

# update progress message
. /tmp/progress.lib
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring network interfaces")" >&9

. /tmp/installation_profile

ifconfig lo 127.0.0.1 up

echo
ifconfig -a | grep ^eth
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
    	dynamic=`echo $line | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
    	if [ -n "$dynamic" ] && [ "$dynamic" = "dynamic" -o "$dynamic" = "dhcp" ]; then
    		python2.6 /sbin/univention-config-registry set interfaces/$ucr_network_device/type=dhcp

			address=`set | egrep "^${ucr_network_device}_ip=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
			if [ -n "$address" ]; then
				netmask=`set | egrep "^${ucr_network_device}_netmask=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				broadcast=`set | egrep "^${ucr_network_device}_broadcast=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				network=`set | egrep "^${ucr_network_device}_network=" | sed -e 's|.*=||' -e 's|"||g' -e "s|'||g"`
				if [ -n "$netmask" ] || [ -n "$broadcast" ] || [ -n "$network" ]; then
					# for serverroles with ${ucr_network_device}_type='dynamic' or 'dhcp' the installer module 20_net also outputs
					# the data that was determined by dhclient at configuration time,
					# these values are recorded here to reflect the status that is written in the directory
					python2.6 /sbin/univention-config-registry set \
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
		python2.6 /sbin/univention-config-registry set interfaces/$network_device/address=$address
		python2.6 /sbin/univention-config-registry set interfaces/$network_device/netmask=$netmask
		python2.6 /sbin/univention-config-registry set interfaces/$network_device/broadcast=$broadcast
		python2.6 /sbin/univention-config-registry set interfaces/$network_device/network=$network

		network_device=`echo $network_device | sed -e 's|_|:|g'`

		ifconfig $network_device $address netmask $netmask broadcast $broadcast up
    done

	# set IPv6 acceptra
    set | egrep "${ifaceregex}acceptra=" | while read line; do
    	network_device=`echo $line | sed -e 's|_acceptra.*||'`
    	if [ -z "$network_device" ]; then
    		continue
    	fi

    	acceptra="$(echo $line | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g")"

		python2.6 /sbin/univention-config-registry set "interfaces/$network_device/ipv6/acceptRA=false"
		if [ -n "$acceptra" ] ; then
			if [ "$acceptra" = "true" ] ; then
				python2.6 /sbin/univention-config-registry set "interfaces/$network_device/ipv6/acceptRA=$acceptra"
				sysctl -w "net.ipv6.conf.${network_device}.accept_ra=1"
			else
				sysctl -w "net.ipv6.conf.${network_device}.accept_ra=0"
			fi
		fi
		ip link set "$network_device" up
	done

	# set IPv6 address
    set | egrep "${ifaceregex}ip6=" | while read line; do

    	network_device=`echo $line | sed -e 's|_ip6.*||'`

    	if [ -z "$network_device" ]; then
    		continue
    	fi

    	address="$(echo $line | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g")"
		prefix="$(set | egrep "^${network_device}_prefix6=" | sed -e 's|.*=||' | sed -e 's|"||g' | sed -e "s|'||g")"

    	if [ -n "$address" -a -n "$prefix" ] ; then
			python2.6 /sbin/univention-config-registry set "interfaces/$network_device/ipv6/default/address=$address" "interfaces/$network_device/ipv6/default/prefix=$prefix"
			ip link set "$network_device" up
			ip -6 addr add "$address/$prefix" dev "${network_device}"
    	fi
    done
done

if [ -n "$gateway" ]; then
	python2.6 /sbin/univention-config-registry set gateway=$gateway

	nm=$(python2.6 /sbin/univention-config-registry get interfaces/eth0/netmask)
	if [ -n "$nm" ]; then
		if [ "$nm" = "255.255.255.255" ]; then
			ip route add $gateway/32 dev eth0
		fi
	fi
	route add default gw $gateway
fi
# set IPv6 gateway
if [ -n "$gateway6" ]; then
	python2.6 /sbin/univention-config-registry set "ipv6/gateway=$gateway6"
	ip -6 route add ::/0 via "$gateway6" 
fi


if [ -n "$nameserver_1" ]; then
	echo "nameserver $nameserver_1" >>/etc/resolv.conf
	python2.6 /sbin/univention-config-registry set nameserver1=$nameserver_1
fi

if [ -n "$nameserver_2" ]; then
	echo "nameserver $nameserver_2" >>/etc/resolv.conf
	python2.6 /sbin/univention-config-registry set nameserver2=$nameserver_2
fi

if [ -n "$nameserver_3" ]; then
	echo "nameserver $nameserver_3" >>/etc/resolv.conf
	python2.6 /sbin/univention-config-registry set nameserver3=$nameserver_3
fi

if [ -n "$proxy_http" ]; then
	python2.6 /sbin/univention-config-registry set proxy/http=$proxy_http
	python2.6 /sbin/univention-config-registry set proxy/ftp=$proxy_http
fi
