#!/bin/bash
#
# Run test suite
#
BASE=$(cd "${0%/*}" && pwd -P)
BIN="$BASE"/../univention/testing/ldif.py
for directory in "$BASE"/*
do
	[ -d "$directory" ] || continue
	(
		cd "$directory"
		echo -n "$directory: "
		python "$BIN" -a InputA.ldif InputB.ldif >failed
		ret=$?
		if cmp --quiet OutputOK failed
		then
			tput setaf 2
			echo "OK ($ret)"
			rm -f failed
		else
			tput setaf 1
			echo "FAIL ($ret)"
		fi
		tput op
	)
done
