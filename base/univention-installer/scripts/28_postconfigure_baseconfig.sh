#!/bin/sh
#
# Univention Installer
#  configure Univention Baseconfig
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

architecture=`/bin/uname -m`

acpi_off=`grep "acpi=off" /proc/cmdline`
pci_acpi_off=`grep "pci=noacpi" /proc/cmdline`
pci_acpi_on=`grep "pci=acpi" /proc/cmdline`
grub_append=`cat /proc/cmdline | sed -e 's|.* profile||;s|.* usb||;s|.* floppy||;s|.* text||'`
version_version=`cat /instmnt/sourcedevice/.univention_install | grep VERSION | sed -e 's|VERSION=||'`
version_patchlevel=`cat /instmnt/sourcedevice/.univention_install | grep PATCHLEVEL | sed -e 's|PATCHLEVEL=||'`

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi
cat >>/instmnt/hostname.sh <<__EOT__
if [ -n "$to_scan" ] || [ -n "$scan" ]; then
	for ts in $to_scan $scan; do
		if [ "\$ts" = "hostname" ]; then
			ipcmd=\`cat /proc/cmdline | grep ip | sed -e 's/.*ip=//g'\`
			myip=\`echo \$ipcmd | awk -F ':' '{print \$1}'\`
			if [ -n "$nameserver1" ]; then
				host=\`host \$myip $nameserver1 |tail -1 | awk '{print \$5}' | awk -F '.' '{print \$1}'\`
			elif [ -n "$nameserver_1" ]; then
				host=\`host \$myip $nameserver_1 |tail -1 | awk '{print \$5}' | awk -F '.' '{print \$1}'\`
			fi
		fi
	done
fi
if [ -n "\$host" ]; then
	univention-baseconfig set hostname=\$host
elif [ -n "$hostname" ]; then
	univention-baseconfig set hostname=$hostname
fi
__EOT__

chmod +x /instmnt/hostname.sh
chroot /instmnt ./hostname.sh

cat >>/instmnt/postconfigure_baseconfig.sh <<__EOT__

univention-baseconfig set domainname=$domainname
#univention-baseconfig set hostname=$hostname
univention-baseconfig set windows/domain=$windows_domain
hostname $hostname

if [ -n "$eth0_type" -a "$eth0_type" = "dynamic" ]; then
	univention-baseconfig set interfaces/eth0/type=dhcp
fi

if [ -n "$use_external_nameserver" -a "$use_external_nameserver" = "true" ]; then
	univention-baseconfig set nameserver/external=true
else
	univention-baseconfig set nameserver/external=false
fi

if [ -n "$dns_forwarder_1" ]; then
	univention-baseconfig set dns/forwarder1=$dns_forwarder_1
fi
if [ -n "$dns_forwarder_2" ]; then
	univention-baseconfig set dns/forwarder2=$dns_forwarder_2
fi
if [ -n "$dns_forwarder_3" ]; then
	univention-baseconfig set dns/forwarder3=$dns_forwarder_3
fi

if [ -n "$create_home_share" -a "$create_home_share" = "true" ]; then
	univention-baseconfig set create/home/share=true
fi


if [ -n "$ldap_position" ]; then
	univention-baseconfig set ldap/position="$ldap_position"
fi

if [ "$server_role" = "domaincontroller_master" ]; then
	if [ -n "$ldap_base" ]; then
		univention-baseconfig set ldap/base="$ldap_base"
	fi
	univention-baseconfig set ldap/server/ip=$eth0_ip
	univention-baseconfig set ldap/server/name=$hostname.$domainname
	univention-baseconfig set ldap/master=$hostname.$domainname
	univention-baseconfig set kerberos/adminserver=$hostname.$domainname
	univention-baseconfig set server/role=domaincontroller_master
	univention-baseconfig set ldap/server/type=master
else
	if [ -n "$ldap_base" ]; then
		univention-baseconfig set ldap/base="$ldap_base"
	fi
	if [ -n "$domain_controller_ip" ]; then
		univention-baseconfig set ldap/master/ip=$domain_controller_ip
	fi

	univention-baseconfig set ldap/server/type=slave

	if [ $server_role = "domaincontroller_slave" ]; then
		univention-baseconfig set server/role=domaincontroller_slave
	elif [ $server_role = "memberserver" ]; then
		univention-baseconfig set server/role=memberserver
	elif [ $server_role = "managed_client" ]; then
		univention-baseconfig set server/role=fatclient
	elif [ $server_role = "mobile_client" ]; then
		univention-baseconfig set server/role=mobileclient
	elif [ $server_role = "domaincontroller_backup" ]; then
		univention-baseconfig set server/role=domaincontroller_backup
	fi
fi

if [ -n "$ssl_country" ]; then
	univention-baseconfig set ssl/country="$ssl_country"
fi
if [ -n "$ssl_state" ]; then
	univention-baseconfig set ssl/state="$ssl_state"
fi
if [ -n "$ssl_locality" ]; then
	univention-baseconfig set ssl/locality="$ssl_locality"
fi
if [ -n "$ssl_organization" ]; then
	univention-baseconfig set ssl/organization="$ssl_organization"
fi
if [ -n "$ssl_organizationalunit" ]; then
	univention-baseconfig set ssl/organizationalunit="$ssl_organizationalunit"
fi
if [ -n "$ssl_common" ]; then
	univention-baseconfig set ssl/common="$ssl_common"
fi
if [ -n "$ssl_email" ]; then
	univention-baseconfig set ssl/email=$ssl_email
fi

if [ -n "$acpi_off" ]; then
	univention-baseconfig set "$(univention-baseconfig get grub/append) acpi=off"
fi

if [ -n "$pci_acpi_off" ]; then
	univention-baseconfig set "$(univention-baseconfig get grub/append) pci=noacpi"
fi

if [ -n "$grub_append" ]; then
	univention-baseconfig set grub/append="$grub_append"
fi

univention-baseconfig set locale="$locales"

if [ -n "$locale_default" ]; then
	short_form=`echo $locale_default | cut -c 1-2`

	univention-baseconfig set "locale/default"="$locale_default"

	univention-baseconfig set admin/web/language="\$short_form"
	univention-baseconfig set console/web/language="\$short_form"
	univention-baseconfig set gdm/language="\$locale_default"
fi

echo "$timezone" >/etc/timezone
ln -sf /usr/share/zoneinfo/$timezone /etc/localtime

if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	cp /usr/share/keymaps/powerpc/*/$keymap.kmap.gz /etc/console/boottime.kmap.gz >/dev/null 2>&1
else
	cp /usr/share/keymaps/i386/*/$keymap.kmap.gz /etc/console/boottime.kmap.gz
fi

univention-baseconfig set version/version=$version_version
univention-baseconfig set version/patchlevel=$version_patchlevel

univention-baseconfig commit

__EOT__

chmod +x /instmnt/postconfigure_baseconfig.sh
chroot /instmnt ./postconfigure_baseconfig.sh
