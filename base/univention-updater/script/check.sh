#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2018-2022 Univention GmbH
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

# shellcheck disable=SC2154
UPDATER_LOG="/var/log/univention/updater.log"
###CHECKS_ONLY###
if [ -z "${UPDATE_NEXT_VERSION:-}" ]
then
	# stdout to screen and log
	exec > >(exec tee -ia "$UPDATER_LOG")
fi
###CHECKS_COMMON###

VERSION="50"
VERSION_NAME="5.0"
MIN_VERSION="4.4-8"

updateLogDir="/var/univention-backup/update-to-${UPDATE_NEXT_VERSION:-$VERSION}"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

echo
echo "Starting $0 ($(date)):"

eval "$(univention-config-registry shell)"
# shellcheck source=/dev/null
. /usr/share/univention-lib/ucr.sh || exit $?

conffile_is_unmodified () {
	# conffile_is_unmodified <conffile>
	# returns exitcode 0 if given conffile is unmodified
	local chksum fnregex testchksum
	chksum="$(md5sum "${1:?}" | awk '{print $1}')"
	fnregex="$(python -c 'import re,sys;print re.escape(sys.argv[1])' "$1")"
	for testchksum in $(dpkg-query -W -f '${Conffiles}\n' | sed -nre "s,^ $fnregex ([0-9a-f]+)( .*)?$,\\1,p") ; do
		[ "$testchksum" = "$chksum" ] &&
			return 0
	done
	return 1
}

ignore_check () {
	local var="$1"
	is_ucr_true "$var" ||
		return 1
	echo -n "Ignoring test as requested by $var " 1>&2
	return 0
}

have () {
	command -v "$1" >/dev/null 2>&1
}

die () {
	echo "${0##*/}: $*"
	exit 1
}

# check for hold packages
update_check_hold_packages () {
	local var="update$VERSION/ignore_hold"
	ignore_check "$var" && return 100
	hold_packages=$(LC_ALL=C dpkg -l | awk '/^h/{print $2}')
	[ -n "$hold_packages" ] || return 0

	echo "	WARNING: Some packages are marked as hold -- this may interrupt the update and result in an inconsistent system!"
	echo "	Please check the following packages and unmark them or set the UCR variable $var to yes"
	for hp in $hold_packages; do
		echo "	- $hp"
	done
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}

# Bug #44650 begin - check slapd on Managed Node
update_check_slapd_on_member () {
	local var="update$VERSION/ignore_slapd_on_member"
	ignore_check "$var" && return 100
	have slapd ||
		return 0
	[ "$server_role" = "memberserver" ] ||
		return 0

	echo "	The ldap server is installed on your Managed Node. This is not supported"
	echo "	and may lead to problems during the update. Please deinstall the package"
	echo "	*slapd* from this system with either the command line tool univention-remove "
	echo "	  -> univention-remove slapd"
	echo "	or via the package management in the Univention Management Console."
	echo "	Make sure that only the package slapd gets removed!"
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}

update_check_ldap_schema () {
	[ -x /usr/sbin/slapschema ] ||
		return 0
	/usr/sbin/slapschema 1>&2 &&
		return 0

	echo "	There is a problem with the LDAP schema on this system."
	echo "	Please check $UPDATER_LOG or run 'slapschema' manually."
	return 1
}

update_check_valid_machine_credentials () {
	[ -f /var/univention-join/joined ] ||
		return 0
	[ -f /etc/machine.secret ] &&
		return 0

	echo "	The credentials for the machine account could not be found!"
	echo "	Please re-join this system."
	return 1
}

update_check_ldap_connection () {
	case "$server_role" in
	'') return 0 ;;
	esac
	[ -n "$ldap_base" ] || return 0
	[ -n "$ldap_hostdn" ] || return 0

	ldapsearch -x -D "$ldap_hostdn" -y /etc/machine.secret -b "$ldap_base" -s base &>/dev/null
	[ $? -eq 49 ] ||
		return 0

	echo "	A LDAP connection to the configured LDAP servers with the machine"
	echo "	account has failed (invalid credentials)!"
	echo "	This MUST be fixed before the update can continue."
	echo "	This problem can be corrected by setting the content of the file"
	echo "	/etc/machine.secret to the password of the computer object using"
	echo "	Univention Management Console."
	return 1
}

update_check_role_package_removed () {
	local role_package
	case "$server_role" in
	domaincontroller_master) role_package="univention-server-master" ;;
	domaincontroller_backup) role_package="univention-server-backup" ;;
	domaincontroller_slave) role_package="univention-server-slave" ;;
	memberserver) role_package="univention-server-member" ;;
	*) return 0 ;;
	esac

	LC_ALL=C ${update_commands_distupgrade_simulate:-false} 2>&1 | grep -q "^Remv $role_package" ||
		return 0

	echo "	The pre-check of the update calculated that the"
	echo "	essential software package $role_package will be removed"
	echo "	during the upgrade. This could result into a broken system."
	echo
	# If you really know what you are doing, you can skip this check by
	# setting the UCR variable update/commands/distupgrade/simulate to /bin/true.
	# But you have been warned!
	# In this case, you have to set the UCR variable after the update back
	# to the old value which can be get from /var/log/univention/config-registry.replog
	echo "	Please contact Univention Support in case you have an Enterprise"
	echo "	Subscription. Otherwise please try Univention Help"
	echo "	<https://help.univention.com/>"
	return 1
}

# check that no apache configuration files are manually adjusted; Bug #43520
update_check_overwritten_umc_templates () {
	local var="update$VERSION/ignore_apache_template_checks"
	ignore_check "$var" && return 100
	univention-check-templates 2>/dev/null |
		grep /etc/univention/templates/files/etc/apache2/sites-available/ 1>&2 ||
		return 0

	echo "	WARNING: There are modified Apache configuration files in /etc/univention/templates/files/etc/apache2/sites-available/."
	echo "	Please restore the original configuration files before upgrading and apply the manual changes again after the upgrade succeeded."
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}

update_check_package_status () {
	dpkg -l | LC_ALL=C grep "^[a-zA-Z][A-Z] " 1>&2 || return 0

	echo "	The package state on this system is inconsistent."
	echo "	Please run 'dpkg --configure -a' manually"
	return 1
}


# check for Primary Directory Node UCS version
update_check_master_version () {
	local master_version ATTR=univentionOperatingSystemVersion var="update$VERSION/ignore_version"
	ignore_check "$var" && return 100
	[ -f /var/univention-join/joined ] || return 0

	case "$server_role" in
	domaincontroller_master) return 0 ;;
	esac

	master_version="$(univention-ldapsearch -LLL '(univentionServerRole=master)' "$ATTR" | sed -ne "s/$ATTR: //p;T;q")"
	dpkg --compare-versions "$master_version" le "${version_version}-${version_patchlevel}" || return 0

	echo "	Your Primary Directory Node is still on version $master_version."
	echo "	It is strongly recommended that the Primary Directory Node is"
	echo "	always the first system to be updated during a release update."
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}

update_check_disk_space () {
	local var="update$VERSION/ignore_free_space" ret=0
	ignore_check "$var" && return 100
	while read -r partition size usersize
	do
		if [ "$(($(stat -f -c '%a*%S' "$partition")/1024))" -le "$size" ]
		then
			echo "	Not enough space in $partition, need at least $usersize."
			echo "	This may interrupt the update and result in an inconsistent system!"
			if [ "$partition" = "/boot" ] && [ "$update50_pruneoldkernel" != "yes" ]
			then
				echo
				echo "	Old kernel versions on /boot/ can be pruned by manully by running"
				echo "	'univention-prune-kernels' or automatically during"
				echo "	next update attempt by setting config registry variable"
				echo "	update${VERSION}/pruneoldkernel to \"yes\"."
			fi
			ret=1
		fi
	done <<__PART__
/var/cache/apt/archives	4000000	4000 MB
/boot	100000	100 MB
/	4000000	4000 MB
__PART__
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	echo "	But be aware that this is not recommended!"
	return "$ret"
}

# block if failed.ldif exists
update_check_failed_ldif() {
	[ -e /var/lib/univention-directory-replication/failed.ldif ] || return 0

	echo "	A failed.ldif exists."
	echo "	Please check <https://help.univention.com/t/6432> for further information."
	echo "	The update can be started after the failed.ldif has been removed."
	return 1
}

# block update if system date is too old
update_check_system_date_too_old() {
	local system_year
	system_year="$(date +%Y)"
	local var="update$VERSION/ignore_system_date"
	ignore_check "$var" && return 100
	[ "$system_year" -lt 2020 ] || return 0

	echo "	The system date ($(date +%Y-%m-%d)) does not seem to be correct."
	echo "	Please set a current system time before the update, otherwise the"
	echo "	update will fail if Spamassassin is installed."
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}

update_check_minimum_ucs_version_of_all_systems_in_domain () {  # Bug #51621
	[ "$server_role" != "domaincontroller_master" ] && return 0

	# FIXME: python3-univention-lib is not installed on UCS-4.4-7 by default, so this must remain Python 2 (for now):
	MIN_VERSION="$MIN_VERSION" /usr/bin/python2.7 -c '
# -*- coding: utf-8 -*-
from __future__ import print_function
from distutils.version import LooseVersion
from os import environ
from univention.uldap import getMachineConnection

lo = getMachineConnection()

REQUIRED_VERSION = environ["MIN_VERSION"]
V5 = LooseVersion("5.0-0")

ATTR = "univentionOperatingSystemVersion"
blocking_computers = [
    "%s: %s" % (dn, attrs[ATTR][0].decode("UTF-8", "replace"))
    for dn, attrs in lo.search("(&(%s=*)(univentionOperatingSystem=Univention Corporate Server)(!(univentionObjectFlag=docker)))" % ATTR, attr=[ATTR])
    if LooseVersion(attrs[ATTR][0].decode("UTF-8", "replace")) < LooseVersion(REQUIRED_VERSION)
]

blocking_objects = []
ATTRS = ["univentionUCSVersionStart", "univentionUCSVersionEnd"]
for dn, attrs in lo.search("(&(objectClass=univentionObjectMetadata)(!(objectClass=univentionLDAPExtensionSchema)))", attr=ATTRS):
    start, end = (attrs.get(attr, [b""])[0].decode("UTF-8", "replace") for attr in ATTRS)
    if start and LooseVersion(start) >= V5:
        continue
    if end and LooseVersion(end) < V5:
        continue
    if start and LooseVersion(start) < V5 and end:
        continue
    blocking_objects.append("%s: [%s..%s)" % (dn, start or "unspecified", end or "unspecified"))

if blocking_computers:
    print("The following hosts must be upgraded to UCS %s first:\n\t%s" % (REQUIRED_VERSION, "\n\t".join(blocking_computers)))
if blocking_objects:
    print("The following extensions are incompatible with UCS 5.0:\n\t%s" % "\n\t".join(blocking_objects))

if blocking_computers or blocking_objects:
    exit(1)'
}

update_check_required_ucsschool_version () {  # Bug #54883 Bug #54896
	if ! python3 -c '
import sys
from distutils.version import LooseVersion
from univention.appcenter.app_cache import Apps
ucsschool = Apps().find("ucsschool")

if ucsschool.is_installed():
	sys.exit(LooseVersion(ucsschool.version) <= LooseVersion("5.0 v1"))
	'; then
		echo "UCS@school is installed. To upgrade to UCS 5.0-2 as least UCS@school 5.0 v2 is required."
		echo "Please upgrade the UCS@school app first!"
		return 1
	fi
}

checks () {
	# stderr to log
	exec 2>>"$UPDATER_LOG"

	local f name stat stdout ret key success=true
	declare -A messages
	for f in $(declare -F)
	do
		if [[ "$f" =~ update_check_.* ]]
		then
			name=${f#update_check_}
			stat="OK"
			printf "%-50s" "Checking $name ... "
			stdout=$($f)
			ret=$?
			if [ $ret -ne 0 ]
			then
				if [ $ret -eq 100 ]
				then
					stat="IGNORED"
				else
					stat="FAIL"
					success=false
					messages["$name"]="$stdout"
				fi
			fi
			echo "$stat"
		fi
	done

	# summary
	ret=0
	if ! $success
	then
		echo
		echo "The system can not be updated to UCS $VERSION_NAME due to the following reasons:"
		for key in "${!messages[@]}"
		do
			echo
			echo "$key:"
			echo "${messages[$key]}" # | fmt --uniform-spacing --width="${COLUMNS:-80}"
		done
		echo
		ret=1
	fi
	[ "$ret" -gt 0 ] &&
		exit "$ret"
}

###CHECKS_ONLY###
if [ -z "${UPDATE_NEXT_VERSION:-}" ]
then
	main () {
		[ $# -ge 1 ] || set checks
		while [ $# -ge 1 ]
		do
			"$1"
			shift
		done
	}

	main "$@"
fi
###CHECKS_COMMON###
