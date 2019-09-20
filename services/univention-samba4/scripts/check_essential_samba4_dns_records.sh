#!/bin/bash
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

eval "$(univention-config-registry shell windows/domain samba4/ldap/base ldap/hostdn domainname)"

Domain_GUID="$(ldbsearch -H /var/lib/samba/private/sam.ldb -s base objectGUID | sed -n 's/^objectGUID: \(.*\)/\1/p')"

## Now lookup DNS entries
host "gc._msdcs.$domainname"
cat << %EOF | while read rec proto; do host -t srv "_$rec._$proto.$domainname"; done
gc tcp
ldap._tcp.gc msdcs
ldap tcp
ldap._tcp.dc msdcs
ldap._tcp.pdc msdcs
ldap._tcp.$Domain_GUID.domains msdcs
kerberos._tcp.dc msdcs
kerberos tcp
kerberos udp
kpasswd tcp
kpasswd udp
%EOF


## retrieve DC specific GUID
NTDS_objectGUIDs=()
sites=()
samba4servicedcs=$(ldapsearch -ZZ -LLL -D "$ldap_hostdn" -y /etc/machine.secret "(&(univentionService=Samba 4)(objectClass=univentionDomainController))" cn | ldapsearch-wrapper | sed -n 's/^cn: \(.*\)/\1/p')      ## currently there is no u-d-m module computers/dc

for s4dc in $samba4servicedcs; do
	server_object_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb samAccountName="${s4dc}\$" \
							serverReferenceBL | ldapsearch-wrapper | sed -n 's/^serverReferenceBL: \(.*\)/\1/p')
	if [ -z "$server_object_dn" ]; then
		continue
	fi
	NTDS_objectGUID=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$server_object_dn" \
							"CN=NTDS Settings" objectGUID | ldapsearch-wrapper | sed -n 's/^objectGUID: \(.*\)/\1/p')
	NTDS_objectGUIDs+=($NTDS_objectGUID)

	## Determine sitename
	sitename=$(echo "$server_object_dn" | sed -n 's/[^,]*,CN=Servers,CN=\([^,]*\),CN=Sites,CN=Configuration,.*/\1/p')

	if [ -n "$sitename" ]; then
		echo "Located DC '$s4dc' in site '$sitename'"
	else
		sitename="Default-First-Site-Name"
		echo "Failed to determine site of local DC, using default '$sitename'"
	fi

	found=0
	for site in "${sites[@]}"; do
		if [ "$site" = "$sitename" ]; then
			found=1
			break
		fi
	done

	if [ "$found" != "1" ]; then
		sites+=($sitename)
	fi
done

for NTDS_objectGUID in "${NTDS_objectGUIDs[@]}"; do
	host -t cname "$NTDS_objectGUID._msdcs.$domainname"
done

for sitename in "${sites[@]}"; do
	echo "## Records for site $sitename:"
	cat <<-%EOF | while read rec proto; do host -t srv "_$rec._$proto.$domainname"; done
	ldap._tcp.$sitename sites
	ldap._tcp.$sitename._sites.dc msdcs
	kerberos._tcp.$sitename sites
	kerberos._tcp.$sitename._sites.dc msdcs
	%EOF
	echo "## Optional GC Records for site $sitename:"
	cat <<-%EOF | while read rec proto; do host -t srv "_$rec._$proto.$domainname"; done
	gc._tcp.$sitename sites
	ldap._tcp.$sitename._sites.gc msdcs
	%EOF
done

output=$(host -t txt _kerberos 2>&1)
if [ $? = 0 ]; then
	echo "$output"
else
	echo "No _kerberos TXT record (ok)"
fi

exit 0

