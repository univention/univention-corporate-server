# Univention Common Shell Library
#
# Copyright 2011-2019 Univention GmbH
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

. /usr/share/univention-lib/ucr.sh

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
	if [ ! -e "$1" ] ; then
		create_logfile "$@"
	fi
}

#
# calls the given joinscript
# call_joinscript <joinscript>
# e.g. call_joinscript 99my-custom-joinscript.inst
# e.g. call_joinscript 99my-custom-joinscript.inst --binddn ... --bindpwd ...
#
call_joinscript () {
	local joinscript
	joinscript="/usr/lib/univention-install/$1"
	if [ -x "$joinscript" ] ; then
		local namejoinscript
		namejoinscript="$1"
		shift
		local role="$(/usr/sbin/univention-config-registry get server/role)"
		if [ "$role" = "domaincontroller_master" -o "$role" = "domaincontroller_backup" ] ; then
			echo "Calling joinscript $namejoinscript ..."
			"$joinscript" "$@"
			echo "Joinscript $namejoinscript finished with exitcode $?"
		fi
	fi
}

#
# deletes the given unjoinscript if it does not belong to any package
# delete_unjoinscript <joinscript>
# e.g. call_unjoinscript 99my-custom-joinscript.uinst
#
delete_unjoinscript ()
{
	local joinscript
	joinscript="/usr/lib/univention-install/$1"

	# Nothing to do if it does not exist
	test -e "$joinscript" || return 1

	# Does the script ends with uinst?
	echo "$joinscript" | grep -q ".uinst$" || return 1

	# Remove the script only if it is not part of a package
	dpkg -S "$joinscript" >/dev/null 2>&1 && return 1

	# Do it
	rm -f "$joinscript"

	return 0
}

# removes the given joinscript from the join script status file
# remove_joinscript_status <name>
# e.g. remove_joinscript_status univention-pkgdb-tools
#
remove_joinscript_status ()
{
	local name="$1"

	sed -i "/^${name} /d" /var/univention-join/status
}

#
# calls the given unjoinscript
# call_unjoinscript <joinscript>
# e.g. call_unjoinscript 99my-custom-joinscript.uinst
# e.g. call_unjoinscript 99my-custom-joinscript.uinst --binddn ... --bindpwd ...
#
call_unjoinscript () {
	local joinscript
	local joinscript_name

	joinscript_name="$1"
	joinscript="/usr/lib/univention-install/${joinscript_name}"

	if [ -x "$joinscript" ] ; then
		shift
		local role="$(/usr/sbin/univention-config-registry get server/role)"
		if [ "$role" = "domaincontroller_master" -o "$role" = "domaincontroller_backup" ] ; then
			"$joinscript" "$@" && delete_unjoinscript "${joinscript_name}"
		fi
	fi
}

#
# calls the given joinscript ONLY on DC master
# call_joinscript_on_dcmaster <joinscript>
# e.g. call_joinscript_on_dcmaster 99my-custom-joinscript.inst
# e.g. call_joinscript_on_dcmaster 99my-custom-joinscript.inst --binddn ... --bindpwd ...
#
call_joinscript_on_dcmaster () {
	local joinscript
	joinscript="/usr/lib/univention-install/$1"
	if [ -x "$joinscript" ] ; then
		shift
		if [ "$(/usr/sbin/univention-config-registry get server/role)" = "domaincontroller_master" ] ; then
			"$joinscript" "$@"
		fi
	fi
}

#
# stops any currently running UDM CLI server
#
stop_udm_cli_server () {
	local pids signal=SIGTERM
	pids=$(pgrep -f "/usr/bin/python.* /usr/share/univention-directory-manager-tools/univention-cli-server") || return 0
	# As long as one of the processes remains, try to kill it.
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
	python2.7 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ip_address().ip)'
}

#
# returns the default IPv4 address
#
get_default_ipv4_address () {
	python2.7 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ipv4_address().ip)'
}

#
# returns the default IPv6 address
#
get_default_ipv6_address () {
	python2.7 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ipv6_address().ip)'
}

#
# returns the default netmask
#
get_default_netmask () {
	python2.7 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; import ipaddr; a=Interfaces().get_default_ip_address(); print(a.netmask if isinstance(a,ipaddr.IPv4Network) else a.prefixlen)'
}

#
# returns the default network
#
get_default_network () {
	python2.7 2>/dev/null -c 'from univention.config_registry.interfaces import Interfaces; print(Interfaces().get_default_ip_address().network)'
}


#
# check whether a package is installed or not
#
check_package_status ()
{
        echo "$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
}

#
# create passwort
#
create_machine_password () {
	local length="$(/usr/sbin/univention-config-registry get machine/password/length)"
	local compl="$(/usr/sbin/univention-config-registry get machine/password/complexity)"
	
	if [ -z "$length" ]; then
		length=20
	fi
	if [ -z "$compl" ]; then
		compl="scn"
	fi
	
	pwgen -1 -${compl} ${length} | tr -d '\n'
}

#
# Update the NSS group cache
#
update_nss_group_cache () {
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
	local name
	local ucr_varname
	local result
	name="${1:?Usage: custom_username <username>}"
	ucr_varname="$(echo "$name" | tr '[A-Z]' '[a-z]' | sed 's| ||g')"
	ucr_varname="users/default/$ucr_varname"

	result="$(/usr/sbin/univention-config-registry get "$ucr_varname")"
	if [ -n "$result" ]; then
		echo -n "$result"
	else
		echo -n "$name"
	fi
}

#
# Get to localized name for a group
#
custom_groupname() {
	local name
	local ucr_varname
	local result
	name="${1:?Usage: custom_groupname <groupname>}"
	ucr_varname="$(echo "$name" | tr '[A-Z]' '[a-z]' | sed 's| ||g')"
	ucr_varname="groups/default/$ucr_varname"

	result="$(/usr/sbin/univention-config-registry get "$ucr_varname")"
	if [ -n "$result" ]; then
		echo -n "$result"
	else
		echo -n "$name"
	fi
}

# vim:set sw=4 ts=4 noet:
