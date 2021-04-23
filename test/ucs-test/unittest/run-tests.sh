#!/bin/sh
#
# Run test suite
#
BASE=$(cd "${0%/*}" && pwd -P)
BIN="$BASE"/../univention/testing/ldif.py
ret=0
for py in python2 python3
do
	"$py" "$BIN" --test-internal
	for directory in "$BASE"/*/
	do
		(
			cd "$directory" || exit $?
			echo -n "${directory}[${py}]: "
			"$py" "$BIN" -a InputA.ldif InputB.ldif >failed
			ret=$?
			if cmp --quiet OutputOK failed
			then
				tput setaf 2
				echo "OK ($ret)"
				rm -f failed
				ret=0
			else
				tput setaf 1
				echo "FAIL ($ret)"
				ret=1
			fi
			tput op
			exit "$ret"
		) || ret=$?
	done
done
exit "$ret"
