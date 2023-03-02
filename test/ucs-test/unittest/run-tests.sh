#!/bin/sh
#
# Run test suite
#
BASE=$(cd "${0%/*}" >/dev/null && pwd -P)
BIN="$BASE"/../univention/testing/ldif.py
ret=0
python3 "$BIN" --test-internal
{ [ -n "${TERM:-}" ] && [ -t 1 ]; } || tput () { :; }
for directory in "$BASE"/*/
do
	(
		cd "$directory" || exit $?
		echo -n "${directory}[python3]: "
		python3 "$BIN" -a InputA.ldif InputB.ldif >failed
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
exit "$ret"
