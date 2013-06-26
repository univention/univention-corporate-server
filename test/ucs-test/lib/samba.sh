wait_for_LDAP_replication_of_domain_sambaSid() {
	username="$1"
	if [ -z "$username" ]; then
		echo "usage: $0 <username>"
		return 1
	fi
	t0=$(date +%Y%m%d%H%M%S)
	sambaSID=$(univention-ldapsearch -xLLL uid="$username" sambaSID | sed -n 's/^sambaSID: //p')
	i=0
	if [ -z "${sambaSID%S-1-4*}" ]; then
		echo -n "Waiting for S4-Connector and LDAP replication of domain sambaSID for user $username (current: $sambaSID)."
		while [ -z "${sambaSID%S-1-4*}" ]; do
			if [ "$i" = 30 ]; then
				t=$(date +%Y%m%d%H%M%S)
				fail_fast 1 "TIMEOUT: No domain sambaSID replicated to local LDAP after $(($t-$t0)) seconds"
			fi
			sleep 1
			echo -n "."
			i=$(($i+1))
			sambaSID=$(univention-ldapsearch -xLLL uid="$username" sambaSID | sed -n 's/^sambaSID: //p')
		done
		echo
	fi
	t=$(date +%Y%m%d%H%M%S)
	echo "S4-Connector and LDAP replication of domain sambaSID took $(($t-$t0)) seconds"
}

wait_for_drs_replication() {
	ldap_filter="$1"
	if [ -z "$ldap_filter" ]; then
		echo "usage: $0 <ldap_filter>"
		return 1
	fi
	attr="$2"
	if [ -z "$attr" ]; then
		attr='dn'
	fi


	t0=$(date +%Y%m%d%H%M%S)
	value=$(ldbsearch -H /var/lib/samba/private/sam.ldb "$ldap_filter" "$attr" | sed -n "s/^$attr: //p")
	i=0
	if [ -z "$value" ]; then
		echo -n "Waiting for DRS replication, filter: $ldap_filter"
		while [ -z "$objectSid" ]; do
			if [ "$i" = 360 ]; then
				t=$(date +%Y%m%d%H%M%S)
				fail_fast 1 "TIMEOUT: Replication timout to local sam.ldb after $(($t-$t0)) seconds"
			fi
			sleep 1
			echo -n "."
			i=$(($i+1))
			objectSid=$(ldbsearch -H /var/lib/samba/private/sam.ldb "$ldap_filter" "$attr" | sed -n "s/^$attr: //p")
		done
		echo
	fi
	t2=$(date +%Y%m%d%H%M%S)
	echo "DRS Replication took $(($t2-$t0)) seconds"
}

force_drs_replication() {
	source_dc="$1"
	if [ -z "$source_dc" ]; then
		source_dc=$(ucr get ldap/master)
	fi
	partition_dn="$2"
	if [ -z "$partition_dn" ]; then
		partition_dn=$(ucr get samba4/ldap/base)
	fi

	hostname=$(ucr get hostname)
	samba-tool drs replicate "$hostname" "$source_dc" "$partition_dn"
}
