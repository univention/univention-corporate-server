#!/bin/bash
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

sslbase="/etc/freeradius/ssl"

if [ -d "$sslbase/ucsCA" ] ; then
	echo "Creation of new SSL-CA for freeradius has been skipped - already present"
	exit 0
fi

# shellcheck source=/dev/null
. /usr/share/univention-ssl/make-certificates.sh

TMPDIR="$(mktemp -d -t setupCA.XXXXXXXXXX)"
# shellcheck disable=SC2064
trap "rm -rf '$TMPDIR'" 0               # EXIT
# shellcheck disable=SC2064
trap "rm -rf '$TMPDIR'; exit 1" 2       # INT
# shellcheck disable=SC2064
trap "rm -rf '$TMPDIR'; exit 1" 1 15    # HUP TERM

[ ! -e "$sslbase/dh" ] && openssl dhparam -out "$TMPDIR/dh" 1024 && chmod 444 "$TMPDIR/dh"

init

mv "$TMPDIR/dh" "$sslbase"

name="univention-freeradius"
gencert "$sslbase/$name" "$name"
chmod -R g+rx "$sslbase/$name"
