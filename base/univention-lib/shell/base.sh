# shellcheck shell=bash
# Univention Common Shell Library
#
# Copyright 2011-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

# shellcheck source=/dev/null
[ -e /usr/share/univention-lib/ucr.sh ] &&
. /usr/share/univention-lib/ucr.sh
# shellcheck source=/dev/null
[ -e /usr/share/univention-lib/join.sh ] &&
. /usr/share/univention-lib/join.sh

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}

have () {
	command -v "$1" >/dev/null 2>&1
}

#
# creates an empty file with given owner/group and permissions
# create_logfile <filename> <owner> <permissions>
# e.g. create_logfile /tmp/foo.log root:adm 0750
#
create_logfile () {
	touch "$1"
	chown "$2" "$1"
	chmod "$3" "$1"
}

#
# creates an empty file with given owner/group and permissions if file does not exist
# create_logfile_if_missing <filename> <owner> <permissions>
# e.g. create_logfile_if_missing /tmp/foo.log root:adm 0750
#
create_logfile_if_missing () {
	[ -e "$1" ] ||
		create_logfile "$@"
}

#
# stops any currently running UDM CLI server
#
stop_udm_cli_server () {
	local pids signal=SIGTERM
	pids=$(pgrep -f "/usr/bin/python.* /usr/share/univention-directory-manager-tools/univention-cli-server") || return 0
	# As long as one of the processes remains, try to kill it.
	# shellcheck disable=SC2086
	while /bin/kill -"$signal" $pids 2>/dev/null # IFS
	do
		sleep 1
		signal=SIGKILL
	done
	return 0
}

#
# if is_domain_controller; then
#         ... do domain controller stuff ...
# fi
#
is_domain_controller () {
	case "$(/usr/sbin/univention-config-registry get server/role)" in
	domaincontroller_master) return 0 ;;
	domaincontroller_backup) return 0 ;;
	domaincontroller_slave) return 0 ;;
	*) return 1 ;;
	esac
}

#
# returns the default IP address
#
get_default_ip_address () {
	python3 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ip_address().ip)'
}

#
# returns the default IPv4 address
#
get_default_ipv4_address () {
	python3 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ipv4_address().ip)'
}

#
# returns the default IPv6 address
#
get_default_ipv6_address () {
	python3 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ipv6_address().ip)'
}

#
# returns the default netmask
#
get_default_netmask () {
	python3 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; import ipaddress; a = Interfaces().get_default_ip_address(); print(a.netmask if isinstance(a, ipaddress.IPv4Interface) else a.network.prefixlen)'
}

#
# returns the default network
#
get_default_network () {
	python3 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ip_address().network.network_address)'
}


#
# check whether a package is installed or not
#
check_package_status () {
	dpkg-query -W -f '${db:Status-Status}\n' "$1" 2>/dev/null
}

#
# create passwort
#
create_machine_password () {
	local length compl
	length="$(/usr/sbin/univention-config-registry get machine/password/length)"
	compl="$(/usr/sbin/univention-config-registry get machine/password/complexity)"
	pwgen -1 -"${compl:-scn}" "${length:-20}" | tr -d '\n'
}

#
# Update the NSS group cache
#
update_nss_group_cache () {
	local ldap_group_to_file_param
	if is_ucr_true nss/group/cachefile; then
		is_ucr_true nss/group/cachefile/check_member && ldap_group_to_file_param="--check_member"
		/usr/lib/univention-pam/ldap-group-to-file.py $ldap_group_to_file_param
	else
		nscd -i group
	fi
}

#
# Get to localized name for a user
#
custom_username() {
	local ucr_varname result name="${1:?Usage: custom_username <username>}"
	ucr_varname="users/default/$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -d ' ')"

	result="$(/usr/sbin/univention-config-registry get "$ucr_varname")"
	echo -n "${result:-$name}"
}

#
# Get to localized name for a group
#
custom_groupname() {
	local ucr_varname result name="${1:?Usage: custom_groupname <groupname>}"
	ucr_varname="groups/default/$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -d ' ')"

	result="$(/usr/sbin/univention-config-registry get "$ucr_varname")"
	echo -n "${result:-$name}"
}

#
# Echo with timestamp
#
echowithtimestamp() {
	echo "[$(date '+%F %T.%N')] $@"
}

# vim:set sw=4 ts=4 noet:
