#!/bin/bash

umc_login() {
	local user="$1"
	local password="$2"
	python <<%EOF
import sys
import univention.lib.umc
client = univention.lib.umc.Client(None, $user, $password)
r = client.umc_command("ucr/get", ["apache2/autostart"])
if not r.status == "200":
	sys.exit(1)
%EOF
}

check_hashes_are_replicated() {
	local user="$1"
	local -a attrs=(userPassword krb5Key sambaNTPassword)
	ldif=$(univention-ldapsearch uid="$user" "${attrs[@]}")
	for attr in "${attrs[@]}"; do
		if ! grep -q "^$attr:" <<<"$ldif"; then
			echo "Attribute $attr not found on user account $user"
			return 1
		fi
	done
}

measure_duration() {
	local limit
	## poor mans option parsing
	limit="${1#--limit=}"
	if [ "$1" != "$limit" ]; then
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
	echo -e "START $operation\tTIMESTAMP: $timestamp_start"

	"$@"

	timestamp_end=$(date +%Y%m%d%H%M%S)
	echo -e "END $operation\tTIMESTAMP: $timestamp_end"

	duration=$((timestamp_end - timestamp_start))
	echo "INFO: $operation took $duration seconds"
	if [ -n "$limit" ] && [ "$duration" -gt "$limit" ]; then
		echo "ERROR: $operation took too long (allowed time: $limit seconds)"
	fi
}
