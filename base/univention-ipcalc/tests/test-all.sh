#!/bin/sh
# Test univention-ipcalc* by calling it with some test values
# diff -y <(./test-all.sh '../') <(./test-all.sh)
test=${0%/*}/test-univention-ipcalc.sh
echo === Normal
echo == all
"$test" "$@" --output all
echo == network
"$test" "$@" --output network
echo == reverse
"$test" "$@" --output reverse
echo == pointer
"$test" "$@" --output pointer
echo === DNS
echo == all
"$test" "$@" --calcdns --output all
echo == network
"$test" "$@" --calcdns --output network
echo == reverse
"$test" "$@" --calcdns --output reverse
echo == pointer
"$test" "$@" --calcdns --output pointer
echo === v6
echo == network
"$test" "$@" -6 --calcdns --output network
echo == reverse
"$test" "$@" -6 --calcdns --output reverse
echo == pointer
"$test" "$@" -6 --calcdns --output pointer
