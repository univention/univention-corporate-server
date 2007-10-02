#!/bin/sh -e
#
# Univention Client Basesystem
#  init script: setting up a thin client
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

getXModul()
{
    card=`kudzu -p --class=video | grep ^driver | sed -e 's/driver: Card://g'`
    if [ -z "$card" ]; then
		echo "vesa"
		return
    fi

    driver=`cat /usr/share/hwdata/Cards | grep -1 "^NAME $card$" | grep CHIPSET | sed -e 's/CHIPSET //g'`
    if [ -z "$driver" ]; then
		card=`cat /usr/share/hwdata/Cards | grep -1 "^NAME $card$" | grep SEE | sed -e 's/SEE //g'`
		if [ -z "$card" ]; then
			if [ -n "`kudzu -p --class=video | grep 'desc: VMWare Inc|unknown'`" ]; then
				echo "vmware"
			else
				echo "vesa"
			fi
			return
		fi
		driver=`cat /usr/share/hwdata/Cards | grep -1 "^NAME $card$" | grep CHIPSET | sed -e 's/CHIPSET //g'`
		if [ -z "$driver" ] ; then
			echo "vesa"
			return
		fi
    else
		driver=`cat /usr/share/hwdata/Cards | grep -2 "^NAME $card$" | grep DRIVER | sed -e 's/DRIVER //g'`
    fi

    echo "$driver" | head -1 |  tr [:upper:] [:lower:]
}

preparePythonEnvironment ()
{
	mkdir -p /var/lib/python-support/python2.4/
	update-python-modules -i /usr/share/python-support/python-dns
}

ramdisk="/ramdisk"

echo -n "Setting up diskless filesystem: "

dmesg -n 1

echo -n "   Loadkeys de: " >>/dev/tty8
loadkeys de >/dev/tty8 2>&1
echo  "" >>/dev/tty8

#prepare ramdisk

mkdir -p /proc

mount /proc

mount -t tmpfs /dev/shm "$ramdisk"
mkdir -p -m 1777 "$ramdisk/tmp" "$ramdisk/var/tmp"
for dir in "/var/lib/dhcp3" "/etc/univention" "/home" "/var/lib/univention-home-mounter" "/var/run/cups" "/etc/network/run" "/etc/X11" "/etc/apt" "/etc/cron.d" "/etc/default" "/etc/init.d" "/etc/samba" "/etc/udev/rules.d";
  do
  mkdir -p "$ramdisk$dir"
done

for file in "/etc/network/ifstate" "/etc/network/interfaces" "/etc/udev/rules.d/z25_persistent-net.rules" "/modules.dep";
  do
  touch "$ramdisk$file"
done

echo "   creating cache directory " >>/dev/tty8
mkdir -p /var/cache/univention-config

# install template directories
cd /
find etc/univention/templates/files -type d | while read d; do
	n=${d#etc/univention/templates/files}
	mkdir -p "$ramdisk$n"
done

preparePythonEnvironment

univention-baseconfig commit /etc/default/bootsplash

echo -n "   ip address: " >>/dev/tty8
ipcmd=`cat /proc/cmdline | grep ip | sed -e 's/.*ip=//g'`
myip=`echo $ipcmd | awk -F ':' '{print $1}'`
subnetmask=`echo $ipcmd | awk -F ':' '{print $4}'`
network=""

for n in `echo $subnetmask.$myip | awk -F '.' '{print $4"."$8" "$3"."$7" "$2"."$6" "$1"."$5}'`
  do
  mnm=`echo $n | awk -F '.' '{print $1}'`
  mip=`echo $n | awk -F '.' '{print $2}'`
  if [ "$mnm" = "255" ]
	  then
	  network="."$mip$network
	  else
	  network=".0"$network
  fi
done
network=`echo $network | sed -e "s/.//"`

if [ ! -z $myip ]; then
	echo "  $myip" >>/dev/tty8
else  fqn
	echo " failed"
	echo "  Failed to get the ip address from the /proc/cmdline."
	echo "  /proc/cmdline: $(cat /proc/cmdline)"
	read
	halt
fi

echo -n "   dns server: " >>/dev/tty8
nameserver=`cat /proc/cmdline | grep DNSSERVER | sed -e 's/.*DNSSERVER=//g' | awk '{print $1}'`
if [ ! -z $nameserver ]; then
	echo "  $nameserver" >>/dev/tty8
	echo "nameserver $nameserver" >/etc/resolv.conf
else
	echo "  failed"
	echo "Missing the DNSSERVER parameter in /proc/cmdline. Try to set the Univention Config Registry variable pxe/nameserver and resync the clientbootpxe listener module"
	read
	halt
fi

nameserver_fqdn=`/usr/bin/dns-lookup $nameserver ptr | head -1`

echo -n "   FQDN: " >>/dev/tty8
fqn=`/usr/bin/dns-lookup $myip ptr | head -1`

  hostname=`echo $fqn | cut -d'.' -f 1`
domainname=`echo $fqn | cut -d'.' -f 2-`

echo "  $hostname.$domainname" >>/dev/tty8


hostname $hostname >>/dev/tty8
univention-baseconfig set hostname="$hostname" domainname="$domainname" nameserver="$nameserver" interfaces/eth0/address="$myip" interfaces/eth0/netmask="$subnetmask" interfaces/eth0/network="$network"  >/dev/tty8 2>&1

# searching ldap server for this subnet
res=$(/usr/bin/dns-lookup _ldap._tcp.$domainname srv | \
	while read priority weight ldap_port_tmp ldap_server_tmp; do
		ldapIP=`host $ldap_server_tmp | awk '{print $4}'`
		if [ "$ldapIP" != "3(NXDOMAIN)" -a "$ldapIP" != "found" ]; then
			for ((i=1; i<5; i++)); do
				if [ "`echo $myip | cut -d '.' -f $i`" == "`echo $ldapIP | cut -d '.' -f $i`" ]; then
					continue
				else
					if [ "$(echo $subnetmask | cut -d '.' -f $i)" == "255" ]; then
						break
					else
						ldapServer=$ldap_server_tmp
						break
					fi
				fi
			done
			if [ -n "$ldapServer" ]; then
				ping -c 1 $ldapServer 1>/dev/null 2>/dev/null
				if [ "$?" -eq 0 ]; then
					echo "$ldapServer $ldap_port_tmp"
					break;
				else
					ldapServer=""
				fi
			fi
		fi
	done)

if [ -n "$ldapServer" ]
	then
	echo "No LDAP-Server server in local subnet found"

    #if nothing found take the first we can ping
	res=$(/usr/bin/dns-lookup _ldap._tcp.$domainname srv | \
		while read priority weight ldap_port ldap_server; do
			ldapIP=`host $ldap_server | awk '{print $4}'`
			if [ -n "$ldapServer" ]; then
				ping -c 1 $ldapServer 1>/dev/null 2>/dev/null
				if [ "$?" -eq 0 ]; then
					echo "$ldapServer $ldap_port_tmp"
					break;
				else
					ldapServer=""
				fi
			fi
		done)
fi

ldapServer=`echo $res | awk '{ print $1 }'`
ldapPort=`echo $res | awk '{ print $2 }'`
if [ -z "$ldapServer" -o -z "$ldapPort" ]; then
	echo "LDAP Server and/or Port missing"
	echo "Check dns entry _ldap._tcp.$domainname"
	bash
fi

ldapBase=`ldapsearch -x -h $ldapServer -p $ldapPort -b "" -s base 'objectclass=*' NamingContexts -LLL | grep "namingContexts" | sed -e 's/.*namingContexts: //g'`
if [ -z "$ldapBase" ]; then
	echo "Could not find ldapBase"
	echo "ldapsearch -x -h $ldapServer -p $ldapPort -b "" -s base 'objectclass=*' NamingContexts -LLL | grep "namingContexts" | sed -e 's/.*namingContexts: //g'"
	bash
fi

myDN=`ldapsearch -x -h $ldapServer -p $ldapPort -b $ldapBase "(&(cn=$hostname)(objectClass=univentionThinClient))" -LLL dn | grep -A4 "^dn:" | perl -e '$f=""; $f.=$_ while(<>); $f =~ s/\n //g; print $f;' | grep "^dn:" | sed -e 's/dn: //g'`

univention-baseconfig set ldap/server/name=$ldapServer ldap/port=$ldapPort ldap/base=$ldapBase ldap/mydn=$myDN >/dev/tty8 2>&1

# update config registry entries via ldap policies
/usr/lib/univention-directory-policy/univention-policy-update-config-registry $myDN

## get the policies

policy_file=$(mktemp)
policy_file_result=$(mktemp)

# remove univentionRegistry entries - handled earlier by univention-policy-update-config-registry
univention_policy_result -h $ldapServer -s $myDN | sed -e 's|fixedAttributes=[^ ]*||;s|"||g' -e 's|^univentionRegistry;entry-.*||;s|"||g' >$policy_file
cat $policy_file | while read line; do

	# split the line a=b in a and b
	var="${line%%=*}"
	val="${line#*=}"

	if [ -n "$var" ] && [ -n "$val" ]; then
		new_value=$(grep "$var=" /etc/univention/templates/mapping/* | head -n 1 | sed -e 's|.*=||;s|"||g')
		if [ -n "${new_value}" ]; then
			echo $line | sed -e "s|${var}=|${new_value}=|g" >>$policy_file_result
		else
			echo $line >>$policy_file_result
		fi
	fi

done

univention-baseconfig set $(cat $policy_file_result) >/dev/tty8 2>&1

eval $(univention-baseconfig shell)

# set all desktopServer as possible timeserver

timeserver=''
for i in `cat $policy_file_result | grep univentionDesktopServer | sed -e 's|.*univentionDesktopServer=||' | sed -e 's|"||g'`; do
  timeserver=`echo $timeserver ' ' $i`
done

univention-baseconfig set ntpdate/server="$timeserver" >/dev/tty8 2>&1

for i in $timeserver; do
	if /bin/netcat -q0 -w4 $i 37 </dev/null >/dev/null 2>&1; then
		/usr/sbin/rdate $i >/dev/tty8 2>&1
	fi
	/usr/sbin/ntpdate $i >/dev/tty8 2>&1 && break
done

/sbin/hwclock --systohc



authserver=''
for i in `cat $policy_file_result | grep univentionAuthServer | sed -e 's|.*univentionAuthServer=||' | sed -e 's|"||g'`; do
  authserver="$authserver $i"
done

if [ -n "$authserver" ]; then
	univention-baseconfig set univentionAuthServer="$authserver" >/dev/tty8 2>&1
fi

realm=`/usr/bin/dns-lookup _kerberos.$domainname txt | head -1`
if [ -z "$realm" ]; then
    echo "WARNING: Kerberos realm TXT record not found. Check the DNS for the TXT record _kerberos.$domainname"
else
	univention-baseconfig set kerberos/realm=$realm >/dev/tty8 2>&1
fi

eval `univention-baseconfig shell`

vals="portmap/autostart?yes locale/default?de_DE.UTF-8:UTF-8"

if [ -z "$xorg_device_drive" ]; then
	vals="$vals xorg/device/driver?`eval getXModul`"
fi
if [ -z "$xorg_resolution" ]; then
	vals="$vals xorg/resolution?1024x768"
fi
if [ -z "$xorg_screen_DefaultDepth" ]; then
	vals="$vals xorg/screen/DefaultDepth?24"
fi
if [ -n "$vals" ]; then
	univention-baseconfig set $vals >/dev/tty8 2>&1
fi

# univention-baseconfig set locale/default?"de_DE@euro:ISO-8859-15"

univention-baseconfig set univentionAutoStartScript="`univention-policy-result -h $ldapServer -s $myDN  | grep univentionAutoStartScript= | sed -e 's|univentionAutoStartScript=||' `" >/dev/tty8 2>&1
# prepare to run gdm
univention-baseconfig commit	/etc/default/gdm \
								/etc/gdm/gdm.conf \
								/etc/gdm/Init/Default \
								/usr/share/gdm/themes/univention/univention.xml\
								/etc/pam.d/gdm-autologin >/dev/tty8 2>&1

chown gdm.gdm /var/lib/gdm
chmod 0750 /var/lib/gdm

mkdir -p /ramdisk/etc/cups/ppd/
mkdir -p /var/spool/cups/cert/

# DEBUG-Messages for tty10
echo "Local-Settings:" > /dev/tty8
echo "Policy-Settings:" > /dev/tty9

univention-baseconfig dump | grep -v univention > /dev/tty8
univention-baseconfig dump | grep univention > /dev/tty9

if [ "`univention-baseconfig get univentionXMouseDevice`" = "/dev/input/mice" ]; then
    modprobe usbmouse >/dev/tty8 2>&1
fi

echo "done."
