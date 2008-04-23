#!/bin/sh
#
# Univention Installer
#  setup required user accounts
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

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

cat >>/instmnt/ldap.sh <<__EOT__


if [ "$server_role" = "domaincontroller_master" ]; then
	eval \`univention-config-registry shell\`
	echo "Create User Administrator"
	univention-directory-manager users/user create --position="cn=users,\$ldap_base" --set username=Administrator --set unixhome=/home/Administrator --set lastname=Administrator --set password="\$root_password" --set primaryGroup="cn=Domain Admins,cn=groups,\$ldap_base" --policy-reference "cn=default-admins,cn=admin-settings,cn=users,cn=policies,\$ldap_base" >/dev/null 2>&1
	univention-directory-manager groups/group modify --dn "cn=DC Backup Hosts,cn=groups,\$ldap_base" --append users="uid=Administrator,cn=users,\$ldap_base" > /dev/null 2>&1

	#create default network
	forwardZone=\`univention-directory-manager dns/forward_zone list --filter zone=\$domainname | grep DN | head -1 | sed -e 's/DN: //g'\`
	reverseZone=\`univention-directory-manager dns/reverse_zone list | grep ^DN | head -1 | sed -e 's|DN: ||'\`
	dhcpService=\`univention-directory-manager dhcp/service list | grep DN | head -1 | sed -e 's/DN: //g'\`

	echo "Create default network"
	univention-directory-manager networks/network create --position "cn=networks,\$ldap_base" --set name=default --set netmask=\$interfaces_eth0_netmask --set network=\$interfaces_eth0_network --set dnsEntryZoneForward=\$forwardZone --set dnsEntryZoneReverse=\$reverseZone --set dhcpEntryZone=\$dhcpService >/dev/null 2>&1
fi

__EOT__

chmod +x /instmnt/ldap.sh
export root_password	# for a second, better than writing into the script file
chroot /instmnt ./ldap.sh
export -n root_password
