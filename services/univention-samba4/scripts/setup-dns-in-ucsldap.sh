#!/bin/bash
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

## The DNS-entries recommended by Samba4 provision in /var/lib/samba/private/dns/samba4.qa.zone
## need to be created in the UCS directory service for univention-bind

SCRIPTDIR=/usr/share/univention-samba4/scripts

LDB_MODULES_PATH=/usr/lib/ldb; export LDB_MODULES_PATH;		## currently necessary for ldbtools

eval "$(univention-config-registry shell)"

# LDB_URI="ldapi:///var/lib/samba/private/ldap_priv/ldapi"	# seems to open a bit too late after samba4 startup
LDB_URI="tdb:///var/lib/samba/private/sam.ldb"

domaindn="DC=${kerberos_realm/./,DC=}"	# that's what /usr/share/pyshared/samba/provision.py uses
if ! ldbsearch -H "$LDB_URI" -b $domaindn -s base dn 2>/dev/null| grep -qi ^"dn: $domaindn"; then
	echo "Samba4 does not seem to be provisioned, exiting $0"
	exit 1
fi

server_object_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb samAccountName="${hostname}\$" \
							serverReferenceBL | ldapsearch-wrapper | sed -n 's/^serverReferenceBL: \(.*\)/\1/p')
NTDS_objectGUID=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$server_object_dn" \
							"CN=NTDS Settings" objectGUID | sed -n 's/^objectGUID: \(.*\)/\1/p')

case "${LDB_URI%%:*}" in
	ldapi|LDAPI)
		ldb_control="--extended-dn"
esac

Partition_GUID="$(ldbsearch -H "$LDB_URI" -b "CN=$windows_domain,CN=Partitions,CN=Configuration,$domaindn" $ldb_control objectGUID | sed -n 's/^objectGUID: \(.*\)/\1/p')"

## gc._msdcs               IN A    $interfaces_eth0_address
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-missing-zone $domainname add a gc._msdcs $interfaces_eth0_address

## 1b9c8108-ab68-42b3-bc1a-f4269559df7e._msdcs     IN CNAME        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add cname $NTDS_objectGUID._msdcs $hostname.$domainname.

###
### global catalog servers
##_gc._tcp                IN SRV 0 100 3268       qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv gc tcp 0 100 3268 $hostname.$domainname.
## _gc._tcp.Default-First-Site-Name._sites IN SRV 0 100 3268       qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv gc._tcp.Default-First-Site-Name sites 0 100 3268 $hostname.$domainname.
## _ldap._tcp.gc._msdcs    IN SRV 0 100 3268       qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.gc msdcs 0 100 3268 $hostname.$domainname.
## _ldap._tcp.Default-First-Site-Name._sites.gc._msdcs     IN SRV 0 100 3268 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.Default-First-Site-Name._sites.gc msdcs 0 100 3268 $hostname.$domainname.

###
### ldap servers
## _ldap._tcp              IN SRV 0 100 389        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap tcp 0 100 389 $hostname.$domainname.
## _ldap._tcp.dc._msdcs    IN SRV 0 100 389        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.dc msdcs 0 100 389 $hostname.$domainname.
## _ldap._tcp.pdc._msdcs   IN SRV 0 100 389        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.pdc msdcs 0 100 389 $hostname.$domainname.
if [ -n "$Partition_GUID" ]; then
	## _ldap._tcp.cd12388d-d1ca-45b5-a427-d91071c3b7b1.domains._msdcs          IN SRV 0 100 389 qamaster
	/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap.$Partition_GUID.domains msdcs 0 100 389 $hostname.$domainname.
else
	echo "Error: Partition_GUID was not found!"
fi

## _ldap._tcp.Default-First-Site-Name._sites               IN SRV 0 100 389 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.Default-First-Site-Name sites 0 100 389 $hostname.$domainname.
## _ldap._tcp.Default-First-Site-Name._sites.dc._msdcs     IN SRV 0 100 389 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv ldap._tcp.Default-First-Site-Name._sites.dc msdcs 0 100 389 $hostname.$domainname.

###
### krb5 servers
## _kerberos._tcp.dc._msdcs        IN SRV 0 100 88 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos._tcp.dc msdcs 0 100 88 $hostname.$domainname.
## _kerberos._tcp.Default-First-Site-Name._sites   IN SRV 0 100 88 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos._tcp.Default-First-Site-Name sites 0 100 88 $hostname.$domainname.
## _kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs IN SRV 0 100 88 qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos._tcp.Default-First-Site-Name._sites.dc msdcs 0 100 88 $hostname.$domainname.
## TODO: the next two might collide/duplicate the ones created by 15univention-heimdal-kdc.inst
## _kerberos._tcp          IN SRV 0 100 88         qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos tcp 0 100 88 $hostname.$domainname.
## _kerberos._udp          IN SRV 0 100 88         qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos udp 0 100 88 $hostname.$domainname.
### MIT kpasswd likes to lookup this name on password change
## _kerberos-master._tcp           IN SRV 0 100 88         qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos-master tcp 0 100 88 $hostname.$domainname.
## _kerberos-master._udp           IN SRV 0 100 88         qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kerberos-master udp 0 100 88 $hostname.$domainname.
###
### kpasswd
## _kpasswd._tcp           IN SRV 0 100 464        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kpasswd tcp 0 100 464 $hostname.$domainname.
## _kpasswd._udp           IN SRV 0 100 464        qamaster
/usr/share/univention-admin-tools/univention-dnsedit $@ --ignore-exists $domainname add srv kpasswd udp 0 100 464 $hostname.$domainname.
###
### heimdal 'find realm for host' hack
## TODO: also done in /usr/lib/univention-install/15univention-heimdal-kdc.inst but might be 'old' after u-s-s-base
## _kerberos               IN TXT  SAMBA4.QA
/usr/share/univention-directory-manager-tools/univention-dnsedit $@ --ignore-exists $domainname add txt _kerberos $kerberos_realm

