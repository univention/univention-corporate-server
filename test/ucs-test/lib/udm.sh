#!/bin/bash

. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/ldap.sh" || exit 137

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
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"

	local idattr=$(udm_get_identifier_attribute "$module")

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
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"

	for attr in $(udm_get_attribute_list "$module"); do
		eval '$variableprefix${attr//-/_}='
	done
}

log_and_eval_execute () {
	info "EXECUTING: $*"
	eval "$@"
}

udm_exists () {
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$3"
	local ldaplocation="${4:-$superordinate}"
	local objectname="${5:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	local cmd="udm-test '$module' list"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi

	if [ -n "$ldaplocation" ]; then
		cmd+=" | egrep '^DN: $(udm_get_ldap_identifier_qualifier "$module")=$objectname,$ldaplocation$'"
	else
		cmd+=" | egrep '^DN: $(udm_get_ldap_identifier_qualifier "$module")=$objectname,$(udm_get_ldap_prefix "$module")$ldap_base$'"
	fi

	if log_and_eval_execute $cmd; then
		info "$module object $objectname exists"
		return 0
	else
		info "$module object $objectname does not exist"
		return 1
	fi
}

udm_create () {
	local module="$1"
	shift
	local variableprefix="${1:-$(udm_get_module_variable_prefix "$module")}"
	shift
	local superordinate="$1"
	shift
	local ldaplocation="${1:-$superordinate}"
	shift
	local objectname="${1:-$(udm_get_identifier_value "$module" "$variableprefix")}"
	shift

	local cmd="udm-test '$module' create"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi
	if [ -n "$ldaplocation" ]; then
		cmd+=" --position '$ldaplocation'"
	else
		cmd+=" --position \"$(udm_get_ldap_prefix "$module")$ldap_base\""
	fi

	local params=
	local var=
	for attr in $(udm_get_attribute_list "$module"); do
		eval "var=\$$variableprefix${attr//-/_}"
		if [ -n "$var" ]; then
			params+=" --set '$attr'='$var'"
		fi
	done

	if log_and_eval_execute $cmd $params $@; then
		info "created $module object $objectname"
		return 0
	else
		info "failed creating $module object $objectname"
		return 1
	fi
}

udm_modify () {
	local module="$1"
	shift
	local variableprefix="${1:-$(udm_get_module_variable_prefix "$module")}"
	shift
	local superordinate="$1"
	shift
	local ldaplocation="${1:-$superordinate}"
	shift
	local objectname="${1:-$(udm_get_identifier_value "$module" "$variableprefix")}"
	shift

	local cmd="udm-test '$module' modify"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi
	if [ -n "$ldaplocation" ]; then
		cmd+=" --dn \"$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$ldaplocation\""
	else
		cmd+=" --dn \"$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$(udm_get_ldap_prefix "$module")$ldap_base\""
	fi

	if log_and_eval_execute $cmd $@; then
		info "$module object $objectname modified"
		return 0
	else
		info "failed modifying $module object $objectname"
		return 1
	fi
}

udm_remove () {
	local module="$1"
	shift
	local variableprefix="${1:-$(udm_get_module_variable_prefix "$module")}"
	shift
	local superordinate="$1"
	shift
	local ldaplocation="${1:-$superordinate}"
	shift
	local objectname="${1:-$(udm_get_identifier_value "$module" "$variableprefix")}"
	shift

	local cmd="udm-test '$module' remove"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi
	if [ -n "$ldaplocation" ]; then
		cmd+=" --dn \"$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$ldaplocation\""
	else
		cmd+=" --dn \"$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$(udm_get_ldap_prefix "$module")$ldap_base\""
	fi

	if log_and_eval_execute $cmd $@; then
		info "removed $module object $objectname"
		return 0
	else
		info "failed removing $module object $objectname"
		return 1
	fi
}

udm_ldap_remove () {
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$3"
	local ldaplocation="${4:-$superordinate}"
	local objectname="${5:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	if [ -n "$ldaplocation" ]; then
		ldap_delete "$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$ldaplocation"
	else
		ldap_delete "$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$(udm_get_ldap_prefix "$module")$ldap_base"
	fi
}

udm_purge () {
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$3"
	local ldaplocation="${4:-$superordinate}"
	local objectname="${5:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	if ! udm_remove "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" --remove_referring ||
		udm_exists "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		warning "Cleanup via udm failed"
		if ! udm_ldap_remove "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"; then
			warning "Cleanup via ldapdelete failed as well"
		fi
	fi
}

udm_get_required_module_attributes () {
	local module="$1"

	let local linecount="$(udm-test "$module" | wc -l)"
	let local syntaxbeginning="$(udm-test "$module" | grep -n "$module variables:" | sed "s#:$module variables:##")"
	let local tailcount="$linecount-$syntaxbeginning"


	local output="$(udm-test "$module" | tail -n2 | grep -n "^$" | head -n 1)"
	if [ -n "$output" ]; then
		let local relativesyntaxend="${output/:/}"
	else
		let local relativesyntaxend="$tailcount"
	fi

	udm-test "$module" |
		tail -n "$tailcount" |
		head -n "$relativesyntaxend" |
		egrep -v "^  .*:$" |
		egrep "\(c\)|\(c,.*\)|\(.*,c\)|\(.*,c,.*\)" |
		sed "s/^ *//" |
		sed "s/ .*$//"
}

udm_get_plain_module_attributes () {
	local module="$1"

	let local linecount="$(udm-test "$module" | wc -l)"
	let local syntaxbeginning="$(udm-test "$module" | grep -n "$module variables:" | sed "s#:$module variables:##")"
	let local tailcount="$linecount - $syntaxbeginning"

	local output="$(udm-test "$module" | tail -n "$tailcount" | grep -n "^$" | head -n 1)"
	if [ -n "$output" ]; then
	        let local relativesyntaxend="${output/:/}"
	else
	        let local relativesyntaxend="$tailcount"
	fi

	udm-test "$module" |
	        tail -n "$tailcount" |
	        head -n "$relativesyntaxend" |
	        egrep -v "^  .*:$" |
	        sed "s/^ *//" |
	        sed "s/ .*$//"
}

udm_get_tab_entries () {
	local module="$1"
	local tabname="$2"

	let local linecount="$(udm-test "$module" | wc -l)"
	let local tabbeginning="$(udm-test "$module" | grep -n "$tabname:" | sed "s#: *$tabname:##")"
	let local tailcount="$linecount - $tabbeginning"

	local output="$(udm-test "$module" | tail -n "$tailcount" | egrep -n ".*:\$" | head -n 1 | sed "s#:.*##")"
	if [ -n "$output" ]; then
		let local relativetabend="$output - 1"
	else
		let local relativetabend="$tailcount + 1"
	fi

	udm-test "$module" |
		tail -n "$tailcount" |
		head -n "$relativetabend" |
		sed "s/^ *//"
}

udm_get_ldap_attribute () {
	local attributename="$1"
	local module="$2"
	local variableprefix="${3:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$4"
	local ldaplocation="${5:-$superordinate}"
	local objectname="${6:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	if [ -n "$ldaplocation" ]; then
		local branch="$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$ldaplocation"
	else
		local branch="$(udm_get_ldap_identifier_qualifier "$module")=$objectname,$(udm_get_ldap_prefix "$module")$ldap_base"
	fi

	log_and_eval_execute "ldapsearch -xLLL -D 'cn=admin,$ldap_base' -w '`cat /etc/ldap.secret`' -b '$branch' \
		'$attributename' |
		grep '^$attributename' |
		sed 's/^${attributename}\;//' |
		sed 's/^${attributename}\: //'"
}

udm_has_object_class () {
	local objectclass="$1"
	local module="$2"
	local variableprefix="${3:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$4"
	local ldaplocation="$5"
	local objectname="${6:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	local objectclasses="$(udm_get_ldap_attribute objectClass "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname")"

	IFS="
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
	local attribute="$1"
	local expected_value="$2"
	local module="$3"
	local variableprefix="$4"
	local superordinate="$5"
	local ldaplocation="$6"
	local objectname="$7"

	local value="$(udm_get_ldap_attribute "$attribute" "$module" "$variableprefix"  "$superordinate" "$ldaplocation" "$objectname")"
	verify_value "$attribute" "$value" "$expected_value"
}

udm_verify_ldap_attributes () {
	local module="$1"
	shift
	local variableprefix="${1:-$(udm_get_module_variable_prefix "$module")}"
	shift
	local superordinate="$1"
	shift
	local ldaplocation="$1"
	shift
	local objectname="$1"
	shift

	local attr=
	local switch=attr
	for elem in "$@"; do
		if [ "$switch" = "attr" ]; then
			switch=value
			attr="$elem"
		else
			switch=attr
			if ! udm_verify_ldap_attribute "$attr" "$elem" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
			then
				return 1
			fi
		fi
	done
	return 0
}

udm_get_udm_attribute () {
	local attribute="$1"
	local module="$2"
	local variableprefix="${3:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$4"
	local ldaplocation="$5"
	local objectname="${6:-$(udm_get_identifier_value "$module" "$variableprefix")}"

	local cmd="udm-test '$module' list"
	if [ -n "$superordinate" ]; then
		cmd+=" --superordinate '$superordinate'"
	fi
	cmd+=" --filter \"$(udm_get_udm_filter_qualifier "$module")=$objectname\" | egrep '^ *${attribute}: ' | sed 's/^ *${attribute}: //'"

	log_and_eval_execute $cmd
}

udm_verify_udm_attribute () {
	local attribute="$1"
	local expected_value="$2"
	local module="$3"
	local variableprefix="$4"
	local superordinate="$5"
	local ldaplocation="$6"
	local objectname="$7"

	local value="$(udm_get_udm_attribute "$attribute" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname")"

	verify_value "$attribute" "$value" "$expected_value"
}

udm_verify_multi_value_udm_attribute_contains_ignore_case () {
	local attribute="$1"
	local expected_value="$2"
	local module="$3"
	local variableprefix="$4"
	local superordinate="$5"
	local ldaplocation="$6"
	local objectname="$7"

	local value="$(udm_get_udm_attribute "$attribute" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname")"

	verify_value_contains_line_ignore_case "$attribute" "$value" "$expected_value"
}

udm_verify_multi_value_udm_attribute_contains () {
	local attribute="$1"
	local expected_value="$2"
	local module="$3"
	local variableprefix="$4"
	local superordinate="$5"
	local ldaplocation="$6"
	local objectname="$7"

	local value="$(udm_get_udm_attribute "$attribute" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname")"

	verify_value_contains_line "$attribute" "$value" "$expected_value"
}

udm_verify_udm_attributes () {
	local module="$1"
	local variableprefix="${2:-$(udm_get_module_variable_prefix "$module")}"
	local superordinate="$3"
	local ldaplocation="$4"
	local objectname="$5"

	local var=
	for attr in $(udm_get_attribute_list "$module"); do
		eval "var=\$$variableprefix${attr//-/_}"
		if [ -n "$var" ]; then
			if ! udm_verify_udm_attribute "$attr" "$var" "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
			then
				return 1
			fi
		fi
	done
	return 0
}

udm_check_required_singlevalue_attribute () {
	local attribute="$1"
	local value1="$2"
	local value2="$3"
	local module="$4"
	local variableprefix="$5"
	local superordinate="$6"
	local ldaplocation="$7"
	local objectname="$8"

	local expected_value="$value1"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--set \""$attribute=$value1"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Singlevalue attribute '$attribute': Setting initial value failed"
		return 1
	fi

	expected_value="$value1"
	if udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--append \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Singlevalue attribute '$attribute': Appending second value succeeded"
		return 1
	fi

	expected_value="$value2"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--set \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Singlevalue attribute '$attribute': Overwriting previous value failed"
		return 1
	fi

	return 0
}

udm_check_singlevalue_attribute () {
	local attribute="$1"
	local value1="$2"
	local value2="$3"
	local module="$4"
	local variableprefix="$5"
	local superordinate="$6"
	local ldaplocation="$7"
	local objectname="$8"

	if ! udm_check_required_singlevalue_attribute "$attribute" "$value1" "$value2" \
		"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		return 1
	fi

	expected_value="None"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--remove \""$attribute=$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Singlevalue attribute '$attribute': Removing value failed"
		return 1
	fi

	return 0
}

udm_check_multivalue_attribute () {
	local attribute="$1"
	local value1="$2"
	local value2="$3"
	local value3="$4"
	local module="$5"
	local variableprefix="$6"
	local superordinate="$7"
	local ldaplocation="$8"
	local objectname="$9"

	local expected_value="$value1"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--set \""$attribute=$value1"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Multivalue attribute '$attribute': Setting initial value failed"
		return 1
	fi

	local expected_value="$value1
$value2
$value3"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--append \""$attribute=$value2"\" --append \""$attribute=$value3"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Multivalue attribute '$attribute': Appending two values failed"
		return 1
	fi

	expected_value="$value1
$value3"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--remove \""$attribute"\"=\""$value2"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Multivalue attribute \"$attribute\": Removing middle value failed"
		return 1
	fi

	expected_value="$value1"
	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			--remove \""$attribute"\"=\""$value3"\" ||
		! udm_verify_udm_attribute "$attribute" "$expected_value" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		info "Multivalue attribute \"$attribute\": Removing last value failed"
		return 1
	fi

	return 0
}

udm_check_flag_attribute () {
	local attribute="$1"
	local module="$2"
	local variableprefix="$3"
	local superordinate="$4"
	local ldaplocation="$5"
	local objectname="$6"

	udm_check_required_singlevalue_attribute "$attribute" "0" "1" \
		"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	return $?
}

udm_check_syntax_for_attribute () {
	local attribute="$1"
	local valid1="$2"
	local valid2="$3"
	local invalid="$4"
	local module="$5"
	local variableprefix="$6"
	local superordinate="$7"
	local ldaplocation="$8"
	local objectname="$9"
	local customcliname="${10}"

	if [ -n "$customcliname" ]; then
		local set="--customattribute"
	else
		customcliname="$attribute"
		local set="--set"
	fi

	if ! udm_create "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			"$set" \""$customcliname"\"="$valid1" ||
		! udm_exists "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" ||
		! udm_verify_udm_attribute "$attribute" "$valid1" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		udm_purge "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
		warning "Syntax check for attribute \"$attribute\": Creation with correct syntax failed."
		return 1
	fi

	if ! udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			"$set" \""$customcliname"\"="$valid2" ||
		! udm_verify_udm_attribute "$attribute" "$valid2" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		udm_purge "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
		warning "Syntax check for attribute \"$attribute\": Modification with correct syntax failed."
		return 1
	fi

	if udm_modify "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
			"$set" \""$customcliname"\"="$invalid" ||
		! udm_verify_udm_attribute "$attribute" "$valid2" \
			"$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
	then
		udm_purge "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
		warning "Syntax check for attribute \"$attribute\": Modification with incorrect syntax succeeded."
		return 1
	fi

	udm_purge "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"

	if udm_create "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname" \
		"$set" \""$customcliname"\"="$invalid"
	then
		udm_purge "$module" "$variableprefix" "$superordinate" "$ldaplocation" "$objectname"
		warning "Syntax check for attribute \"$attribute\": Creation with incorrect syntax succeeded."
		return 1
	fi

	return 0
}

udm_kill_univention_cli_server () {
	local pids="$(pgrep -f "univention-cli-server")"
	for pid in $pids; do
		info "Killing univention-cli-server with pid $pid"
		kill "$pid"
	done
}

_UDM_HOOK_FOLDER="/usr/lib/python2.7/site-packages/univention/admin/hooks.d"
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
