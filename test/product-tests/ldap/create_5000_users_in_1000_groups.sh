#!/bin/bash

set -e

create_5000_users_distributed_in_100_groups() {
	## 50 users per group
	## Each user ends up in 10 groups

	eval "$(ucr shell)"

	echo "USER CREATE START"
	date

	## Create 5000 user accounts
	num_users=5000
	first_usernumber=1000

	for((i=0; i<$num_users; i++)); do
		user_number=$(($first_usernumber + $i))
		udm users/user create --position "cn=users,$ldap_base" \
			--set username="testuser$user_number" \
			--set firstname="Test$user_number" \
			--set lastname="User$user_number" \
			--set password=univention
	done

	## Create 1000 group objects
	num_groups=1000
	first_groupnumber=1000
	for((i=0; i<$num_groups; i++)); do
		c=$(( $first_usernumber + ($i*50)%$num_users ))
		group_number=$(($first_groupnumber + $i))
		udm groups/group create --set "name=gp$group_number" \
			--position "cn=groups,$ldap_base" \
			--append users="uid=testuser$c,cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+1)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+2)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+3)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+4)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+5)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+6)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+7)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+8)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+9)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+10)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+11)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+12)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+13)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+14)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+15)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+16)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+17)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+18)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+19)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+20)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+21)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+22)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+23)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+24)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+25)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+26)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+27)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+28)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+29)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+30)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+31)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+32)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+33)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+34)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+35)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+36)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+37)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+38)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+39)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+40)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+41)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+42)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+43)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+44)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+45)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+46)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+47)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+48)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+49)),cn=users,$ldap_base" 
	done
	date
	echo "USER CREATE END"
}

create_group_with_5000_members() {
	eval "$(ucr shell)"

	echo "GROUP CREATE START"
	date

	group_number=2000
	udm groups/group create --set "name=gp$group_number" \
		--position "cn=groups,$ldap_base"

	first_usernumber=1000
	for((i=0; i<100; i++)); do
		c=$(( $first_usernumber + ($i*50) ))
		udm groups/group modify \
			--dn "cn=gp$group_number,cn=groups,$ldap_base" \
			--append users="uid=testuser$c,cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+1)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+2)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+3)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+4)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+5)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+6)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+7)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+8)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+9)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+10)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+11)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+12)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+13)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+14)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+15)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+16)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+17)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+18)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+19)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+20)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+21)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+22)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+23)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+24)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+25)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+26)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+27)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+28)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+29)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+30)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+31)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+32)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+33)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+34)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+35)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+36)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+37)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+38)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+39)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+40)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+41)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+42)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+43)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+44)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+45)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+46)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+47)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+48)),cn=users,$ldap_base" \
			--append users="uid=testuser$(($c+49)),cn=users,$ldap_base" 
	done
	date
	echo "GROUP CREATE END"
}

measure_time_for_create_5000_users_distributed_in_100_groups() {
	echo "Measure time to create 5000 users distributed in 1000 groups:"
	time create_5000_users_distributed_in_100_groups
	echo "Check /var/log/univention/connector-s4.log for sync end time"
}

measure_time_for_create_group_with_5000_members() {
	echo "Measure time to create group with 5000 members:"
	time create_group_with_5000_members
	echo "Check /var/log/univention/connector-s4.log for sync end time"
}
