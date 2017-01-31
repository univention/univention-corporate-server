#!/bin/bash
set -e -u

create_machine_password () {
	echo "univention"
}

ln () {
	local run=true
	for i in "$@"; do
		if [[ "$i" == /usr/local/share/* ]]; then
			run=false
		fi
	done
	if $run; then
		command ln "$@"
	else
		echo "MOCKING ln $@"
	fi
}

update-ca-certificates () {
	echo "MOCKING update-ca-certificates $@"
}

[ -t 1 ] && [ -n "$TERM" ] || tput () { :;}
debug () { echo "$(tput setaf 4)${0}: $*$(tput op)";}
debug ""

tmp=$(mktemp -d )
cleanup () {
	debug "EXIT=$?"
	rm -rf "$tmp"
}
trap cleanup EXIT

export PATH="$(readlink -f "${0%/*}/.."):${PATH}"
export MAKE_CERTIFICATES_SH_INCLUDE="./make-certificates.sh"
export EXTERNAL_REQUEST_FILE=""
export EXTERNAL_REQUEST_FILE_KEY=""
export UNIVENTION_BASECONF="$tmp/base.conf"
rnd () { tr -dc '[:alnum:]' </dev/urandom|dd bs=1 count=$1 2>/dev/null; }
R2=$(rnd 2)
R64=$(rnd 64)
R128=$(rnd 128)
xargs -d '\n' ucr set >>"$tmp/log" 2>&1 <<__UCR__
ssl/country=${R2}
ssl/state=${R128}
ssl/locality=${R128}
ssl/organization=${R64}
ssl/organizationalunit=${R64}
ssl/email=${R128}
ssl/common=${R64}
__UCR__

export sslbase="$tmp/ssl"
. "${0%/*}/../make-certificates.sh"
