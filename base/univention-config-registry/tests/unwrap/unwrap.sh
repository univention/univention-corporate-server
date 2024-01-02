#!/bin/sh
# SPDX-FileCopyrightText: 2014-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
eof=false
nl=
pending_nl=
while ! "$eof"
do
	IFS= read -r line && nl='
' || eof=true nl=
	case "${line}" in
	[\ \	]*)
		echo -n "${line#[ 	]}"
		;;
	*)
		echo -n "${pending_nl}${line}"
		;;
	esac
	pending_nl="${nl}"
done
echo -n "${pending_nl}"
