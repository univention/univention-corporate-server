#!/bin/bash
set -e -u
setup_var () {
	PATH="$PATH:/usr/sbin"
	SELF="$(readlink -f "${0%/*}")"
	PAMD="$(readlink -f "${0%/*}/../conffiles/etc/pam.d")"
}
setup_ucr () {
	tmp="$(mktemp -d)"
	trap "rm -rf '$tmp'" EXIT
	export UNIVENTION_BASECONF="$tmp/base.conf"
	ucr set dummy='42'
	echo >>"$UNIVENTION_BASECONF"
	local IFS=' '
	echo "auth/methods: $*" >>"$UNIVENTION_BASECONF"
}
gen_common () {
	ucr filter <"$PAMD/common-account" >"$tmp/common-account"
	cat "$PAMD/common-auth.d/"* | ucr filter >"$tmp/common-auth"
	cat "$PAMD/common-session.d/"* | ucr filter >"$tmp/common-session"
	ucr filter <"$PAMD/common-password" >"$tmp/common-password"
	sed -i -r -e 's/[ \t]+/ /g;/^ *#/d' "$tmp/common-"*
}
check () {
	local service="$1" action="$2" module="$3" arg="${4:-}"
	local file="$tmp/common-$service" search="${service} ${action} ${module}${arg:+ ${arg}}"
	fgrep "$search" "$file" && return 0
	echo "*** MISSING:"
	echo "$search"
	echo "*** IN:"
	grep "^${service} .* ${module}" "$file" ||
		grep "^${service} " "$file" ||
		egrep -vx ' *(#.*)?' "$file" ||
		cat "$file"
	return 1
}
main
