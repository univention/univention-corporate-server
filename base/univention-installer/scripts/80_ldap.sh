#!/bin/sh
#
# Univention Installer
#  setup required user accounts
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring LDAP server")" >&9

. /tmp/installation_profile

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

cat >>/instmnt/ldap.sh <<__EOT__


if [ "$server_role" = "domaincontroller_master" ]; then
    echo '__MSG__:Configuring LDAP' >&9

	eval "\$(univention-config-registry shell)"

	echo "Create User Administrator"
	# mailPrimaryAddress is required on ox systems
	if [ -n "$ox_primary_maildomain" ] ; then
		univention-directory-manager users/user create --position="cn=users,\$ldap_base" --set mailPrimaryAddress="administrator@$ox_primary_maildomain" --set firstname="Admin" --set username=Administrator --set sambaRID=500 --set unixhome=/home/Administrator --set lastname=Administrator --set password="\$root_password" --set primaryGroup="cn=Domain Admins,cn=groups,\$ldap_base" --policy-reference "cn=default-admins,cn=admin-settings,cn=users,cn=policies,\$ldap_base"
	else	
		univention-directory-manager users/user create --position="cn=users,\$ldap_base" --set username=Administrator --set sambaRID=500 --set unixhome=/home/Administrator --set lastname=Administrator --set password="\$root_password" --set primaryGroup="cn=Domain Admins,cn=groups,\$ldap_base" --policy-reference "cn=default-admins,cn=admin-settings,cn=users,cn=policies,\$ldap_base"
	fi
	unset root_password
	univention-directory-manager groups/group modify --dn "cn=DC Backup Hosts,cn=groups,\$ldap_base" --append users="uid=Administrator,cn=users,\$ldap_base"
	univention-directory-manager groups/group modify --dn "cn=Domain Users,cn=groups,\$ldap_base" --append users="uid=Administrator,cn=users,\$ldap_base"

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
unset root_password
