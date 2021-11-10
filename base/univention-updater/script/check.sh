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

# Bug #53003
update_check_kolab_schema () {
	local var="update$VERSION/ignore_kolab_schema"
	ignore_check "$var" && return 100
	local status
	status=$(dpkg-query -W -f '${db:Status-Status}' "univention-legacy-kolab-schema" 2>/dev/null)
	if [ "$status" = "installed" ]; then
		echo " The package univention-legacy-kolab-schema is installed. This package is"
		echo " incompatible with UCS 5.0-0."
		echo
		echo " As the package contains a LDAP schema extension, this extension (a) has to"
		echo " registered in the LDAP database or (b) has to be removed before the update"
		echo " to UCS 5.0 is possible."
		echo
		echo " Note: These steps are only required on the Primary Node. On non-primary systems,"
		echo "       the package can be removed without step (a) or (b)."
		echo
		echo " (a) Register LDAP schema files from univention-legacy-kolab-schema:"
		echo "     To register the LDAP schema, run the following commands:"
		echo "     cat /usr/share/univention-ldap/schema/legacy/rfc2739.schema > /opt/kolab-legacy.schema"
		echo "     cat /usr/share/univention-ldap/schema/legacy/kolab2.schema >> /opt/kolab-legacy.schema"
		echo "     cat /usr/share/univention-ldap/schema/legacy/univention-kolab2.schema >> /opt/kolab-legacy.schema"
		echo "     cat /usr/share/univention-ldap/schema/legacy/kolab-legacy.schema >> /opt/kolab-legacy.schema"
		echo "     bash -c 'source /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension --packagename \"univention-legacy-kolab-schema\" --packageversion \"3.0.0-1.22.201309110849\" --schema /opt/kolab-legacy.schema'"
		echo
		echo " or (b) Remove the LDAP schema extension:"
		echo "        Please visit https://help.univention.com/t/6443 for how to remove LDAP schema extensions"
		echo "        (remove all attributes and objectclasses from that schema from the LDAP database)."
		echo
		echo " After either (a) or (b) has been completed, the package has to be removed from this server:"
		echo "  univention-remove --purge univention-legacy-kolab-schema"
		return 1
	fi
}

# Bug #53313
update_check_ox_schema () {
	status=$(dpkg-query -W -f '${db:Status-Status}' "univention-ox-directory-integration" 2>/dev/null)
	if [ "$status" = "installed" ]; then
		if ! is_ucr_true "ox/master/42/registered_ldap_acls"; then
			local convert_schema_script
			case "$server_role" in
				domaincontroller_master)
					convert_schema_script="/usr/share/univention-server-master/reregister_ox_ldap_schema.sh"
					;;
				domaincontroller_backup)
					convert_schema_script="/usr/share/univention-server-backup/reregister_ox_ldap_schema.sh"
					;;
				*)
					return 0
					;;
			esac
			echo " The package univention-ox-directory-integration is installed. This package is"
			echo " incompatible with UCS 5.0-0."
			echo
			echo " As the package contains a LDAP schema extension, this extension (a) has to"
			echo " registered in the LDAP database or (b) has to be removed before the update"
			echo " to UCS 5.0 is possible."
			echo
			echo " (a) Register LDAP schema files from univention-ox-directory-integration:"
			echo "     To register the LDAP schema, run the following commands:"
			echo "     \"$convert_schema_script\""
			echo
			echo " or (b) Remove the LDAP schema extension:"
			echo "        Please visit https://help.univention.com/t/6443 for how to remove LDAP schema extensions"
			echo "        (remove all attributes and objectclasses from that schema from the LDAP database)."
			echo
			echo " After either a) or b) has been completed, the package has to be removed from this server:"
			echo "  univention-remove --purge univention-ox-directory-integration"
			return 1
		else
			echo " The package univention-ox-directory-integration is installed. This package is"
			echo " incompatible with UCS 5.0-0."
			echo
			echo " The package has to be removed from this server:"
			echo "  univention-remove --purge univention-ox-directory-integration"
			return 1
		fi
	fi
}

# Bug #51955
update_check_old_packages () {
	local pkg status IFS=$'\n' var="update$VERSION/ignore_old_packages"
	ignore_check "$var" && return 100
	declare -a found=() old=(
		univention-kvm-compat
		univention-kvm-virtio'=Mark libvirt as manually installed "apt-mark manual libvirt-daemon" to keep virtualisation capabilities'
		univention-novnc
		univention-virtual-machine-manager-daemon
		python-univention-virtual-machine-manager
		python3-univention-virtual-machine-manager
		univention-management-console-module-uvmm
		univention-virtual-machine-manager-node-common
		univention-virtual-machine-manager-node-kvm
		univention-nagios-server
		univention-bacula
		univention-kde'=Mark KDE as manually installed "apt-mark manual kde-standard" to keep KDE'
		univention-kde-setdirs
		univention-kdm
		univention-mozilla-firefox
		univention-x-core
		univention-samba-slave-pdc
		univention-dansguardian
		univention-printquota
		univention-passwd-store
		univention-corporate-client-schema
		univention-ox-dependencies-master
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
	echo "Use \"univention-remove --purge\" with the packages as following arguments to remove them"
	return 1
}

# Bug #51497 #51973 #31048 #51655 #51955 #51982 #51482
# Admin must agree to remove these:
declare -a legacy_ocs_structural=(
	# UCC:
	'(structuralObjectClass=univentionPolicyCorporateClientUser)'
	'(structuralObjectClass=univentionCorporateClientSession)'
	'(structuralObjectClass=univentionCorporateClientAutostart)'
	'(structuralObjectClass=univentionCorporateClientImage)'
	'(structuralObjectClass=univentionPolicyCorporateClientComputer)'
	'(structuralObjectClass=univentionPolicyCorporateClientDesktop)'
	'(structuralObjectClass=univentionPolicySoftwareupdates)'
	'(structuralObjectClass=univentionPolicyCorporateClient)'
)
declare -a legacy_ocs_auxiliary=(
	'(objectClass=univentionSamba4WinsHost)'  # EA
	'(objectClass=univentionCorporateClient)'
)
# These are auto-removed:
declare -a obsolete_objectclasses=(
	'(structuralObjectClass=univentionAdminUserSettings)'
	'(structuralObjectClass=univentionPolicySharePrintQuota)'
	'(structuralObjectClass=univentionXConfigurationChoices)'
	'(structuralObjectClass=univentionMailQuota)'
	# UCS TCS:
	'(structuralObjectClass=univentionPolicyAutoStart)'
	'(structuralObjectClass=univentionPolicyThinClient)'
	'(objectClass=univentionThinClient)'
	'(objectClass=univentionMobileClient)'
	'(objectClass=univentionFatClient)'
)

update_check_legacy_objects () {
	local var="update$VERSION/ignore_legacy_objects"
	ignore_check "$var" && return 100
	[ -f /var/univention-join/joined ] || return 0

	declare -a found_structural=() found_auxiliary=()
	local IFS=''

	local filter="(|${legacy_ocs_structural[*]})"
	univention-ldapsearch -LLL "$filter" 1.1 >"$tmp" || die "Failed to search LDAP"
	IFS=$'\n' read -d '' -r -a found_structural <<<"$(grep '^dn:' "$tmp")"

	local filter="${legacy_ocs_auxiliary[*]}"
	univention-ldapsearch -LLL -E mv="($filter)" "(|$filter)" objectClass >"$tmp" || die "Failed to search LDAP"
	IFS=$'\n' read -d '' -r -a found_auxiliary <<<"$(sed '/^./{H;d};x;s/\n/\t/g' "$tmp")"

	# shellcheck disable=SC2128
	[ -z "${found_structural:-}" ] && [ -z "${found_auxiliary:-}" ] && return 0

	if [ -n "${found_structural:-}" ]
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
	if [ -n "${found_auxiliary:-}" ]
	then
		echo "	The following objects contain auxiliary data no longer supported with UCS-5:"
		local obj
		for obj in "${found_auxiliary[@]}"
		do
			printf '\t%s\n' "${obj}"
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

# Some objects get deleted automatically in preup.sh
# Objects are found by queries based on obsolete_objectclasses
# references to these deleted objects are also deleted if the
# reference is in an attribute named univentionPolicyReference or
# univentionPolicyObject
delete_obsolete_objects () {
	[ "$server_role" != "domaincontroller_master" ] && return 0
	[ -r /etc/ldap.secret ] || die "ERROR: Cannot get LDAP credentials from '/etc/ldap.secret'"
	[ -d "${updateLogDir:?}" ] ||
		install -m0700 -o root -d "$updateLogDir" ||
		die "ERROR: Could not create $updateLogDir"
	local filter ldif oc backupfile
	backupfile="${updateLogDir}/removed_with_ucs5_$(date +%Y-%m-%d-%S).ldif"

	echo "> Several LDAP objects are no longer supported with UCS 5 and are removed automatically."
	echo "> An LDIF file of removed objects is available: ${backupfile}"
	install -b -m 400 /dev/null "${backupfile}"
	echo "> Removing objects with obsolete objectClasses"
	for filter in "${obsolete_objectclasses[@]}"
	do
		echo ">> $filter"
		# check if object is referenced anywhere in a policy
		local object_dns
		object_dns="$(univention-ldapsearch -LLL "$filter" | sed -ne 's/^dn: //p')"
		[ -z "$object_dns" ] && continue
		echo "Deleting object(s) with dn: $object_dns"
		# Iterate over all found objects matching the ldap filter to find references
		while IFS= read -r object_dn; do
			# References to objects can come in two attributes
			for policy_reference_type in univentionPolicyReference univentionPolicyObject; do
				local policy_references dn="$object_dn"
				dn="${dn//\\/\\5c}"
				dn="${dn//\*/\\2a}"
				dn="${dn//\(/\\28}"
				dn="${dn//\)/\\29}"
				policy_references="$(univention-ldapsearch -LLL "($policy_reference_type=$dn)" 1.1 | sed -ne 's/^dn: //p')"
				[ -z "$policy_references" ] && continue
				while read -r referencing_dn; do
					echo "# Deleting reference to $object_dn from $referencing_dn" | tee -a "${backupfile}"
					ldapmodify -x -D "cn=admin,${ldap_base:?}" -y /etc/ldap.secret <<__EOF__
dn: $referencing_dn
changetype: modify
delete: $policy_reference_type
$policy_reference_type: $object_dn
__EOF__
				done <<< "$policy_references"
			done # for policy_reference_type
		done <<< "$object_dns" # while read object_dn
		univention-ldapsearch -LLL "$filter" "*" + |
			tee -a "${backupfile}" |
			sed -ne 's/^dn: //p' |
			ldapdelete -x -D "cn=admin,${ldap_base:?}" -y /etc/ldap.secret -c || die 'ERROR: could not remove obsolete objects'
	done
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

# Bug 53129: check defaultPackagesMaster of kopano-core and openvpn4ucs
update_check_default_master_packages () {
	[ "$server_role" != "domaincontroller_master" ] && return 0
	[ -f /var/univention-join/joined ] || return 0
	local var="update$VERSION/ignore_default_master_packages_apps"
	local ret=0
	ignore_check "$var" && return 100
	# kopano-core
	status=$(dpkg-query -W -f '${db:Status-Status}' "kopano4ucs-udm" 2>/dev/null)
	if [ "$status" = 'installed' ]; then
		echo
		echo "  The Kopano App is or was installed in your domain."
		echo "  A newer version of the Kopano App is needed in order to update to UCS 5.0."
		echo "  Kopano and Univention are currently working on providing this new version"
		echo "  as soon a possible."
		echo
		echo "  If the Kopano App is no longer used and has already been removed from the domain"
		echo "  the package kopano4ucs-udm can be removed from this server"
		echo "  in order to update to UCS 5.0: univention-remove --purge kopano4ucs-udm"
		echo
		echo "  This check can be disabled by setting the UCR variable '$var' to 'yes'."
		# once the update is available, we can change the message to something like
		#echo "The Kopano App is installed in your domain."
		#echo "In order to update to UCS 5.0 the Kopano App has to be updated to"
		#echo "version x.x. Once all systems are updated the package"
		#echo "  kopano4ucs-udm"
		#echo "has to be removed from this server: univention-remove --purge kopano4ucs-udm"
		ret=1
	fi
	return $ret
}

# Bug #52771: check if apps are available
update_check_blocking_apps () {
	local var="update$VERSION/ignore_blocking_apps"
	ignore_check "$var" && return 100
	[ -f /var/univention-join/joined ] || return 0
	univention-app update-check --ucs-version "${VERSION_NAME}"
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

update_check_tls_public_key_size () {  # Bug #53013
	local min_key_size=2048
	local fqdn=${1:-"$hostname.$domainname"}
	local cert_path="/etc/univention/ssl/$fqdn/cert.pem"
	[ -f "$cert_path" ] || return 0

	local rsa_indicator="Public Key Algorithm: rsaEncryption"
	local certopt="no_header,no_version,no_serial,no_signame,no_subject,no_issuer,no_aux,no_extensions,no_validity,no_sigdump"
	openssl x509 -in "$cert_path" -text -certopt "$certopt" | grep --quiet "$rsa_indicator" || return 0
	local key_size
	key_size="$(openssl x509 -noout -text -certopt "$certopt" -in "$cert_path" | grep 'Public-Key: (.* bit)' | grep -oE '[0-9]+')"
	[ "$key_size" -lt "$min_key_size" ] || return 0

	echo "	The pre-check of the update found that the certificate file:"
	echo "	$cert_path"
	echo "	is using a public key smaller ${min_key_size} bits. This is not supported in"
	echo "	UCS ${VERSION_NAME} and later versions. The public key bit size can be set"
	echo "	on the Primary Directory Node with:"
	echo "	ucr set ssl/default/bits=2048"
	echo "	The certificate needs to be recreated afterwards."
	echo "	A new certificate with a new public key can be created on the"
	echo "	Primary Directory Node with:"
	echo "	univention-certificate new -name ${fqdn}"
	echo "	Afterwards follow the help article below,"
	echo "	as like the certificate had been renewed:"
	echo "	<https://help.univention.com/t/37>"
	return 1
}

update_check_tls_public_key_size_ucs-sso () {  # Bug #53013
	update_check_tls_public_key_size "$ucs_server_sso_fqdn"
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

update_check_architecture () {  # Bug #51972
	local arch
	arch="$(dpkg --print-architecture)"
	case "$arch" in
	amd64) return 0 ;;
	esac

	echo "	The architecture '$arch' is no longer supported."
	echo "	Please setup a new system with an architecture 'amd64'."
	return 1
}

update_check_samba_server_schannel () {  # Bug #49898
	[ -x /usr/bin/testparm ] ||
		return 0
	server_schannel=$(testparm -sv 2>/dev/null | sed -n 's/\t*server schannel = //p')
	if [ "$server_schannel" != "Yes" ]; then
		echo "WARNING: Samba is configured with \"server schannel = ${server_schannel,,}\","
		echo "         This is extremely dangerous, see https://www.samba.org/samba/security/CVE-2020-1472.html"
		echo "         Please take care to change this back to \"yes\" before updating."

		if is_ucr_true update50/ignore_server_schannel; then
			echo "WARNING: update50/ignore_server_schannel is set to true. Continue as requested."
		else
			return 1
		fi
	fi
}

update_check_adc_mapping () {  # Bug #52044
	local tmpoutput
	local md5sum_expected
	if [ "$(dpkg --verify univention-ad-connector 2>/dev/null | grep /etc/univention/connector/ad/mapping | cut -c 3)" = "5" ]; then
		tmpoutput=$(dpkg-query -W -f='${Conffiles}\n' univention-ad-connector)
		md5sum_expected=$(sed -n 's|^ /etc/univention/connector/ad/mapping \(.*\)$|\1|p' <<<"$tmpoutput")
		echo "WARNING: The AD-Connector mapping UCR template file has been modified locally."
		echo "         The file /etc/univention/connector/ad/mapping doesn't have the original md5 sum (expected: $md5sum_expected)."
		echo "         It needs to be reverted to the original and the adjusted mapping should be converted into a python file"
		echo "         named /etc/univention/connector/ad/localmapping.py which must define a function named \"mapping_hook\""
		echo "         which receives the original ad_mapping as argument and must return a (possibly customized) ad_mapping"
		echo "         (See also https://docs.software-univention.de/manual-4.4.html#windows:groups:CustomMappings)."
		echo "         "
		echo "         Please also note that the mapping code needs to be compatible with Python 3.7"
		echo "         (See also https://docs.software-univention.de/developer-reference-5.0.html)."
		if is_ucr_true update50/ignore_adc_mapping; then
			echo "WARNING: update50/ignore_adc_mapping is set to true. Continue as requested."
		else
			return 1
		fi
	fi
}

update_check_adc_multiinstance_mapping () {  # Bug #53103
	local var="update$VERSION/ignore_multi_adc_mapping"
	local tocheck

	eval "$(ucr shell connector/listener/additionalbasenames)"
	for CONFIGBASENAME in $connector_listener_additionalbasenames; do
		if ! [ -d /etc/univention/"$CONFIGBASENAME" ]; then
			continue
		fi
		if grep -sq mapping_hook /etc/univention/"$CONFIGBASENAME/ad/localmapping.py"; then
			continue
		fi
		tocheck="$tocheck $CONFIGBASENAME"
		echo "WARNING: There are additional AD-Connector mappings (registered in UCR connector/listener/additionalbasenames)"
		echo "         It needs to be converted into a python file named /etc/univention/$CONFIGBASENAME/ad/localmapping.py"
		echo "         which must define a function named \"mapping_hook\"which receives the original ad_mapping as argument"
		echo "         and must return a (possibly customized) ad_mapping. See https://help.univention.com/t/17754 for details."
	done
	if [ -n "$tocheck" ]; then
		if is_ucr_true update50/ignore_multi_adc_mapping; then
			echo "WARNING: $var is set to true. Continue as requested."
		else
			return 1
		fi
	fi
}

## Check for PostgreSQL-9.4 (Bug #53034)
update_check_for_postgresql94 () {
	local var="update$VERSION/ignore_postgresql94"
	ignore_check "$var" && return 100

	case "$(dpkg-query -W -f '${Status}' postgresql-9.4 2>/dev/null)" in
	install*) ;;
	*) return 0 ;;
	esac

	echo "WARNING: PostgreSQL-9.4 is no longer supported by UCS-5.0 and must be migrated to"
	echo "         a newer version of PostgreSQL. See https://help.univention.com/t/8075 for"
	echo "         more details."

	echo
	echo "	This check can be disabled by setting the UCR variable '$var' to 'yes'."
	echo "	But be aware that this is not recommended!"

	return 1
}

update_check_samba_tdb_size () {  # Bug #53212
	local var="update$VERSION/ignore_samba_tdb_size"
	local fpath
	local rc=0

	if ! dpkg -l univention-samba4 2>/dev/null | grep -q ^ii; then
		return 0
	fi
	for p in $(ldbsearch -H /var/lib/samba/private/sam.ldb  -b '@PARTITION' -s base partition | ldapsearch-wrapper | sed -n 's/partition: //p'); do
		fpath="/var/lib/samba/private/${p#*:}"
		if file -b "$fpath" | grep -q "^TDB database" && [ "$(stat -c %s "$fpath")" -gt 1950000000 ]; then
			echo "WARNING: The Samba SAM database is very large. During update Samba will convert the database"
			echo "         to a new database and index format. For that step Samba requires temporary duplication"
			echo "         of the database content, which may result in an overflow of the maximal size of the tdb"
			echo "         database of 4GB. This may result in Samba not starting after the update."
			echo "         To avoid this and make Samba scale to even larger numbers of accounts re recommend"
			echo "         to convert the SAM database key-value backend from TDB to LMDB. That's the technology"
			echo "         that UCS uses for OpenLDAP and has shown an exceptional robustness and performance."
			echo "         "
			echo "         The article https://help.univention.com/t/18014 describes the required steps."
			rc=1
			break
		fi
	done
	if is_ucr_true "$var"; then
		echo "WARNING: $var is set to true. Continue as requested."
	else
		return $rc
	fi
}

update_check_python_ucr_template_compatibility () {
	local var="update$VERSION/ignore-python3-compatiblity-ucr-templates"
	ignore_check "$var" && return 100

	/usr/bin/python2.7 - <<EOF
#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import atexit
import shutil
import tempfile
import subprocess

from univention.config_registry.handler import EXECUTE_TOKEN

BASE_DIR = "/etc/univention/templates/files/"

def dpkg():
	etc = {}
	cmd_dpkg = ["dpkg", "-S", os.path.join(BASE_DIR, '*')]
	proc = subprocess.Popen(cmd_dpkg, stdout=subprocess.PIPE)
	for line in proc.stdout:
		pkg, fn = line.decode('UTF-8', 'replace').strip().split(': ')
		etc[fn] = pkg
	return etc


def uninstalled(package):
	try:
		out = subprocess.check_output(['dpkg-query', '-W', '-f', '\${Status}', package], env={'LANG': 'C'})
	except subprocess.CalledProcessError:
		return False
	return out.decode('UTF-8', 'replace').startswith('deinstall ')


def get_registered_files():
	files = []
	registered_directory = '/etc/univention/templates/info/'
	for f in os.listdir(registered_directory):
		for line in open(os.path.join(registered_directory, f), 'r').readlines():
			if line.startswith('File: '):
				fn = line.replace('File: ', '').strip()
				files.append(BASE_DIR + fn)
			elif line.startswith('Subfile: '):
				fn = line.replace('Subfile: ', '').strip()
				files.append(BASE_DIR + fn)

	return files


def cleanup(tmpdir):
	shutil.rmtree(tmpdir, True)


os.umask(0o077)
tmpdir = tempfile.mkdtemp()
atexit.register(cleanup, tmpdir)
tempfiles = [
	path
	for path in (
		os.path.join(path, filename)
		for path, dirs, files in os.walk(BASE_DIR)
		for filename in files
	) if EXECUTE_TOKEN.search(open(path, 'rb').read())
]
registered_files = get_registered_files()
failed = []
for ucr_config_file in tempfiles:
	if ucr_config_file not in registered_files:
		continue
	with open(ucr_config_file, 'rb') as fd:
		template = fd.read()

	num = 0
	while True:
		i = EXECUTE_TOKEN.finditer(template)
		num += 1
		try:
			start = next(i)
			end = next(i)

			ucr_temp_file = os.path.join(tmpdir, '%s%d.py' % (os.path.basename(ucr_config_file), num))
			with open(ucr_temp_file, 'wb') as fd:
				fd.write(b'''\
# -*- coding: utf-8 -*-
import univention.config_registry
configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
# for compatibility
baseConfig = configRegistry
%s
''' % template[start.end():end.start()])
			ret = subprocess.call(
				('/usr/bin/python3', '-m', 'py_compile', ucr_temp_file),
				stdout=open('/dev/null', 'a'), stderr=subprocess.STDOUT,
				close_fds=True)
			template = template[end.end():]

			if ret:
				failed.append(ucr_config_file)
				break

		except StopIteration:
			break

if failed:
	packages = dpkg()
failed = [p for p in failed if not packages.get(p) or not uninstalled(packages[p])]
if failed:
	print('The following UCR templates are not compatible with Python 3:')
for failed_template in failed:
	print('\\t', failed_template, end='')
	if failed_template in packages:
		print(' (package: %s)' % (packages[failed_template], ), end='')
	print('')
	print('See <https://help.univention.com/t/17948> for information on how to proceed with each template.')
if failed:
	exit(1)
EOF
}

update_check_python_ucsschool_hooks_compatibility() {
	local var="update$VERSION/ignore-python3-compatiblity-ucsschool-hooks"
	ignore_check "$var" && return 100

	/usr/bin/python2.7 - <<EOF
#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import atexit
import shutil
import tempfile
import subprocess


def dpkg(files):
	etc = {}
	cmd_dpkg = ["dpkg", "-S"] + files
	proc = subprocess.Popen(cmd_dpkg, stdout=subprocess.PIPE)
	for line in proc.stdout:
		pkg, fn = line.decode('UTF-8', 'replace').strip().split(': ')
		etc[fn] = pkg
	return etc


def uninstalled(package):
	try:
		out = subprocess.check_output(['dpkg-query', '-W', '-f', '\${Status}', package], env={'LANG': 'C'})
	except subprocess.CalledProcessError:
		return False
	return out.decode('UTF-8', 'replace').startswith('deinstall ')


def get_registered_files():
	for dir in ('/usr/share/ucs-school-import/checks/', '/usr/share/ucs-school-import/pyhooks/', '/var/lib/ucs-school-lib/hooks/'):
		for path, directories, files in os.walk(dir):
			for file in files:
				if not file.endswith('.py'):
					continue
				yield os.path.join(path, file)


registered_files = list(get_registered_files())
failed = []
for hook in registered_files:
	ret = subprocess.call(('/usr/bin/python3', '-m', 'py_compile', hook), stdout=open('/dev/null', 'a'), stderr=subprocess.STDOUT, close_fds=True)
	if ret:
		failed.append(hook)

if failed:
	packages = dpkg(failed)
failed = [p for p in failed if not packages.get(p) or not uninstalled(packages[p])]
if failed:
	print('The following UCS@school Hooks are not compatible with Python 3:')
for failed_hook in failed:
	print('\\t', failed_hook, end='')
	if failed_hook in packages:
		print(' (package: %s)' % (packages[failed_hook], ), end='')
	print('')
if failed:
	exit(1)
EOF
}

update_check_ucsschool_computerroom_compatibility() {
	local var="update$VERSION/ignore-ucsschool-computerroom-compatibility"
	ignore_check "$var" && return 100
	/usr/bin/python2.7 - <<EOF
#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

import univention.admin.uldap
import univention.config_registry

try:
	from ucsschool.lib.models.school import School
	from ucsschool.lib.models.group import ComputerRoom
except ImportError:
	# import error means no ucsschool is installed
	exit(0)

lo, po = univention.admin.uldap.getMachineConnection()
ucr = univention.config_registry.ConfigRegistry()
ucr.load()
edu_dc_dns = lo.getAttr("cn=DC-Edukativnetz,cn=ucsschool,cn=groups,{}".format(ucr["ldap/base"]), "uniqueMember")
host_dn = ucr['ldap/hostdn']
if ucr.is_true("ucsschool/singlemaster", False) or (host_dn in edu_dc_dns):
	# host is replica in a multi-server environment or a single server
	computerroom_dns = []
	for school in School.get_all(lo):
			rooms = ComputerRoom.get_all(lo, school.name)
			computerroom_dns.extend([room.dn for room in rooms])

	if computerroom_dns:
		print("Updating to UCS@school 5.0 with computer rooms is not yet supported. An update, which enables this, will follow.")
		print("The following UCS@school computer room objects prevent the upgrade to UCS@school 5.0:\n")
		for dn in computerroom_dns:
			print("\t\t{}".format(dn))
		print("\nINFO: In preparation for this upgrade, all computer rooms, which are configured to have iTALC as it's backend, should be migrated to Veyon.")
		print("iTALC computer rooms will still be usable in mixed environments with the primary upgraded to UCS@school 5.0 with school replica nodes running UCS@school 4.4. iTALC computer rooms won't be usable in UCS@school 5.0 replica nodes.")
		print("Please visit https://help.univention.com/t/16937 for more information.")
		exit(1)
EOF
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
