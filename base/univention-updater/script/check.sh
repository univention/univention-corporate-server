#!/bin/bash
#
# Copyright (C) 2018-2021 Univention GmbH
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
MIN_VERSION="4.4-7"

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


update_check_system_role () {
	case "${server_role:=}" in
	domaincontroller_master) return 0 ;;
	domaincontroller_backup) return 0 ;;
	domaincontroller_slave) return 0 ;;
	memberserver) return 0 ;;
	'') return 0 ;;  # unconfigured
	basesystem) echo "	The server role '$server_role' is not supported anymore with UCS-5!" ;;
	*) echo "	The server role '$server_role' is not supported!" ;;
	esac
	return 1
}

update_check_min_version () {
	dpkg --compare-versions "$MIN_VERSION" le "${version_version}-${version_patchlevel}" && return 0

	echo "	The system needs to be at least at version $MIN_VERSION in order to update!"
	return 1
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

# check /usr on separate file system
update_check_usr_mountpoint () {
	mountpoint -q /usr ||
		return 0

	echo "	/usr/ seems to be a separate file system, which is no longer supported."
	echo "	Mounting file systems nowadays requires many helpers, which use libraries"
	echo "	and other resources from /usr/ by default. With a separate /usr/ they"
	echo "	often break in subtle ways or lead to hard to debug boot problems."
	echo "	As such the content of /usr/ must be moved to the root file system before"
	echo "	the system can be upgraded to UCS-4.2. This procedure should be performed"
	echo "	manually and might require resizing the file systems. It is described at"
	echo "	<https://help.univention.com/t/6382>."
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

# Bug #51955
update_check_old_packages () {
	local pkg status IFS=$'\n' var="update$VERSION/ignore_old_packages"
	ignore_check "$var" && return 100
	declare -a found=() old=(
		univention-kvm-compat
		univention-kvm-virtio
		univention-novnc
		univention-virtual-machine-manager-daemon
		python-univention-virtual-machine-manager
		python3-univention-virtual-machine-manager
		univention-management-console-module-uvmm
		univention-virtual-machine-manager-node-common
		univention-virtual-machine-manager-node-kvm
		univention-virtual-machine-manager-schema'=See <https://help.univention.com/t/6443>'
		python-univention-directory-manager-uvmm
		python3-univention-directory-manager-uvmm
		univention-nagios-libvirtd
		univention-nagios-libvirtd-xen
		univention-nagios-uvmmd
		univention-pkgdb-lib
		univention-bacula
		univention-doc'=Now online at <https://docs.software-univention.de/ucs-python-api/>'
		univention-mysql'=Switch to univention-mariadb'
		univention-ftp
		univention-management-console-module-mrtg
		univention-kernel-image'=Use linux-image-amd64'
		univention-kernel-headers'=Use linux-headers-amd64'
		univention-kernel-source'=Use linux-source'
		univention-kde
		univention-kde-setdirs
		univention-kdm
		univention-mozilla-firefox
		univention-x-core
		univention-java'=Use default-jre or default-jdk'
		univention-samba4wins
		univention-debootstrap
		univention-debootstrap-3
		univention-check-printers
		univention-snmp
		univention-snmpd
		univention-remote-backup
	)
	for pkg in "${old[@]}"
	do
		status=$(dpkg-query -W -f '${db:Status-Status}' "${pkg%%=*}" 2>/dev/null) || continue
		[ "$status" = 'not-installed' ] && continue
		case "$pkg" in
		*=*) found+=("	${pkg%%=*}	${pkg#*=}") ;;
		*) found+=("	$pkg") ;;
		esac
	done
	# shellcheck disable=SC2128
	[ -n "$found" ] || return 0
	echo "WARNING: The following packages from UCS-4 are still installed, which are no longer supported with UCS-5:"
	echo "${found[*]}"
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 0
}

# Bug #51497 #51973 #31048 #51655 #51955 #51982
declare -a legacy_ocs_structural=(
	'(structuralObjectClass=univentionAdminUserSettings)'
	# UCS TCS:
	'(structuralObjectClass=univentionPolicyAutoStart)'
	'(structuralObjectClass=univentionPolicyThinClient)'
	'(structuralObjectClass=univentionThinClient)'
	'(structuralObjectClass=univentionMobileClient)'
	'(structuralObjectClass=univentionFatClient)'
	# UCC:
	'(structuralObjectClass=univentionCorporateClient)'
	'(structuralObjectClass=univentionPolicyCorporateClientUser)'
	'(structuralObjectClass=univentionCorporateClientSession)'
	'(structuralObjectClass=univentionCorporateClientAutostart)'
	'(structuralObjectClass=univentionCorporateClientImage)'
	'(structuralObjectClass=univentionPolicyCorporateClientComputer)'
	'(structuralObjectClass=univentionPolicyCorporateClientDesktop)'
	'(structuralObjectClass=univentionPolicySoftwareupdates)'
	'(structuralObjectClass=univentionPolicyCorporateClient)'
	# UVMM:
	'(structuralObjectClass=univentionVirtualMachineCloudConnection)'
	'(structuralObjectClass=univentionVirtualMachineCloudType)'
	'(structuralObjectClass=univentionVirtualMachine)'
	'(structuralObjectClass=univentionVirtualMachineProfile)'
)
declare -a legacy_ocs_auxiliary=(
	'(objectClass=univentionSamba4WinsHost)'  # EA
	'(objectClass=univentionVirtualMachineGroupOC)'  # EA
	'(objectClass=univentionVirtualMachineHostOC)'  # EA
)
update_check_legacy_objects () {
	local var="update$VERSION/ignore_legacy_objects"
	ignore_check "$var" && return 100
	declare -a found_structural=() found_auxiliary=()
	local IFS=''
	local filter="(|${legacy_ocs_structural[*]})"
	IFS=$'\n' read -d '' -r -a found_structural <<<"$(univention-ldapsearch -LLL "$filter" 1.1 | grep '^dn:')"
	local filter="(|${legacy_ocs_auxiliary[*]})"
	IFS=$'\n' read -d '' -r -a found_auxiliary <<<"$(univention-ldapsearch -LLL "$filter" 1.1 | grep '^dn:')"

	# shellcheck disable=SC2128
	[ -z "$found_structural" ] && [ -z "$found_auxiliary" ] && return 0

	if [ -n "$found_structural" ]
	then
		echo "	The following objects are no longer supported with UCS-5:"
		local obj
		for obj in "${found_structural[@]}"
		do
			printf '\t\t%s\n' "${obj}"
		done
		echo "	They must be removed before the update can be done."
		echo
	fi
	if [ -n "$found_auxiliary" ]
	then
		echo "	The following objects contain auxiliary data no longer supported with UCS-5:"
		local obj
		for obj in "${found_auxiliary[@]}"
		do
			printf '\t\t%s\n' "${obj}"
		done
		echo "	They must be cleaned up before the update can be done."
		echo
	fi
	echo "	See <https://help.univention.com/t/16227> for details."
	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	return 1
}
delete_legacy_objects () {
	local filter ldif oc
	[ -r /etc/ldap.secret ] || die "Cannot get LDAP credentials from '/etc/ldap.secret'"

	echo "> Removing structural objects"
	for filter in "${legacy_ocs_structural[@]}"
	do
		echo ">> $filter"
		univention-ldapsearch -LLL "$filter" 1.1 |
			sed -ne 's/^dn: //p' |
			ldapdelete -x -D "cn=admin,${ldap_base:?}" -y /etc/ldap.secret -c
	done

	echo "> Removing auxiliary data"
	ldif="$(mktemp)"
	for filter in "${legacy_ocs_auxiliary[@]}"
	do
		echo ">> $filter"
		oc="${filter#(objectClass=}"  # the closing parenthesis is stripped below!
		univention-ldapsearch -LLL -b 'cn=Subschema' -s base objectClasses -E mv="${filter/objectClass=/objectClasses=}" >"$ldif"
		sed -rne 's/objectClasses: //;T;s/.* (MUST|MAY)//;s/ (MUST|MAY|[($)])//g;s/^ +| +$//g;s/ +/\n/g;s/\S+/replace: &\n-/g;a delete: objectClass\nobjectClass: '"${oc%)}" -e p -i "$ldif"
		[ -s "$ldif" ] || continue
		univention-ldapsearch -LLL "$filter" 1.1 |
			sed -e "/^dn: /r $ldif" |
			ldapmodify -x -D "cn=admin,${ldap_base:?}" -y /etc/ldap.secret -c
	done
	rm -f "$ldif"
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

# stop if md5 based "Signature Algorithm" is used in tls certificate
update_check_md5_signature_is_used () {
	local cert_path="/etc/univention/ssl/$hostname.$domainname/cert.pem"
	[ -f "$cert_path" ] || return 0

	local md5_indicator="Signature Algorithm: md5WithRSAEncryption"
	local certopt="no_header,no_version,no_serial,no_signame,no_subject,no_issuer,no_pubkey,no_aux,no_extensions,no_validity"
	openssl x509 -in "$cert_path" -text -certopt "$certopt" | grep --quiet "$md5_indicator" || return 0

	echo "	The pre-check of the update found that the certificate file:"
	echo "	$cert_path"
	echo "	is using md5 as the signature algorithm. This is not supported in"
	echo "	UCS ${VERSION_NAME} and later versions. The signature algorithm can be set"
	echo "	on the Primary Directory Node with:"
	echo "	ucr set ssl/default/hashfunction=sha256"
	echo "	The certificate needs to be renewed afterwards. Doing that is"
	echo "	described at:"
	echo "	<https://help.univention.com/t/37>"
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
    for dn, attrs in lo.search("(&(%s=*)(univentionOperatingSystem=Univention Corporate Server))" % ATTR, attr=[ATTR])
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
