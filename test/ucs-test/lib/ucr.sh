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
	[ -n "${remove}" ] && univention-config-registry unset "${remove[@]}"
	[ -n "${reset}" ] && univention-config-registry set "${reset[@]}"
}
# vim:set filetype=sh ts=4:
