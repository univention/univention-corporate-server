#!/bin/bash
# Wrapper around ucr which saves the original value and (manually) restores them on exit.

# Clear all shell variables starting with a single underscore
unset "${!_[^_]@}"
# Load current values read-only and prefix with single underscore
eval "$(univention-config-registry --shell dump | sed -e 's/^/declare -r _/')"
declare -a _reset=()
ucr () { # (get|set|unset) name[=value]...
	local mode="${1}"
	case "${mode}" in
		set|unset)
			shift
			case "${1:-}" in
			--force) echo "$0: UCR layer '$1' not supported" >&2 ;;
			--schedule) echo "$0: UCR layer '$1' not supported" >&2 ;;
			--ldap-policy) echo "$0: UCR layer '$1' not supported" >&2 ;;
			--*) echo "$0: Unknown UCR argument '$*'" >&2 ;;
			esac
			local name_value
			for name_value in "$@"
			do
				_reset+=("${name_value%%[=?]*}")
			done
			univention-config-registry "${mode}" "$@"
			;;
		*)
			univention-config-registry "$@"
			;;
	esac
}
ucr_restore () { # restore original values
	declare -a reset remove
	local name sname
	for name in "${_reset[@]}"
	do
		local sname="_${name//\//_}"
		if [ -n "${!sname+X}" ]
		then
			reset+=("${name}=${!sname}")
		else
			remove+=("${name}")
		fi
	done
	[ -n "${remove:-}" ] && univention-config-registry unset "${remove[@]}"
	[ -n "${reset:-}" ] && univention-config-registry set "${reset[@]}"
}
# vim:set filetype=sh ts=4:
