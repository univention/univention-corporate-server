#!/bin/bash
# shellcheck shell=bash

# shellcheck disable=SC2089,SC2090

# shellcheck source=base.sh
. "$TESTLIBPATH/base.sh" || exit 137
# shellcheck source=ldap.sh
. "$TESTLIBPATH/ldap.sh" || exit 137

# shellcheck disable=SC2034
UDM_ALL_COMPUTER_ROLES="computers/domaincontroller_backup
computers/domaincontroller_master
computers/domaincontroller_slave
computers/ipmanagedclient
computers/macos
computers/memberserver
computers/linux
computers/ubuntu
computers/windows
computers/windows_domaincontroller"

udm_get_identifier_attribute () {
	local module="$1"

	case "$module" in
		dhcp/host)
			echo "host"
			;;
		dhcp/server)
			echo "server"
			;;
		dhcp/service)
			echo "service"
			;;
		dhcp/sharedsubnet|dhcp/subnet|dns/reverse_zone)
			echo "subnet"
			;;
		dns/forward_zone)
			echo "zone"
			;;
		dns/ptr_record)
			echo "address"
			;;
		settings/user|users/user)
			echo "username"
			;;
		*)
			echo "name"
			;;
	esac
}

udm_get_ldap_identifier_qualifier () {
	local module="$1"

	case "$module" in #This is probably not complete
		container/ou)
			echo "ou"
			;;
		dns/forward_zone|dns/reverse_zone)
			echo "zoneName"
			;;
		dns/host_record|dns/ptr_record|dns/srv_record|dns/alias)
			echo "relativeDomainName"
			;;
		settings/sambadomain)
			echo "sambaDomainName"
			;;
		users/user)
			echo "uid"
			;;
		*)
			echo "cn"
			;;
	esac
}

udm_get_udm_filter_qualifier () {
	local module="$1"

	case "$module" in #This is probably not complete
		*)
			udm_get_ldap_identifier_qualifier "$module"
			;;
	esac
}

udm_get_ldap_prefix () {
	local module="$1"

	case "$module" in #This is probably not complete
		computers/*)
			echo "cn=computers,"
			;;
		dns/forward_zone|dns/reverse_zone)
			echo "cn=dns,"
			;;
		dhcp/service)
			echo "cn=dhcp,"
			;;
		groups/group)
			echo "cn=groups,"
			;;
		networks/network)
			echo "cn=networks,"
			;;
		users/user)
			echo "cn=users,"
			;;
		settings/extended_attribute|settings/customattribute)
			echo "cn=custom attributes,cn=univention,"
			;;
		policies/dhcp_*)
			echo "cn=${module#policies/dhcp_},cn=dhcp,cn=policies,"
			;;
		policies/pwhistory)
			echo "cn=pwhistory,cn=users,cn=policies,"
			;;
		*)
			echo ""
			;;
	esac
}

udm_get_module_variable_prefix () {
	local module="$1"

	module="${module//\//_}"
	module="${module//-/_}"

	echo "UDM_${module}_"
}

udm_get_identifier_value () {
	local module="$1" variableprefix="${2:-$(udm_get_module_variable_prefix "$1")}"

	local idattr
	idattr=$(udm_get_identifier_attribute "$module")

	local a=
	eval "a=\$$variableprefix${idattr//-/_}"
	echo "$a"
}

udm_get_attribute_list () {
	local module="$1"

	local attributelist=
	eval "attributelist=\$_$(udm_get_module_variable_prefix "$module")_ATTRIBUTE_LIST"

	if [ -z "$attributelist" ]; then
		attributelist="$(udm_get_plain_module_attributes "$module")"
	fi

	echo "$attributelist"
}

udm_get_required_attribute_list () {
	local module="$1"

	local attributelist=
	eval "attributelist=\$_$(udm_get_module_variable_prefix "$module")_REQUIRED_ATTRIBUTE_LIST"

	if [ -z "$attributelist" ]; then
		attributelist="$(udm_get_required_module_attributes "$module")"
	fi

	echo "$attributelist"
}

udm_reset_params () {
	local module="$1" variableprefix="${2:-$(udm_get_module_variable_prefix "$1")}"

	for attr in $(udm_get_attribute_list "$module"); do
		eval '$variableprefix${attr//-/_}='
	done
}

log_and_eval_execute () {
	info "EXECUTING: $*"
	eval "$@"
}

_udm_args () {
	module="$1"
	variableprefix="${2:-$(udm_get_module_variable_prefix "$1")}"
	superordinate="$3"
	ldaplocation="${4:-$3}"
	objectname="${5:-$(udm_get_identifier_value "$module" "$variableprefix")}"
}

udm_exists () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"

	local dn
	dn="$(udm_get_ldap_identifier_qualifier "$module")=$objectname,${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}"
	# shellcheck disable=SC2016
	local cmd="udm-test '$module' list ${superordinate:+--superordinate '$superordinate'} | grep -Fx 'DN: $dn'"

	if log_and_eval_execute "$cmd"; then
		info "$module object $objectname exists"
		return 0
	else
		info "$module object $objectname does not exist"
		return 1
	fi
}

udm_create () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"
	shift
	shift
	shift
	shift
	shift

	# shellcheck disable=SC2016
	local cmd="udm-test '$module' create ${superordinate:+--superordinate '$superordinate'}"
	cmd+=" --position '${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}'"

	local params=
	local var=
	for attr in $(udm_get_attribute_list "$module"); do
		eval "var=\$$variableprefix${attr//-/_}"
		if [ -n "$var" ]; then
			params+=" --set '$attr'='$var'"
		fi
	done

	# shellcheck disable=SC2086,SC2068
	if log_and_eval_execute "$cmd $params $*"; then
		info "created $module object $objectname"
		return 0
	else
		info "failed creating $module object $objectname"
		return 1
	fi
}

udm_modify () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"
	shift
	shift
	shift
	shift
	shift

	# shellcheck disable=SC2016
	local cmd="udm-test '$module' modify ${superordinate:+--superordinate '$superordinate'}"
	cmd+=" --dn '$(udm_get_ldap_identifier_qualifier "$module")=$objectname,${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}'"

	# shellcheck disable=SC2068,SC2086
	if log_and_eval_execute "$cmd $*"; then
		info "$module object $objectname modified"
		return 0
	else
		info "failed modifying $module object $objectname"
		return 1
	fi
}

udm_remove () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"
	shift
	shift
	shift
	shift
	shift

	# shellcheck disable=SC2016
	local cmd="udm-test '$module' remove ${superordinate:+--superordinate '$superordinate'}"
	cmd+=" --dn '$(udm_get_ldap_identifier_qualifier "$module")=$objectname,${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}'"

	# shellcheck disable=SC2068,SC2086
	if log_and_eval_execute "$cmd $*"; then
		info "removed $module object $objectname"
		return 0
	else
		info "failed removing $module object $objectname"
		return 1
	fi
}

udm_ldap_remove () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"
	ldap_delete "$(udm_get_ldap_identifier_qualifier "$module")=$objectname,${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}"
}

udm_purge () {
	if ! udm_remove "$@" --remove_referring ||
		udm_exists "$@"
	then
		warning "Cleanup via udm failed"
		udm_ldap_remove "$@" ||
			warning "Cleanup via ldapdelete failed as well"
	fi
}

udm_get_required_module_attributes () {
	local module="$1"
	udm-test "$module" | sed -ne '\#'"$module"' variables:#,${/:$/d;/^\$/d;s/^\t\t\(\S\+\) (\(\S+,\)\?\<c\>\(,\S\+\)\?).*/\1/p}'
}

udm_get_plain_module_attributes () {
	local module="$1"
	udm-test "$module" | sed -ne '\#'"$module"' variables:#,${/:$/d;/^\$/d;s/^\t\t\(\S\+\) .*/\1/p}'
}

udm_get_ldap_attribute () {
	local attributename="$1" module variableprefix superordinate ldaplocation objectname
	shift
	_udm_args "$@"

	local branch
	branch="$(udm_get_ldap_identifier_qualifier "$module")=$objectname,${ldaplocation:-$(udm_get_ldap_prefix "$module")$ldap_base}"

	log_and_eval_execute "ldapsearch -xLLL -D 'cn=admin,$ldap_base' -y /etc/ldap.secret -b '$branch' '$attributename' | VAL '$attributename'"
}

udm_has_object_class () {
	local objectclass="$1"
	shift

	local objectclasses
	objectclasses="$(udm_get_ldap_attribute objectClass "$@")"

	local IFS="
"
	for class in $objectclasses; do
		if [ "$class" == "$objectclass" ]; then
			info "'$module'-object '$objectname' has objectclass '$objectclass'"
			return 0
		fi
	done

	info "'$module'-object '$objectname' doesn't have objectclass '$objectclass'"
	return 1
}

udm_verify_ldap_attribute () {
	local attribute="$1" expected_value="$2"
	shift 2

	local value
	value="$(udm_get_ldap_attribute "$attribute" "$@")"
	verify_value "$attribute" "$value" "$expected_value"
}

udm_verify_ldap_attributes () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"
	shift
	shift
	shift
	shift
	shift

	local attr=
	local switch=attr
	for elem in "$@"; do
		if [ "$switch" = "attr" ]; then
			switch=value
			attr="$elem"
		else
			switch=attr
			udm_verify_ldap_attribute "$attr" "$elem" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" ||
				return 1
		fi
	done
	return 0
}

udm_get_udm_attribute () {
	local attribute="$1" module variableprefix superordinate ldaplocation objectname
	shift
	_udm_args "$@"

	local cmd="udm-test '$module' list"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi
	cmd+=" --filter '$(udm_get_udm_filter_qualifier "$module")=$objectname' | sed -nre 's/^ *${attribute}: //p'"

	log_and_eval_execute "$cmd"
}

udm_verify_udm_attribute () {
	local attribute="$1" expected_value="$2"
	shift 2

	local value
	value="$(udm_get_udm_attribute "$attribute" "$@")"

	verify_value "$attribute" "$value" "$expected_value"
}

udm_verify_multi_value_udm_attribute_contains_ignore_case () {
	local attribute="$1" expected_value="$2"
	shift 2

	local value
	value="$(udm_get_udm_attribute "$attribute" "$@")"

	verify_value_contains_line_ignore_case "$attribute" "$value" "$expected_value"
}

udm_verify_multi_value_udm_attribute_contains () {
	local attribute="$1" expected_value="$2"
	shift 2

	local value
	value="$(udm_get_udm_attribute "$attribute" "$@")"

	verify_value_contains_line "$attribute" "$value" "$expected_value"
}

udm_verify_udm_attributes () {
	local module variableprefix superordinate ldaplocation objectname
	_udm_args "$@"

	local attr var=
	for attr in $(udm_get_attribute_list "$module"); do
		eval "var=\$$variableprefix${attr//-/_}"
		if [ -n "$var" ]; then
			udm_verify_udm_attribute "$attr" "$var" "$@" ||
				return 1
		fi
	done
	return 0
}

udm_check_required_singlevalue_attribute () {
	local attribute="$1" value1="$2" value2="$3"
	shift 3

	local expected_value="$value1"
	if ! udm_modify "$@" --set \""$attribute=$value1"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Singlevalue attribute '$attribute': Setting initial value failed"
		return 1
	fi

	expected_value="$value1"
	if udm_modify "$@" --append \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Singlevalue attribute '$attribute': Appending second value succeeded"
		return 1
	fi

	expected_value="$value2"
	if ! udm_modify "$@" --set \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Singlevalue attribute '$attribute': Overwriting previous value failed"
		return 1
	fi

	return 0
}

udm_check_singlevalue_attribute () {
	local attribute="$1" value1="$2" value2="$3"
	shift 3

	udm_check_required_singlevalue_attribute "$attribute" "$value1" "$value2" "$@" ||
		return 1

	expected_value="None"
	if ! udm_modify "$@" --remove \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Singlevalue attribute '$attribute': Removing value failed"
		return 1
	fi

	return 0
}

udm_check_multivalue_attribute () {
	local attribute="$1" value1="$2" value2="$3" value3="$4"
	shift 4

	local expected_value="$value1"
	if ! udm_modify "$@" --set \""$attribute=$value1"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Multivalue attribute '$attribute': Setting initial value failed"
		return 1
	fi

	local expected_value="$value1
$value2
$value3"
	if ! udm_modify "$@" \
			--append \""$attribute=$value2"\" --append \""$attribute=$value3"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$@"
	then
		info "Multivalue attribute '$attribute': Appending two values failed"
		return 1
	fi

	expected_value="$value1
$value3"
	if ! udm_modify "$@" --remove \""$attribute"\"=\""$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Multivalue attribute \"$attribute\": Removing middle value failed"
		return 1
	fi

	expected_value="$value1"
	if ! udm_modify "$@" --remove \""$attribute"\"=\""$value3"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" "$@"
	then
		info "Multivalue attribute \"$attribute\": Removing last value failed"
		return 1
	fi

	return 0
}

udm_check_flag_attribute () {
	local attribute="$1"
	shift
	udm_check_required_singlevalue_attribute "$attribute" "0" "1" "$@"
}

udm_check_syntax_for_attribute () {
	local attribute="$1" valid1="$2" valid2="$3" invalid="$4" customcliname="${10}"
	shift 4
	set -- "$1" "$2" "$3" "$4" "$5"

	if [ -n "$customcliname" ]; then
		local set="--customattribute"
	else
		customcliname="$attribute"
		local set="--set"
	fi

	if ! udm_create "$@" "$set" \""$customcliname"\"="$valid1" ||
		! udm_exists "$@" ||
		! udm_verify_udm_attribute "$attribute" "$valid1" "$@"
	then
		udm_purge "$@"
		warning "Syntax check for attribute \"$attribute\": Creation with correct syntax failed."
		return 1
	fi

	if ! udm_modify "$@" "$set" \""$customcliname"\"="$valid2" ||
		! udm_verify_udm_attribute "$attribute" "$valid2" "$@"
	then
		udm_purge "$@"
		warning "Syntax check for attribute \"$attribute\": Modification with correct syntax failed."
		return 1
	fi

	if udm_modify "$@" "$set" \""$customcliname"\"="$invalid" ||
		! udm_verify_udm_attribute "$attribute" "$valid2" "$@"
	then
		udm_purge "$@"
		warning "Syntax check for attribute \"$attribute\": Modification with incorrect syntax succeeded."
		return 1
	fi

	udm_purge "$@"

	if udm_create "$@" "$set" \""$customcliname"\"="$invalid"
	then
		udm_purge "$@"
		warning "Syntax check for attribute \"$attribute\": Creation with incorrect syntax succeeded."
		return 1
	fi

	return 0
}

udm_kill_univention_cli_server () {
	pkill --echo --full univention-cli-server
}

_UDM_HOOK_FOLDER="/usr/lib/python3/site-packages/univention/admin/hooks.d"
_UDM_HOOK_NAME="ucs_test_hook.py"
udm_extended_attribute_install_hook () {
	local hook="$1"
	local hookname="${2:-$_UDM_HOOK_NAME}"
	local hookfolder="${3:-$_UDM_HOOK_FOLDER}"

	info "Installing Test-Hook to '$hookfolder/$hookname'"
	mkdir -p "$hookfolder"
	echo "$hook" > "$hookfolder/$hookname"
	udm_kill_univention_cli_server
}

udm_extended_attribute_uninstall_hook () {
	local hookname="${1:-$_UDM_HOOK_NAME}"
	local hookfolder="${2:-$_UDM_HOOK_FOLDER}"

	info "Deleting '$hookfolder/$hookname'"
	rm -f "$hookfolder/$hookname"
	udm_kill_univention_cli_server
}

# vim: set ts=4 sw=4 noexpandtab filetype=sh iskeyword=@,48-57,_,192-255 :
