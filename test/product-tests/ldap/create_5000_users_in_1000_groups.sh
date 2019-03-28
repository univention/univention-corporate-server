#!/bin/bash

set -e

. utils.sh
. /usr/share/ucs-test/lib/samba.sh
eval "$(ucr shell ldap/base connector/s4/poll/sleep connector/s4/retryrejected)"

### TODO: Define current limits
CONNECTOR_WAIT_CYCLES=2
CONNECTOR_WAIT_DURATION_PER_SYNC=1
CONNECTOR_WAIT_TIME=$((CONNECTOR_WAIT_CYCLES * (CONNECTOR_WAIT_DURATION_PER_SYNC + connector_s4_poll_sleep * (1 + connector_s4_retryrejected))))
MAX_SECONDS_USER_CREATE=$((45 * 60))
MAX_SECONDS_SAMBA_USER_CREATE=$((160 * 60 + CONNECTOR_WAIT_TIME))
MAX_SECONDS_GROUP_CREATE=$((10 * 60))
MAX_SECONDS_SAMBA_GROUP_CREATE=$((30 * 60 + CONNECTOR_WAIT_TIME))

TESTUSER_PREFIX="testuser"
TESTGROUP_PREFIX="gp"

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

	local num_users="${1:-5000}"
	local num_groups="${2:-1000}"
	local i

	for((i=0; i<num_users; i++)); do
		udm users/user create --position "cn=users,$ldap_base" \
			--set username="$TESTUSER_PREFIX$NEXT_USERNUMBER" \
			--set firstname="Test$NEXT_USERNUMBER" \
			--set lastname="User$NEXT_USERNUMBER" \
			--set password=univention
		((++NEXT_USERNUMBER))
	done

	for((i=0; i<num_groups; i++)); do
		c=$(( FIRST_USERNUMBER + (i*50)%num_users ))
		udm groups/group create --set "name=$TESTGROUP_PREFIX$NEXT_GROUPNUMBER" \
			--position "cn=groups,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$c,cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+1)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+2)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+3)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+4)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+5)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+6)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+7)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+8)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+9)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+10)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+11)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+12)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+13)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+14)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+15)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+16)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+17)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+18)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+19)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+20)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+21)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+22)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+23)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+24)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+25)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+26)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+27)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+28)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+29)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+30)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+31)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+32)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+33)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+34)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+35)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+36)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+37)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+38)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+39)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+40)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+41)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+42)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+43)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+44)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+45)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+46)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+47)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+48)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+49)),cn=users,$ldap_base" 
		((++NEXT_GROUPNUMBER))
	done
}

create_group_with_5000_members() {
	local i
	local group_number

	group_number=$((++NEXT_GROUPNUMBER))
	udm groups/group create --set "name=$TESTGROUP_PREFIX$group_number" \
		--position "cn=groups,$ldap_base"

	local batch_size=100
	for((i=0; i<batch_size; i++)); do
		c=$(( FIRST_USERNUMBER + (i*50) ))
		udm groups/group modify \
			--dn "cn=$TESTGROUP_PREFIX$group_number,cn=groups,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$c,cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+1)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+2)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+3)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+4)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+5)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+6)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+7)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+8)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+9)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+10)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+11)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+12)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+13)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+14)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+15)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+16)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+17)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+18)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+19)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+20)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+21)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+22)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+23)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+24)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+25)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+26)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+27)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+28)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+29)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+30)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+31)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+32)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+33)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+34)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+35)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+36)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+37)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+38)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+39)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+40)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+41)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+42)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+43)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+44)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+45)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+46)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+47)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+48)),cn=users,$ldap_base" \
			--append users="uid=$TESTUSER_PREFIX$((c+49)),cn=users,$ldap_base" 
	done
}

create_5000_users_plus_drs_replication() {	## TODO: Adjust numbers back to 5000 users:
	measure_duration --limit="$MAX_SECONDS_USER_CREATE" create_5000_users_distributed_in_1000_groups 500 100
	local last_user_number=$((NEXT_USERNUMBER - 1))
	local ldap_filter="(sAMAccountName=$TESTUSER_PREFIX$last_user_number)"
	wait_for_drs_replication "$ldap_filter"
	wait_for_samba4_idmap_listener "$ldap_filter"
}

measure_time_for_create_5000_users_distributed_in_1000_groups() {
	echo "Measure time to create 5000 users distributed in 1000 groups:"
	measure_duration --limit="$MAX_SECONDS_SAMBA_USER_CREATE" create_5000_users_plus_drs_replication
}

create_group_with_5000_members_plus_drs_replication() {
	local last_user_number=$((NEXT_USERNUMBER - 1))
	local userdn
	userdn=$(univention-s4search "(sAMAccountName=$TESTUSER_PREFIX$last_user_number)" 1.1 | sed -n 's/^dn: //p')

	measure_duration --limit="$MAX_SECONDS_GROUP_CREATE" create_group_with_5000_members

	local last_group_number=$((NEXT_GROUPNUMBER - 1))
	wait_for_drs_replication "(&(sAMAccountName=gp$last_group_number)(member=$userdn))"
}

measure_time_for_create_group_with_5000_members() {
	echo "Measure time to create group with 5000 members:"
	measure_duration --limit="$MAX_SECONDS_SAMBA_GROUP_CREATE" create_group_with_5000_members_plus_drs_replication
}
