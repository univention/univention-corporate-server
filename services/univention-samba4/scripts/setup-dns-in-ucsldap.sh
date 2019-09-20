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

## parse long options from command line arguments into shell variables
## and store binddn and bindpwd options in "$@"

. /usr/share/univention-lib/all.sh

# Bug #27001
local_is_ucr_false () { # test if UCS variable is "true" or "false"
    local value
    value="$(univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
        1|yes|on|true|enable|enabled) return 1 ;;
        0|no|off|false|disable|disabled) return 0 ;;
        *) return 2 ;;
    esac
}

sitename='Default-First-Site-Name'

optspec="h-:"
while getopts "$optspec" option; do
    case "${option}" in
	-)
	    case "${OPTARG}" in
		dc)
			dc=1
			;;
		gc)
			gc=1
			;;
		pdc)
			pdc=1
			;;
		rodc)
			rodc=1
			;;
		binddn|bindpwd|bindpwdfile)
			## store the binddn and bindpwd options in UDM_ARGV
			param=("--${OPTARG}" "${!OPTIND}")
			if [ -z "$UDM_ARGV" ]; then
				UDM_ARGV=("${param[@]}")
			else
				UDM_ARGV=("${UDM_ARGV[@]}" "${param[@]}")
			fi
			OPTIND=$((OPTIND+1))
			;;
		site|site=*)
			## allow "--site=foo" and "--site foo"
			val=${OPTARG#*=}
			if [ "$val" != "$OPTARG" ]; then
				opt=${OPTARG%=$val}
			else
				val="${!OPTIND}"
				opt="${OPTARG}"
			fi
			## store the sitename
			sitename="$val"
			OPTIND=$((OPTIND+1))
			;;
		*)
			echo "Unknown option --${OPTARG}" >&2
			;;
	    esac;;
	h|*) echo "usage: $0 [--dc|--rodc] [--gc|--rogc] [--pdc] [--site=SITENAME]"; echo 'default site is "Default-First-Site-Name"'; exit 1;;
    esac
done
set -- "${UDM_ARGV[@]}"

if [ -z "$dc" ] && [ -z "$rodc" ] && [ -z "$gc" ] && [ -z "$rogc" ] && [ -z "$pdc" ]; then
	echo "Need some option: [--dc|--rodc] [--gc|--rogc] [--pdc]"
	exit 1
fi

## The DNS-entries recommended by Samba4 provision in /var/lib/samba/private/dns/samba4.qa.zone
## need to be created in the UCS directory service for univention-bind

eval "$(univention-config-registry shell)"

# LDB_URI="ldapi:///var/lib/samba/private/ldap_priv/ldapi"	# seems to open a bit too late after samba4 startup
LDB_URI="tdb:///var/lib/samba/private/sam.ldb"

domaindn="DC=${kerberos_realm//./,DC=}"	# that's what /usr/share/pyshared/samba/provision.py uses
if ! ldbsearch -H "$LDB_URI" -b "$domaindn" -s base dn 2>/dev/null| grep -qi ^"dn: $domaindn"; then
	echo "Samba4 does not seem to be provisioned, exiting $0"
	exit 1
fi

case "${LDB_URI%%:*}" in
	ldapi|LDAPI)
		ldb_control="--extended-dn"
esac

if [ -n "$dc" ] || [ -n "$rodc" ]; then		### determine NTDS_objectGUID
	server_object_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb samAccountName="${hostname}\$" \
							serverReferenceBL | ldapsearch-wrapper | sed -n 's/^serverReferenceBL: //p' | grep -v '\\0ACNF:')
	NTDS_objectGUID=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$server_object_dn" \
							"CN=NTDS Settings" objectGUID | sed -n 's/^objectGUID: //p')
fi

IP=$(get_default_ip_address)

if local_is_ucr_false dns/register/srv_records/gc; then 
    unset gc
fi;

if local_is_ucr_false dns/register/srv_records/pdc; then 
    unset pdc
fi;

fqdn="$hostname.$domainname"

if [ -n "$dc" ]; then
	####### <Non-RODC server> #######
	## 1b9c8108-ab68-42b3-bc1a-f4269559df7e._msdcs     IN CNAME        qamaster
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add cname "$NTDS_objectGUID._msdcs" "$fqdn."

	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		###
		### ldap servers
		## _ldap._tcp              IN SRV 0 100 389        qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv ldap tcp 0 100 389 "$fqdn."
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" remove srv ldap tcp 0 100 7389 "$fqdn."
		## _ldap._tcp.dc._msdcs    IN SRV 0 100 389        qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv ldap._tcp.dc msdcs 0 100 389 "$fqdn."

		Domain_GUID="$(ldbsearch -H "$LDB_URI" -b "$domaindn" -s base "${ldb_control[@]}" objectGUID | sed -n 's/^objectGUID: //p')"
		if [ -n "$Domain_GUID" ]; then
			## _ldap._tcp.cd12388d-d1ca-45b5-a427-d91071c3b7b1.domains._msdcs          IN SRV 0 100 389 qamaster
			/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$Domain_GUID.domains" msdcs 0 100 389 "$fqdn."
		else
			echo "Error: Domain_GUID was not found!"
		fi
		Partition_GUID="$(ldbsearch -H "$LDB_URI" -b "CN=$windows_domain,CN=Partitions,CN=Configuration,$domaindn" "${ldb_control[@]}" objectGUID | sed -n 's/^objectGUID: //p')"
		if [ -n "$Partition_GUID" ]; then
			## remove false record: _ldap.PartitionGUID.domains._msdcs          IN SRV 0 100 389 qamaster
			/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" remove srv "ldap.$Partition_GUID.domains" msdcs 0 100 389 "$fqdn."
		else
			echo "Error: Partition_GUID was not found!"
		fi
	fi

	if ! local_is_ucr_false dns/register/srv_records/kerberos; then
		## TODO: the next two might collide/duplicate the ones created by 15univention-heimdal-kdc.inst
		## _kerberos._tcp          IN SRV 0 100 88         qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv kerberos tcp 0 100 88 "$fqdn."
		## _kerberos._udp          IN SRV 0 100 88         qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv kerberos udp 0 100 88 "$fqdn."
		## _kerberos._tcp.dc._msdcs        IN SRV 0 100 88 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv kerberos._tcp.dc msdcs 0 100 88 "$fqdn."
		### kpasswd
		## _kpasswd._tcp           IN SRV 0 100 464        qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv kpasswd tcp 0 100 464 "$fqdn."
		## _kpasswd._udp           IN SRV 0 100 464        qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv kpasswd udp 0 100 464 "$fqdn."
		###
	fi
	
	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		## _ldap._tcp.Default-First-Site-Name._sites               IN SRV 0 100 389 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename" sites 0 100 389 "$fqdn."
		## _ldap._tcp.Default-First-Site-Name._sites.dc._msdcs     IN SRV 0 100 389 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename._sites.dc" msdcs 0 100 389 "$fqdn."
	fi
	
	if ! local_is_ucr_false dns/register/srv_records/kerberos; then
		###
		### krb5 servers
		## _kerberos._tcp.Default-First-Site-Name._sites   IN SRV 0 100 88 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "kerberos._tcp.$sitename" sites 0 100 88 "$fqdn."
		## _kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs IN SRV 0 100 88 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "kerberos._tcp.$sitename._sites.dc" msdcs 0 100 88 "$fqdn."
		####### </Non-RODC server> #######
	fi
	
	### heimdal 'find realm for host' hack
	## TODO: also done in /usr/lib/univention-install/15univention-heimdal-kdc.inst but might be 'old' after u-s-s-base
	## _kerberos               IN TXT  SAMBA4.QA
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add txt _kerberos "$kerberos_realm"
	
fi

if [ -n "$rodc" ]; then
	## 1b9c8108-ab68-42b3-bc1a-f4269559df7e._msdcs     IN CNAME        qamaster
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add cname "$NTDS_objectGUID._msdcs" "$fqdn."

	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		###
		### ldap servers
		## _ldap._tcp.Default-First-Site-Name._sites               IN SRV 0 100 389 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename" sites 0 100 389 "$fqdn."
		## _ldap._tcp.Default-First-Site-Name._sites.dc._msdcs     IN SRV 0 100 389 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename._sites.dc" msdcs 0 100 389 "$fqdn."
	fi

	if ! local_is_ucr_false dns/register/srv_records/kerberos; then
		###
		### krb5 servers
		## _kerberos._tcp.Default-First-Site-Name._sites   IN SRV 0 100 88 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "kerberos._tcp.$sitename" sites 0 100 88 "$fqdn."
		## _kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs IN SRV 0 100 88 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "kerberos._tcp.$sitename._sites.dc" msdcs 0 100 88 "$fqdn."
	fi

fi

if [ -n "$gc" ]; then
	####### <GC server> #######
	## gc._msdcs               IN A    $IP
	if [ -n "$IP" ]; then
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-missing-zone "$domainname" add a gc._msdcs "$IP"
	fi

	##_gc._tcp                IN SRV 0 100 3268       qamaster
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv gc tcp 0 100 3268 "$fqdn."
	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		## _ldap._tcp.gc._msdcs    IN SRV 0 100 3268       qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv ldap._tcp.gc msdcs 0 100 3268 "$fqdn."
	fi

	## _gc._tcp.Default-First-Site-Name._sites IN SRV 0 100 3268       qamaster
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "gc._tcp.$sitename" sites 0 100 3268 "$fqdn."

	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		## _ldap._tcp.Default-First-Site-Name._sites.gc._msdcs     IN SRV 0 100 3268 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename._sites.gc" msdcs 0 100 3268 "$fqdn."
	fi
	####### <GC server> #######
fi

if [ -n "$rogc" ]; then
	####### <RODC GC server> #######
	## gc._msdcs               IN A    $IP
	if [ -n "$IP" ]; then
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-missing-zone "$domainname" add a gc._msdcs "$IP"
	fi

	## _gc._tcp.Default-First-Site-Name._sites IN SRV 0 100 3268       qamaster
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "gc._tcp.$sitename" sites 0 100 3268 "$fqdn."
	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		## _ldap._tcp.Default-First-Site-Name._sites.gc._msdcs     IN SRV 0 100 3268 qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv "ldap._tcp.$sitename._sites.gc" msdcs 0 100 3268 "$fqdn."
	fi
	####### <RODC GC server> #######
fi

if [ -n "$pdc" ]; then
	if ! local_is_ucr_false dns/register/srv_records/ldap; then
		## _ldap._tcp.pdc._msdcs   IN SRV 0 100 389        qamaster
		/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists "$domainname" add srv ldap._tcp.pdc msdcs 0 100 389 "$fqdn."
	fi
fi
