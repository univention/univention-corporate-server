#!/bin/sh
# Univention Common Shell Library
#
# Copyright 2017-2019 Univention GmbH
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
	eval "$(univention-config-registry shell backup/clean/.*)"

	local backup_dir="/var/univention-backup"
	local pattern="$backup_dir/$arg_pattern"
	local max_age="${arg_max_age:-$backup_clean_max_age}"

	if [ -n "$max_age" ]; then
		local count=$(find "$backup_dir" -type f -mtime "+$max_age" -regex "$pattern" | wc -l)
		if [ "$count" -ge "${backup_clean_min_backups:-10}" ]; then
				find "$backup_dir" -type f -mtime "+$max_age" -regex "$pattern" -delete >/dev/null
		fi
	fi
}
