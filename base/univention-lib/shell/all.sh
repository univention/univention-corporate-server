# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# shellcheck shell=sh
for _sh in /usr/share/univention-lib/*.sh
do
	[ "${_sh##*/}" = all.sh ] && continue
	# shellcheck source=/dev/null
	. "$_sh"
done
unset _sh
