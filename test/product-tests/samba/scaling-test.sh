#!/bin/bash

set -x
set -e

scaling_tests () {

	set -x
	set -e

	. product-tests/samba/utils.sh
	eval "$(ucr shell ldap/base windows/domain)"
	#5000 benutzer 1050 gruppen je 50 zufällig benutzer
	#start : 15:08
	#finish : 20:23
	#ca. 5 hours
	for i in $(seq 1 5000); do
		newindex="$i"
		udm users/user create --position "cn=users,$ldap_base" --set username="benutzer$newindex" \
			--set lastname="newuser" --set password="Univention.99"
	done

	for i in $(seq 1 1050); do
		udm groups/group create --position "cn=groups,$ldap_base" --set name="gruppe$i"
		for j in $(seq 1 50); do
			newindex=$(shuf -i 1-5000 -n 1)
			udm groups/group modify --dn "cn=gruppe$i,cn=groups,$ldap_base" \
				--append users="uid=benutzer$newindex,cn=users,$ldap_base"
		done
	done

	# wait for replication
	for i in $(seq 1 1080); do
		if univention-s4search "cn=gruppe1050" | grep -q -i "cn: gruppe1050"; then
			echo "found gruppe1050"
			break
		fi
		echo "waiting for samba object cn=gruppe1050"
		sleep 10
	done

}
