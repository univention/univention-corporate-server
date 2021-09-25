#!/bin/sh
# Test univention-ipcalc6 by calling it with some test values
# diff -y <(./test-all.sh '../') <(./test-all.sh)
test=${0%/*}/test-univention-ipcalc.sh
echo === Normal
echo == network
"$test" "$@" --output network
echo == reverse
"$test" "$@" --output reverse
echo == pointer
"$test" "$@" --output pointer
echo === DNS
echo == network
"$test" "$@" --calcdns --output network
echo == reverse
"$test" "$@" --calcdns --output reverse
echo == pointer
"$test" "$@" --calcdns --output pointer
echo === v6
echo == network
"$test" "$@" --calcdns --output network
echo == reverse
"$test" "$@" --calcdns --output reverse
echo == pointer
"$test" "$@" --calcdns --output pointer
