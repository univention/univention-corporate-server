# shellcheck shell=bash
# Univention Common Shell Library
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

UCS_JS_DIR='/usr/lib/univention-install'
UCS_JS_STATUS='/var/univention-join/status'

is_primary () {
	[ "$(/usr/sbin/univention-config-registry get server/role)" = domaincontroller_master ]
}

is_backup () {
	[ "$(/usr/sbin/univention-config-registry get server/role)" = domaincontroller_backup ]
}

is_replica () {
	[ "$(/usr/sbin/univention-config-registry get server/role)" = domaincontroller_slave ]
}

is_primary_or_backup () {
	case "$(/usr/sbin/univention-config-registry get server/role)" in
	domaincontroller_master) return 0 ;;
	domaincontroller_backup) return 0 ;;
	*) return 1 ;;
	esac
}

_join_call () {  # <role-check> <joinscript> [<args>...]
	local role_check="${1:?}" js_path="${UCS_JS_DIR}/${2:?}" js_name="${2:?}" rv=0
	[ -x "$js_path" ] ||
		return 0
	[ -f "$UCS_JS_STATUS" ] ||
		return 0

	"$role_check" ||
		return $?

	shift 2 ||
		return $?

	echo "Calling joinscript $js_name ..."
	"$js_path" "$@" ||
		rv="$?"
	echo "Joinscript $js_name finished with exitcode $rv"
	return "$rv"
}

call_joinscript () {  # <joinscipt> [<args>...]
	# calls the given joinscript
	# e.g. call_joinscript 99my-custom-joinscript.inst --binddn ... --bindpwdfile ...
	_join_call is_primary_or_backup "$@"
}

delete_unjoinscript () {  # <joinscipt>
	# deletes the given unjoinscript if it does not belong to any package
	# e.g. delete_unjoinscript 99my-custom-joinscript.uinst
	local js_path="${UCS_JS_DIR}/${1:?}"

	# Nothing to do if it does not exist
	[ -e "$js_path" ] ||
		return 1

	# Does the script end with uinst?
	[ "${1%.uinst}" != "$1" ] ||
		return 1

	# Remove the script only if it is no longer part of a package
	dpkg -S "$js_path" >/dev/null 2>&1 &&
		return 1

	# Do it
	rm -f "$js_path"
}

remove_joinscript_status () {  # <name>
	# removes the given joinscript from the join script status file
	# e.g. remove_joinscript_status univention-pkgdb-tools
	local js_name="${1:?}"

	sed -i "/^${js_name} /d" "$UCS_JS_STATUS"
}

call_unjoinscript () {  # <joinscript> [<args>...]
	# calls the given unjoinscript
	# e.g. call_unjoinscript 99my-custom-joinscript.uinst --binddn ... --bindpwdfile ...
	_join_call is_primary_or_backup "$@" &&
		delete_unjoinscript "${1:?}"
}

call_joinscript_on_dcmaster () {  # <joinscript> [<args>...]
	# calls the given joinscript ONLY on Primary Directory Node
	# e.g. call_joinscript_on_dcmaster 99my-custom-joinscript.inst --binddn ... --bindpwdfile ...
	_join_call is_primary "$@"
}

# vim:set sw=4 ts=4 noet:
