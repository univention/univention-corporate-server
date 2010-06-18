#!/bin/bash
#
# /usr/share/doc/sysv-rc/README.policy-rc.d.gz
#
list=false
while [ $# -ge 0 ]
do
	case "$1" in
		--quiet) ;;
		--list) list=true;;
		--*) echo "Unknown option $1" >&2 ; exit 2 ;;
		*) break ;;
	esac
	shift
done

if "$list"
then
	id="${1:?initscript ID missing}"
	runlevel="$2"
else
	id="${1:?initscript ID missing}"
	action="${2:?action missing}"
	runlevel="$3"
fi

case "$id" in
	univention-virtual-machine-manager-daemon) ;;
	*) exit 0 ;; # action allowed
esac

case "$action" in
	start) exit 101 ;; # action forbidden by policy
	restart) exit 101 ;; # action forbidden by policy
	*) exit 0 ;; # action allowed
esac

exit 1

# vim: set ft=sh:
