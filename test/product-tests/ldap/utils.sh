#!/bin/bash

set -e

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
