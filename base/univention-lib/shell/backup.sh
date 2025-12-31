#!/bin/sh
# Univention Common Shell Library
#
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Clean old backups in /var/univention-backup/ that are older than
# backup/clean/max_age, if more than backup/clean/min_backups files exist.
# 1. parameter: a pattern to match files to delete via `find .. -regex ..`
# 2. parameter: override backup/clean/max_age (optional)
#
# Example to cleanup LDAP-backups:
# clean_old_backups 'ldap-backup_*.\(log\|ldif\)'
clean_old_backups () {
	local arg_pattern="$1"
	local arg_max_age="$2"
	[ -z "$arg_pattern" ] && return 1
	eval "$(univention-config-registry shell backup/clean/min_backups backup/clean/max_age)"

	local backup_dir="/var/univention-backup"
	local pattern="$backup_dir/$arg_pattern"
	local max_age="${arg_max_age:-$backup_clean_max_age}"

	if [ -n "$max_age" ]; then
		local count
		count=$(find "$backup_dir" -type f -mtime "+$max_age" -regex "$pattern" | wc -l)
		if [ "$count" -ge "${backup_clean_min_backups:-10}" ]; then
				find "$backup_dir" -type f -mtime "+$max_age" -regex "$pattern" -delete >/dev/null
		fi
	fi
}
