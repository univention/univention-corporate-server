#!/bin/sh
#
# Test-suit for different ldif unwrappers
#

cd "${0%/*}" || exit 2
if which gcc >/dev/null
then
	# shellcheck disable=SC2015
	[ -x unwrap ] && [ unwrap -nt unwrap.c ] || gcc -Wall -Werror -o unwrap unwrap.c
fi
errors=0
run () {
	local in="$1" out="${1%in}out"
	shift
	"$@" <"$in" | diff -y --suppress-common-lines - "$out" || { echo "-- $* $in"; errors=$((errors +1)); }
}
for file in *.in
do
	echo "===== $file ====="
	run "$file" ../../python/univention/ldif.py
	run "$file" ../../python/univention/ldif.py unwrap
	run "$file" ./unwrap.sh
	run "$file" ./unwrap.sed
	run "$file" ./unwrap.sed2
	[ -x unwrap ] && run "$file" ./unwrap
done
exit $errors
