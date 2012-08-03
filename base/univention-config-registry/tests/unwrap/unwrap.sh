#!/bin/sh
eof=false
nl=
pending_nl=
while ! "$eof"
do
	IFS= read line && nl='
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
