#!/bin/sh -e
#
# Univention System Setup
#  setup utils helper script
#
# Copyright 2004-2019 Univention GmbH
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

profile_file="/var/cache/univention-system-setup/profile"
check_ldap_access=0

export TEXTDOMAIN="univention-system-setup-scripts"

while [ $# -gt 0 ]
do
	case "$1" in
		"--check_ldap_access")
			check_ldap_access=1
			shift
			;;
		"--check_ldap_availability")
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
	_path=$1
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
		_STEP_=$1
	else
		echo "__STEP__:$_STEP_"
		_STEP_=$((_STEP_+1))
	fi
}

is_variable_set () {
	if [ ! -e "$profile_file" ]; then
		return 0
	fi

	if [ -z "$1" ]; then
		return 0
	fi
	value="$(egrep "^$1=" "$profile_file")"
	if [ -z "$value" ]; then
		return 0
	else
		return 1
	fi
}
get_profile_var () {
	if [ ! -e "$profile_file" ]; then
		return
	fi

	if [ -z "$1" ]; then
		return
	fi

	sed -rne "/^ *#/d;s|^$1=||;T;s|([\"'])(.*)\1 *\$|\2|;p;q" "$profile_file"
}

is_profile_var_true () {
	local value="$(get_profile_var "$1")"
	if [ -z "$value" ]; then
		return 2
	fi
	value=$(echo "$value" | tr '[:upper:]' '[:lower:]')
	for falsevalue in no false 0 disable disabled off; do
		if [ "$value" = "$falsevalue" ]; then
			return 1
		fi
	done
	return 0
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
	eval "$(univention-config-registry shell server/role ldap/base ldap/master ldap/hostdn)"
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		echo "cn=admin,$ldap_base"
	else
		ldap_username=`get_profile_var ldap_username`
		if [ -n "$ldap_username" ]; then
			dn=`ldapsearch -x -ZZ -D "$ldap_hostdn" -y /etc/machine.secret -h $ldap_master "(&(objectClass=person)(uid=$ldap_username))" | grep "dn: " | sed -e 's|dn: ||' | head -n 1`
			echo "$dn"
		fi
	fi
}

ldap_bindpwd () {
	eval "$(univention-config-registry shell server/role ldap/base ldap/master)"
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		echo "`cat /etc/ldap.secret`"
	else
		ldap_password=`get_profile_var ldap_password`
		if [ -n "$ldap_password" ]; then
			echo "$ldap_password"
		fi
	fi
}
