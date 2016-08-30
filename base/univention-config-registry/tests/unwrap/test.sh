#!/bin/sh
#
# Test-suit for different ldif unwrappers
#

cd "${0%/*}" || exit 2
if which gcc >/dev/null
then
	[ -x unwrap ] && [ unwrap -nt unwrap.c ] || gcc -Wall -Werror -o unwrap unwrap.c
fi
errors=0
run () {
	local prog="$1" in="$2" out="${2%in}out"
	"$prog" <"$in" | diff -y --suppress-common-lines - "$out" || { echo "-- $prog $in"; errors=$((errors +1)); }
}
for file in *.in
do
	echo "===== $file ====="
	run ../../scripts/ldapsearch-wrapper "$file"
	run ./unwrap.py "$file"
	run ./unwrap.sh "$file"
	run ./unwrap.sed "$file"
	run ./unwrap.sed2 "$file"
	[ -x unwrap ] && run ./unwrap "$file"
done
exit $errors
