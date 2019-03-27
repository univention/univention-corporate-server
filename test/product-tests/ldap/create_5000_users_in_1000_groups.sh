#!/bin/bash

set -e

. /usr/share/ucs-test/lib/samba.sh
eval "$(ucr shell ldap/base)"

### TODO: Define current limits
CONNECTOR_WAIT_INTERVAL=12
CONNECTOR_WAIT_SLEEP=5
CONNECTOR_WAIT_TIME=$((CONNECTOR_WAIT_SLEEP * CONNECTOR_WAIT_INTERVAL))
MAX_SECONDS_USER_CREATE=$((2 * 3600))
MAX_SECONDS_SAMBA_USER_CREATE=$((128 * 3600 + CONNECTOR_WAIT_TIME))
MAX_SECONDS_GROUP_CREATE=$((1 * 1800))
MAX_SECONDS_SAMBA_GROUP_CREATE=$((128 * 3600 + CONNECTOR_WAIT_TIME))

FIRST_USERNUMBER=1000
FIRST_GROUPNUMBER=1000
## global counters
NEXT_USERNUMBER="$FIRST_USERNUMBER"
NEXT_GROUPNUMBER="$FIRST_GROUPNUMBER"

create_5000_users_distributed_in_1000_groups() {
	## Create 5000 user accounts
	## Create 1000 group objects
	## 50 users per group
	## Each user ends up in 10 groups

	local user_prefix="${1:-testuser}"
	local group_prefix="gp"
	local num_users="${2:5000}"
	local num_groups="${3:1000}"
	local i

	for((i=0; i<num_users; i++)); do
		udm users/user create --position "cn=users,$ldap_base" \
			--set username="$user_prefix$NEXT_USERNUMBER" \
			--set firstname="Test$NEXT_USERNUMBER" \
			--set lastname="User$NEXT_USERNUMBER" \
			--set password=univention
		((++NEXT_USERNUMBER))
	done

	for((i=0; i<num_groups; i++)); do
		c=$(( FIRST_USERNUMBER + (i*50)%num_users ))
		udm groups/group create --set "name=$group_prefix$NEXT_GROUPNUMBER" \
			--position "cn=groups,$ldap_base" \
			--append users="uid=$user_prefix$c,cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+1)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+2)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+3)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+4)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+5)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+6)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+7)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+8)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+9)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+10)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+11)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+12)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+13)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+14)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+15)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+16)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+17)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+18)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+19)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+20)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+21)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+22)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+23)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+24)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+25)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+26)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+27)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+28)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+29)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+30)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+31)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+32)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+33)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+34)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+35)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+36)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+37)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+38)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+39)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+40)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+41)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+42)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+43)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+44)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+45)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+46)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+47)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+48)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+49)),cn=users,$ldap_base" 
		((++NEXT_GROUPNUMBER))
	done
}

create_group_with_5000_members() {
	local user_prefix="${1:-testuser}"
	local group_prefix="gp"
	local i
	local group_number

	group_number=$((++NEXT_GROUPNUMBER))
	udm groups/group create --set "name=$group_prefix$group_number" \
		--position "cn=groups,$ldap_base"

	local batch_size=100
	for((i=0; i<batch_size; i++)); do
		c=$(( FIRST_USERNUMBER + (i*50) ))
		udm groups/group modify \
			--dn "cn=$group_prefix$group_number,cn=groups,$ldap_base" \
			--append users="uid=$user_prefix$c,cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+1)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+2)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+3)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+4)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+5)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+6)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+7)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+8)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+9)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+10)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+11)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+12)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+13)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+14)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+15)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+16)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+17)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+18)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+19)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+20)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+21)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+22)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+23)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+24)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+25)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+26)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+27)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+28)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+29)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+30)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+31)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+32)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+33)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+34)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+35)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+36)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+37)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+38)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+39)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+40)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+41)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+42)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+43)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+44)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+45)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+46)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+47)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+48)),cn=users,$ldap_base" \
			--append users="uid=$user_prefix$((c+49)),cn=users,$ldap_base" 
	done
}

measure_duration() {
	local limit
	## poor mans option parsing
	limit="${1#--limit=}"
	if [ "$1" != "$limit" ]; then
		unset limit ## ignore limit for now. TODO: determine current limits
		shift
	else
		unset limit
	fi

	local operation="$1"
	local timestamp_start
	local timestamp_end
	local duration

	eval "$(ucr shell ldap/base)"

	timestamp_start=$(date +%Y%m%d%H%M%S)
	echo -n "START $operation AT: $timestamp_start"

	"$@"

	timestamp_end=$(date +%Y%m%d%H%M%S)
	echo -n "END $operation AT: $timestamp_end"

	duration=$((timestamp_start - timestamp_end))
	echo "INFO: $operation took $duration seconds"
	if [ -n "$limit" ] && [ "$duration" -gt "$limit" ]; then
		echo "ERROR: $operation took too long (allowed time: $limit seconds)"
	fi
}

create_5000_users_plus_drs_replication() {
	measure_duration --limit="$MAX_SECONDS_USER_CREATE" create_5000_users_distributed_in_1000_groups
	local last_user_number=$((NEXT_USERNUMBER - 1))
	local ldap_filter="(sAMAccountName=testuser$last_user_number)"
	wait_for_drs_replication "$ldap_filter"
	wait_for_samba4_idmap_listener "$ldap_filter"
}

measure_time_for_create_5000_users_distributed_in_100_groups() {
	echo "Measure time to create 5000 users distributed in 1000 groups:"
	measure_duration --limit="$MAX_SECONDS_SAMBA_USER_CREATE" create_5000_users_plus_drs_replication
}

create_group_with_5000_members_plus_drs_replication() {
	local last_user_number=$((NEXT_USERNUMBER - 1))
	local userdn
	userdn=$(univention-s4search "(sAMAccountName=testuser$last_user_number)" 1.1 | sed -n 's/^dn: //p')

	measure_duration --limit="$MAX_SECONDS_GROUP_CREATE" create_group_with_5000_members

	local last_group_number=$((NEXT_GROUPNUMBER - 1))
	wait_for_drs_replication "(&(sAMAccountName=gp$last_group_number)(member=$userdn))"
}

measure_time_for_create_group_with_5000_members() {
	echo "Measure time to create group with 5000 members:"
	measure_duration --limit="$MAX_SECONDS_SAMBA_GROUP_CREATE" create_group_with_5000_members_plus_drs_replication
}
