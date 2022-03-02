#!/bin/bash
#
# Univention Samba4
#  Migrate DNS zones from legacy position in Samba/AD LDAP
#
# Copyright 2004-2022 Univention GmbH
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

set -e
backup_dir="/var/univention-backup/samba/dns-$(date +%Y%m%d%H%M)"
logfile="/var/log/univention/migrate_legacy_dns_zones-$(date +%Y%m%d%H%M%S).log"

verbose=1
src='CN=System'
ddz='DC=DomainDnsZones'
fdz='DC=ForestDnsZones'
new='new-files'
logdir='tmp'

eval "$(ucr shell)"

if [ "$dns_backend" != "samba4" ]; then
	echo "INFO: Nothing to do, dns/backend != samba4"
	exit 0
fi

if [ "$connector_s4_mapping_dns_position" = "legacy" ]; then
	echo "INFO: connector/s4/mapping/dns/position == legacy"
echo
	echo "INFO: connector/s4/mapping/dns/position != legacy"
fi

{

zonenames=($(ldbsearch -H /var/lib/samba/private/sam.ldb -b "CN=MicrosoftDNS,${src},${samba4_ldap_base}" \
	'(&(objectClass=dnsZone)(!(DC=RootDNSServers)))' DC 2>/dev/null | sed -n 's/^dc: //Ip'))

if [ -z "${zonenames[*]}" ]; then
	echo "INFO: No dnsZone objects found under ${src}, nothing to do."
	exit 0
fi

echo "INFO: Creating backup directory: $backup_dir"
mkdir -p "$backup_dir"
mkdir -p "$backup_dir/$src"
mkdir -p "$backup_dir/$ddz"
mkdir -p "$backup_dir/$fdz"
mkdir -p "$backup_dir/$new"
mkdir -p "$backup_dir/$logdir"

## Prevent Bug #50361:
if [ "${connector_s4_mapping_dns_ignorelist//,_msdcs}" = "${connector_s4_mapping_dns_ignorelist}" ]; then
	ucr set connector/s4/mapping/dns/ignorelist="${connector_s4_mapping_dns_ignorelist},_msdcs"
fi

log() {
	if [ "$verbose" -gt 0 ]; then
		echo "$@"
	fi
}

ns_record() {
	rank="$1"
	python3 <<%EOF
from samba.provision.sambadns import NSRecord
from samba.dcerpc import dnsp
from samba.ndr import ndr_pack
import base64
ns_record = NSRecord("$hostname.$domainname", rank=dnsp.$rank)
print(base64.b64encode(ndr_pack(ns_record)))
%EOF
}

soa_record() {
	serial="$1"
	python3 <<%EOF
from samba.provision.sambadns import SOARecord
from samba.dcerpc import dnsp
from samba.ndr import ndr_pack
import base64
soa_record = SOARecord("$hostname.$domainname", "hostmaster.$domainname", serial=$serial)
print(base64.b64encode(ndr_pack(soa_record)))
%EOF
}

get_samba4_soa_serial() {
	local zone_dn
	zone_dn="$1"
	local serial
	while read -r dnsRecord; do
		serial=$(python3 <<%EOF
import base64
from samba.dcerpc import dnsp
from samba.ndr import ndr_unpack
dnsRecord = base64.b64decode('$dnsRecord')
ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
if ndrRecord.wType == dnsp.DNS_TYPE_SOA: print(ndrRecord.data.serial)
%EOF
		)
		if [ -n "$serial" ]; then
			echo "$serial"
			break
		fi
	done < <(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$zone_dn" DC=@ dnsRecord \
		| ldapsearch-wrapper | sed -n 's/^dnsRecord:: //p')
}

get_dns_soa_serial() {
	local zonename
	zonename="$1"
	dig "$zonename" SOA +short | awk '{print $3;}'
}

active_zonenames=()
if [ "$dns_backend" = "samba4" ]; then
	for zonename in "${zonenames[@]}"; do
		echo "Checking $zonename"
		## Check if DNS gives us the same SOA serial as Samba
		## Purpose: confirm that the Zone below src='CN=System'
		## is actually active
		src_zone_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
			-b "CN=MicrosoftDNS,${src},${samba4_ldap_base}" \
			"(&(objectClass=dnsZone)(DC=$zonename))" \
			distinguishedName \
			2>/dev/null | sed -n 's/^dn: //p')
		samba4_soa_serial=$(get_samba4_soa_serial "$src_zone_dn")
		dns_soa_serial=$(get_dns_soa_serial "$zonename")
		if [ "$samba4_soa_serial" != "$dns_soa_serial" ]; then
			echo "ERROR: Zone '$src_zone_dn' not active"
			continue
		fi
		active_zonenames+=("$zonename")
	done
fi

if [ -z "${active_zonenames[*]}" ]; then
	exit 0
fi

log "Active DNS Zones: ${active_zonenames[*]}"

start_services() {
	if [ "$bind9_was_running" = 1 ]; then
		echo "INFO: Starting bind9"
		service bind9 start
	fi
	if [ "$s4_connector_was_running" = 1 ]; then
		echo "INFO: Starting univention-s4-connector"
		service univention-s4-connector start
	fi
	trap - EXIT
}

trap start_services EXIT

echo "INFO: Stopping univention-s4-connector and bind9"
s4_connector_was_running=0
if service univention-s4-connector status >/dev/null; then
	s4_connector_was_running=1
	service univention-s4-connector stop || :
fi
bind9_was_running=0
if service bind9 status >/dev/null; then
	bind9_was_running=1
	service bind9 stop || :
fi

echo "INFO: Migration starts"
for zonename in "${active_zonenames[@]}"; do
	## check if destination exists and back it up
	ddz_zone_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "CN=MicrosoftDNS,${ddz},${samba4_ldap_base}" \
		-s one "(&(objectClass=dnsZone)(DC=$zonename))" \
		'*' nTSecurityDescriptor \
		| ldapsearch-wrapper \
		| sed -n 's/^dn: //p')

	old_msdcs_glue_rr_ldif=""
	if [ "$zonename" = "$domainname" ] \
		&& [ -n "$ddz_zone_dn" ]; then
		old_msdcs_glue_rr_ldif=$(ldbsearch \
			-H /var/lib/samba/private/sam.ldb \
			-b "$ddz_zone_dn" \
			-s one \
			DC=_msdcs \
			'*' nTSecurityDescriptor \
			| grep -v '^objectGUID: ' \
			| : \
			)
		echo "$old_msdcs_glue_rr_ldif" > "$backup_dir/$logdir/old_msdcs-glue-rr.ldif"
		echo "$old_msdcs_glue_rr_ldif" > "$backup_dir/$new/new_msdcs-related-records.ldif"
	fi

	if [ -n "$ddz_zone_dn" ]; then
		echo "INFO: Backing up target zone: $ddz_zone_dn"
		old_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
			'*' nTSecurityDescriptor \
			-b "$ddz_zone_dn" \
			)
		echo "INFO: Saving to: $backup_dir/$ddz/$ddz_zone_dn.ldif"
		echo "$old_ldif" > "$backup_dir/$ddz/$ddz_zone_dn.ldif"

		echo "INFO: Cleaning up target zone: $ddz_zone_dn"
		ldbdel -H /var/lib/samba/private/sam.ldb \
			--recursive "$ddz_zone_dn"
	fi

	src_zone_dn="DC=${zonename},CN=MicrosoftDNS,${src},${samba4_ldap_base}"
	src_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "$src_zone_dn" \
		-s base \
		'*' nTSecurityDescriptor \
		| ldapsearch-wrapper)
	new_ldif=$(echo "$src_ldif" \
		| grep -v '^objectGUID: ' \
		| sed "s/CN=MicrosoftDNS,${src},/CN=MicrosoftDNS,${ddz},/")

	echo "$new_ldif" > "$backup_dir/$new/new_$zonename-records.ldif"

	dst_zone_dn=$(sed -n 's/^dn: //p' <<<"$new_ldif")
	echo "INFO: Creating zone: $dst_zone_dn"
	ldbadd -H /var/lib/samba/private/sam.ldb <<<"$new_ldif" \
	| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :

	## Skip _msdcs subzone records in this:
	src_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "$src_zone_dn" \
		'(&(objectClass=dnsNode)(!(DC=*._msdcs)))' \
		'*' nTSecurityDescriptor \
		)
	new_ldif=$(echo "$src_ldif" \
		| grep -v '^objectGUID: ' \
		| sed "s/,CN=MicrosoftDNS,${src},/,CN=MicrosoftDNS,${ddz},/")

	echo "" >> "$backup_dir/$new/new_$zonename-records.ldif"
	echo "$new_ldif" >> "$backup_dir/$new/new_$zonename-records.ldif"

	echo "INFO: Copying records to zone: $dst_zone_dn"
	ldbadd -H /var/lib/samba/private/sam.ldb <<<"$new_ldif" \
	| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :

	echo "INFO: Cleaning up S4-Connector pre-map table \"DN Mapping CON\" and \"DN Mapping UCS\""
	while read -r src_node_dn; do
		echo "INFO: Delete '$src_node_dn' from S4-Connector cache"
		sqlite3 /etc/univention/connector/s4internal.sqlite \
			"delete from \"DN Mapping CON\" where key='$src_node_dn'; delete from \"DN Mapping UCS\" where value='$src_node_dn';"
	done < <(sed -n 's/^dn: //p' <<<"$src_ldif")

	if [ "$zonename" != "$domainname" ]; then
		continue
	fi

	msdcs_zonename="_msdcs.$zonename"
	## move _msdcs to ForestDnsZones
	## check if destination exists and back it up
	fdz_zone_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "CN=MicrosoftDNS,${fdz},${samba4_ldap_base}" \
		-s one "(&(objectClass=dnsZone)(DC=$msdcs_zonename))" \
		'*' nTSecurityDescriptor \
		| ldapsearch-wrapper \
		| sed -n 's/^dn: //p')

	old_zone_container_ldif=""
	old_soa_ldif=""
	if [ -n "$fdz_zone_dn" ]; then
		echo "INFO: Backing up target zone: $fdz_zone_dn"
		old_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
			-b "$fdz_zone_dn" \
			'*' nTSecurityDescriptor \
			)
		echo "INFO: Saving to: $backup_dir/$fdz/$fdz_zone_dn.ldif"
		echo "$old_ldif" > "$backup_dir/$fdz/$fdz_zone_dn.ldif"

		old_zone_container_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
			-b "$fdz_zone_dn" -s base \
			'*' nTSecurityDescriptor \
			| grep -v '^objectGUID: ' \
			| : \
			)
		echo "$old_zone_container_ldif" > "$backup_dir/$logdir/old_msdcs-zone-container.ldif"

		echo "" >> "$backup_dir/$new/new_msdcs-related-records.ldif"
		echo "$old_zone_container_ldif" >> "$backup_dir/$new/new_msdcs-related-records.ldif"

		old_soa_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
			-b "$fdz_zone_dn" -s one DC=@ \
			'*' nTSecurityDescriptor \
			| grep -v '^objectGUID: '\
			| : \
			)
		echo "$old_soa_ldif" > "$backup_dir/$logdir/old_msdcs-soa-rr.ldif"

		echo "" >> "$backup_dir/$new/new_msdcs-related-records.ldif"
		echo "$old_soa_ldif" >> "$backup_dir/$new/new_msdcs-related-records.ldif"

		echo "INFO: Cleaning up target zone: $fdz_zone_dn"
		ldbdel -H /var/lib/samba/private/sam.ldb \
			--recursive "$fdz_zone_dn"
	fi
	
	fdz_zone_dn="DC=${msdcs_zonename},CN=MicrosoftDNS,${fdz},${samba4_ldap_base}"
	if [ -n "$(sed -n 's/^dn: //p' <<<"$old_zone_container_ldif")" ]; then
		dst_zone_dn=$(sed -n 's/^dn: //p' <<<"$old_zone_container_ldif")
		echo "INFO: Restoring zone: $dst_zone_dn"
		ldbadd -H /var/lib/samba/private/sam.ldb <<<"$old_zone_container_ldif" \
		| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :
	else
		echo "INFO: Creating zone: $fdz_zone_dn"
		ldbadd -H /var/lib/samba/private/sam.ldb <<%EOF
dn: $fdz_zone_dn
objectClass: dnsZone
%EOF
	fi
	if [ -n "$(sed -n 's/^dn: //p' <<<"$old_soa_ldif")" ]; then
		dst_dn=$(sed -n 's/^dn: //p' <<<"$old_soa_ldif")
		echo "INFO: Restoring SOA: $dst_dn"
		ldbadd -H /var/lib/samba/private/sam.ldb <<<"$old_soa_ldif" \
		| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :
	else
		echo "INFO: Creating SOA: DC=@,$fdz_zone_dn"
		samba4_soa_serial=$(get_samba4_soa_serial "$src_zone_dn")
		dnsRecord_soa=$(soa_record "$samba4_soa_serial")
		dnsRecord_ns=$(ns_record "DNS_RANK_ZONE")
		ldbadd -H /var/lib/samba/private/sam.ldb <<%EOF
dn: DC=@,$fdz_zone_dn
objectClass: dnsNode
dnsRecord:: $dnsRecord_soa
dnsRecord:: $dnsRecord_ns
%EOF
	fi
	

	## Consider only _msdcs subzone records in this:
	src_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "$src_zone_dn" \
		'(&(objectClass=dnsNode)(DC=*._msdcs))' \
		'*' nTSecurityDescriptor \
		)
	new_ldif=$(echo "$src_ldif" \
		| ldapsearch-wrapper \
		| grep -v '^objectGUID: ' \
		| grep -v '^distinguishedName: ' \
		| grep -v '^name: ' \
		| sed "s/^dn: \(.*\)._msdcs,DC=$zonename,CN=MicrosoftDNS,$src,/dn: \1,DC=$msdcs_zonename,CN=MicrosoftDNS,$fdz,/" \
		| sed "s/^DC: \(.*\)._msdcs$/DC: \1/I")
	echo "$new_ldif" > "$backup_dir/$logdir/new_msdcs-zone.ldif"

	echo "" >> "$backup_dir/$new/new_msdcs-related-records.ldif"
	echo "$new_ldif" >> "$backup_dir/$new/new_msdcs-related-records.ldif"

	dst_zone_dn="DC=$msdcs_zonename,CN=MicrosoftDNS,$fdz,${samba4_ldap_base}"
	echo "INFO: Copying records to zone: $dst_zone_dn"
	ldbadd -H /var/lib/samba/private/sam.ldb <<<"$new_ldif" \
	| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :

	echo "INFO: Cleaning up S4-Connector pre-map table \"DN Mapping CON\" and \"DN Mapping UCS\""
	while read -r src_node_dn; do
		echo "INFO: Delete '$src_node_dn' from S4-Connector cache"
		sqlite3 /etc/univention/connector/s4internal.sqlite \
			"delete from \"DN Mapping CON\" where key='$src_node_dn'; delete from \"DN Mapping UCS\" where value='$src_node_dn';"
	done < <(sed -n 's/^dn: //p' <<<"$src_ldif")

	if [ -n "$old_msdcs_glue_rr_ldif" ]; then
		dst_dn=$(sed -n 's/^dn: //p' <<<"$old_msdcs_glue_rr_ldif")
		echo "INFO: Restoring glue record: $dst_dn"
		ldbadd -H /var/lib/samba/private/sam.ldb <<<"$old_msdcs_glue_rr_ldif" \
		| grep -v 'ndr_pull_relative_ptr1 rel_offset' | :
	else
		dst_dn="$DC=_msdcs,DC=$zonename,CN=MicrosoftDNS,${ddz},${samba4_ldap_base}"
		echo "INFO: Creating glue record: $dst_dn"
		dnsRecord=$(ns_record "DNS_RANK_NS_GLUE")
		ldbadd -H /var/lib/samba/private/sam.ldb <<%EOF
dn: $dst_dn
objectClass: dnsNode
dnsRecord:: $dnsRecord
%EOF
	fi
done

for zonename in "${active_zonenames[@]}"; do
	src_zone_dn="DC=${zonename},CN=MicrosoftDNS,${src},${samba4_ldap_base}"
	src_ldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb \
		-b "$src_zone_dn" \
		'*' nTSecurityDescriptor \
		)
	echo "$src_ldif" > "$backup_dir/$src/$src_zone_dn.ldif"

	ldbdel -H /var/lib/samba/private/sam.ldb \
		--recursive \
		"DC=${zonename},CN=MicrosoftDNS,${src},${samba4_ldap_base}"
done

if [ "$connector_s4_mapping_dns_position" = "legacy" ]; then
	ucr unset connector/s4/mapping/dns/position
fi

set +e
samba-tool dbcheck --fix --yes || true
start_services
nscd -i hosts

samba_dnsupdate
echo "INFO: Migration finished"
} 2>&1 | tee "$logfile"

[ -d "$backup_dir/$logdir" ] && cp "$logfile" "$backup_dir/$logdir"
