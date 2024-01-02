#!/bin/sh -e
#
# Univention System Setup
#  setup utils helper script
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

USS_PROFILE='/var/cache/univention-system-setup/profile'
check_ldap_access=0

export TEXTDOMAIN="univention-system-setup-scripts"

while [ $# -gt 0 ]
do
	case "$1" in
		"--check_ldap_access")
			# shellcheck disable=SC2034
			check_ldap_access=1
			shift
			;;
		"--check_ldap_availability")
			# shellcheck disable=SC2034
			check_ldap_availability=1
			shift
			;;
		*)
			shift
			;;
	esac
done

# writes an info header
# @param  script path
# @param  description (optional)
info_header () {
	local _path script name
	_path="$1"
	script="${_path##*scripts/}"
	echo "=== $script ($(date +'%Y-%m-%d %H:%M:%S')) ==="

	# information for the internal progress handler
	# print the name of the script... if not specified the script name
	name="$2"
	[ -z "$name" ] && name="$script"
	echo "__NAME__:$script $name"
}

# prints a message to the UMC module that is displayed in the progress bar
# @param  message to print
progress_msg () {
	echo "__MSG__:$1"
}

# prints a join error message to the UMC module that is displayed in the progress bar
# @param  error message to print
progress_join_error () {
	echo "__JOINERR__:$1"
}

# prints an error message to the UMC module that is displayed in the progress bar
# @param  error message to print
progress_error () {
	echo "__ERR__:$1"
}

# prints the number of total steps for the progress bar
# @param  number of total steps
progress_steps () {
	echo "__STEPS__:$1"
	_STEP_=0
}

# prints the current step number and increases it
# @param  the current number of executed steps (optional)
progress_next_step () {
	if [ -n "$1" ]; then
		echo "__STEP__:$1"
		_STEP_="$1"
	else
		echo "__STEP__:$_STEP_"
		_STEP_="$((_STEP_+1))"
	fi
}

is_variable_set () {  # DEPRECATED: has inverted logic
	[ -e "$USS_PROFILE" ] ||
		return 0
	[ -n "$1" ] ||
		return 0
	value="$(grep -E "^$1=" "$USS_PROFILE")"
	[ -z "$value" ]
}
get_profile_var () {
	[ -e "$USS_PROFILE" ] &&
	[ -n "$1" ] &&
	! sed -rne "/^ *#/d;s|^$1=||;T;s|([\"'])(.*)\1 *\$|\2|;p;q 1" "$USS_PROFILE"
}
is_profile_var_true () {
	case "$(get_profile_var "$1" | tr '[:upper:]' '[:lower:]')" in
	'') return 2 ;;
	false|0|disable|disabled|off) return 1 ;;
	*) return 0 ;;
	esac
}

service () {
	local service script unit state action="$1"
	shift
	for service in "$@"
	do
		unit="${service%.sh}.service" script="/etc/init.d/$service"
		if [ -d /run/systemd/system ] && state="$(systemctl -p LoadState show "$unit")" && [ "$state" = 'LoadState=loaded' ]
		then
			case "$action" in
			crestart) systemctl try-restart "$unit" ; continue ;;
			start|stop|reload|force-reload|restart|status) systemctl "$action" "$unit" ; continue ;;
			esac
		fi
		if [ -x "$script" ]
		then
			"$script" "$action"
		fi
	done
}
service_start () { service start "$@"; }
service_stop () { service stop "$@"; }

ldap_binddn () {
	local server_role ldap_base ldap_master ldap_hostdn ldap_username
	eval "$(univention-config-registry shell server/role ldap/base ldap/master ldap/hostdn)"
	case "${server_role:?}" in
	domaincontroller_master|domaincontroller_backup)
		echo "cn=admin,${ldap_base:?}"
		;;
	*)
		ldap_username="$(get_profile_var ldap_username)"
		[ -n "$ldap_username" ] ||
			return
		ldapsearch -x -ZZ -D "${ldap_hostdn:?}" -y /etc/machine.secret -h "${ldap_master:?}" -LLLo ldif-wrap=no "(&(objectClass=person)(uid=${ldap_username:?}))" 1.1 | sed -ne 's|^dn: ||p;T;q'
		;;
	esac
}

ldap_bindpwd () {
	case "$(ucr get server/role)" in
	domaincontroller_master|domaincontroller_backup)
		cat /etc/ldap.secret
		;;
	*)
		get_profile_var ldap_password
		;;
	esac
}
