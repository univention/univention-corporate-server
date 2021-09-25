#!/bin/sh
# Test univention-ipcalc6 by calling it with some test values
# diff -y <(./test-univention-ipcalc.sh '../' --calcdns) <(./test-univention-ipcalc.sh '' --calcdns)
# diff -y <(./test-univention-ipcalc.sh '../' -6 --calcdns --output pointer) <(./test-univention-ipcalc.sh '' -6 --calcdns --output pointer)
prefix=
while [ $# -ge 1 ]
do
	case "$1" in
		/*|./*|../*|'') prefix=$1 ; shift ;;
		--) shift ; break ;;
		*) break
	esac
done

echo '= v4'
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 0.0.0.0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 128.0.0.0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 255.0.0.0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 255.255.0.0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 255.255.255.0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 170.85.204.51 --netmask 255.255.255.255 "$@"

echo '= v6'
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 0 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 1 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 4 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 64 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 112 "$@"
"${prefix}univention-ipcalc6" --calcdns --ip 0000:1111:2222:3333:4444:5555:6666:7777 --netmask 128 "$@"
