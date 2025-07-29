# Univention Samba4 Shell Library
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


#
# Wait for RID pool replication
# univention_samba4_wait_for_rid_set
#
univention_samba4_wait_for_rid_set() {
	local max_attempts=180

	echo -n "Waiting for RID Pool replication: "
	local rIDSetReferences
	local attempt
	attempt=0
	while [ -z "$rIDSetReferences" ] && [ "$attempt" -lt "$max_attempts" ]; do
		if [ "$attempt" != 0 ]; then
			sleep 1
			echo -n "."
		fi
		attempt=$(($attempt + 1))
		rIDSetReferences=$(ldbsearch -H /var/lib/samba/private/sam.ldb "(sAMAccountName=$hostname\$)" rIDSetReferences \
			| ldapsearch-wrapper | sed -n 's/^rIDSetReferences: //p')
	done

	if [ -z "$rIDSetReferences" ]; then
		echo
		echo "Error no rIDSetReferences replicated for $hostname"
		exit 1
	fi

	local rIDAllocationPool
	max_attempts=60
	attempt=0
	while [ -z "$rIDAllocationPool" ] && [ "$attempt" -lt "$max_attempts" ]; do
		if [ "$attempt" != 0 ]; then
			sleep 1
			echo -n "."
		fi
		attempt=$(($attempt + 1))
		rIDAllocationPool=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$rIDSetReferences" rIDAllocationPool \
			| ldapsearch-wrapper | sed -n 's/^rIDAllocationPool: //p')
	done

	if [ -z "$rIDAllocationPool" ]; then
		echo
		echo "Error no rIDAllocationPool replicated for $hostname"
		exit 1
	fi
	echo "done."
}

