#!/bin/bash

. "$TESTLIBPATH/base.sh" || exit 137

set -e

RESPONSE_CODE=0
function http {
	out=($(curl -s -w '\n%{http_code}' "$@" 'http://localhost:8398'))
	echo "${out[@]:0:${#out[@]}-1}"
	RESPONSE_CODE="${out[${#out[@]}-1]}"
}

function has_request_failed {
	[ "${RESPONSE_CODE:0:1}" != "2" ]
}

function get_license_modify_timestamp {
	univention-ldapsearch -LLL cn=admin modifyTimestamp | sed -n 's/modifyTimestamp: \([0-9]*\)Z/\1/p'
}

