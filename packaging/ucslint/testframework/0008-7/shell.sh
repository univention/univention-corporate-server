#!/bin/sh
set -e
# shellcheck source=/dev/null
. /usr/share/univention-lib/base.sh
printf '%s %s\n' "Administrator" "$(custom_username "Administrator")"
printf '%s %s\n' "Domain Admins" "$(custom_groupname "Domain Admins")"
printf '%s %s\n' "Administrator" "$(custom_groupname "Administrator")"
printf '%s %s\n' "Windows Hosts" "$(custom_groupname "Windows Hosts")"
