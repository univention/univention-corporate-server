#!/bin/dash
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

LDB_MODULES_PATH=/usr/lib/ldb; export LDB_MODULES_PATH;		## currently necessary for ldbtools

eval "$(univention-config-registry shell windows/domain samba4/ldap/base ldap/hostdn)"

host gc._msdcs

## retrive DC specific GUID
samba4servicedcs=$(ldapsearch -ZZ -LLL -D "$ldap_hostdn" -y /etc/machine.secret "(&(univentionService=Samba 4)(objectClass=univentionDomainController))" cn | sed -n 's/^cn: \(.*\)/\1/p')      ## currently there is no u-d-m module computers/dc

for s4dc in $samba4servicedcs; do
	server_object_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb samAccountName="${s4dc}\$" \
							serverReferenceBL | ldapsearch-wrapper | sed -n 's/^serverReferenceBL: \(.*\)/\1/p')
	NTDS_objectGUID=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$server_object_dn" \
							"CN=NTDS Settings" objectGUID | sed -n 's/^objectGUID: \(.*\)/\1/p')
	host -t cname $NTDS_objectGUID._msdcs
done

## retrive domain partition GUID
Partition_GUID="$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "CN=$windows_domain,CN=Partitions,CN=Configuration,$samba4_ldap_base" $ldb_control objectGUID | sed -n 's/^objectGUID: \(.*\)/\1/p')"


cat << %EOF | while read rec proto; do host -t srv "_$rec._$proto"; done
gc tcp
gc._tcp.Default-First-Site-Name sites
ldap._tcp.gc msdcs
ldap._tcp.Default-First-Site-Name._sites.gc msdcs
ldap tcp
ldap._tcp.dc msdcs
ldap._tcp.pdc msdcs
ldap.$Partition_GUID.domains msdcs
ldap._tcp.Default-First-Site-Name sites
ldap._tcp.Default-First-Site-Name._sites.dc msdcs
kerberos._tcp.dc msdcs
kerberos._tcp.Default-First-Site-Name sites
kerberos._tcp.Default-First-Site-Name._sites.dc msdcs
kerberos tcp
kerberos udp
kerberos-master tcp
kerberos-master udp
kpasswd tcp
kpasswd udp
%EOF
host -t txt _kerberos

exit 0

_kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs

for srvrec in
host -t srv _kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs

